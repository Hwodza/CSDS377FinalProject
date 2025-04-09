import sqlite3
import subprocess
import json
import paho.mqtt.client as mqtt
import time
import re
import psutil

db_path = "sysstat_data.db"
mqtt_broker = "localhost"  # Change to your MQTT broker
mqtt_topic = "sender/status"
mqtt_port = 1883


def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Enable foreign key constraints
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Main stats table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS main_stats (
            timestamp TEXT PRIMARY KEY,
            kbmemfree INTEGER,
            kbmemused INTEGER,
            memused_percent REAL,
            cputemp REAL
        )
    """)

    # Disk stats table (composite PK: timestamp + device)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS disk_stats (
            timestamp TEXT,
            device TEXT,
            wait REAL,
            util REAL,
            PRIMARY KEY (timestamp, device),
            FOREIGN KEY (timestamp) REFERENCES main_stats(timestamp)
        )
    """)

    # CPU load table (composite PK: timestamp + core)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cpu_load (
            timestamp TEXT,
            core INTEGER,
            load REAL,
            PRIMARY KEY (timestamp, core),
            FOREIGN KEY (timestamp) REFERENCES main_stats(timestamp)
        )
    """)

    # Network stats table (composite PK: timestamp + iface)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS network_stats (
            timestamp TEXT,
            iface TEXT,
            rx_kb REAL,
            tx_db REAL,
            PRIMARY KEY (timestamp, iface),
            FOREIGN KEY (timestamp) REFERENCES main_stats(timestamp)
        )
    """)
    conn.commit()
    conn.close()


def store_data(timestamp, kbmemfree, kbmemused, memused_percent, cputemp,
               disk_stats, cpu_loads, network_stats):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    try:
        # Insert into main_stats
        cursor.execute("""
            INSERT INTO main_stats (timestamp, kbmemfree, kbmemused,
                       memused_percent, cputemp)
            VALUES (?, ?, ?, ?, ?)
        """, (timestamp, kbmemfree, kbmemused, memused_percent, cputemp))

        # Insert into disk_stats
        for entry in disk_stats:
            cursor.execute("""
                INSERT INTO disk_stats (timestamp, device, wait, util)
                VALUES (?, ?, ?, ?)
            """, (timestamp, entry['device'], entry['wait'], entry['util']))

        # Insert into cpu_load
        for i, entry in enumerate(cpu_loads):
            cursor.execute("""
                INSERT INTO cpu_load (timestamp, core, load)
                VALUES (?, ?, ?)
            """, (timestamp, i, entry))

        # Insert into network_stats
        for entry in network_stats:
            cursor.execute("""
                INSERT INTO network_stats (timestamp, iface, rx_kb, tx_db)
                VALUES (?, ?, ?, ?)
            """, (timestamp, entry['iface'], entry['rx_kb'], entry['tx_db']))

        conn.commit()
        print(f"Inserted system stats for timestamp {timestamp}")
    except sqlite3.IntegrityError as e:
        print(f"Integrity error: {e}")
    finally:
        conn.close()


def publish_data(data):
    client = mqtt.Client()
    client.connect(mqtt_broker, mqtt_port, 60)
    client.publish(mqtt_topic, json.dumps(data))
    client.disconnect()


def get_cpu_temp():
    try:
        # Run the sensors command and capture the output
        output = subprocess.check_output(['sensors'], encoding='utf-8')
    except FileNotFoundError:
        print("Error: 'sensors' command not found. Please install lm-sensors.")
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error running sensors command: {e}")
        return None

    # Look for the k10temp section and extract the Tctl value
    cpu_temp = None
    in_k10temp = False

    for line in output.splitlines():
        if line.startswith("k10temp-pci-"):
            in_k10temp = True
        elif in_k10temp and line.strip().startswith("Tctl:"):
            match = re.search(r'Tctl:\s+\+([\d.]+)°C', line)
            if match:
                cpu_temp = float(match.group(1))
                break
        elif line.strip() == "":
            in_k10temp = False  # end of the k10temp section

    return cpu_temp


def get_per_cpu_load(interval=1):
    print(f"Measuring CPU load over {interval} second(s)...")
    load_per_core = psutil.cpu_percent(interval=interval, percpu=True)
    return load_per_core


def get_memory_stats():
    try:
        # Run the sar command
        result = subprocess.run(['sar', '-r', '1', '1'], 
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True)

        if result.returncode != 0:
            print("Error running sar:", result.stderr)
            return None

        lines = result.stdout.splitlines()

        for line in lines:
            parts = line.split()
            if len(parts) >= 5 and parts[1].isdigit():
                return {
                    'kbmemfree': int(parts[1]),
                    'kbmemused': int(parts[2]),
                    'memused_percent': float(parts[3])
                }

        print("No valid memory data found.")
        return None

    except FileNotFoundError:
        print("sar command not found. Make sure sysstat is installed.")
        return None


def parse_iostat_output(output):
    lines = output.strip().split('\n')
    device_lines_started = False
    stats = []

    for line in lines:
        # Look for the header that starts with "Device"
        if line.strip().startswith('Device'):
            device_lines_started = True
            continue
        if device_lines_started:
            parts = line.split()
            # Ensure line has enough columns to parse
            if len(parts) >= 12:
                try:
                    device = parts[0]
                    wait = float(parts[9])  # "await" value
                    util = float(parts[11])  # "%util" value
                    stats.append({
                        'device': device,
                        'wait': wait,
                        'util': util
                    })
                except ValueError:
                    # Skip line if conversion fails (e.g., malformed line)
                    continue
    return stats


def monitor_disk():
    result = subprocess.run(['iostat', '-dx', '1', '2'], 
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True)
    output = result.stdout
    stats = parse_iostat_output(output)
    return stats


def get_network_stats():
    try:
        # Run the sar command to get network stats (1 second sample)
        result = subprocess.run(['sar', '-n', 'DEV', '1', '1'],
                                capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')

        # Find the header and data lines
        headers = []
        data_lines = []
        for line in lines:
            if 'IFACE' in line:
                headers = line.split()
            elif line and line[0].isdigit():  # Skip timestamped lines
                continue
            elif (
                any(dev in line for dev in ['eth', 'en', 'wl', 'lo'])
                and line.startswith("Average")
            ):
                # print(line)  # common interface prefixes
                data_lines.append(line.split())

        # Print KB/s received and transmitted for each interface
        networks = []
        for line in data_lines:
            networks.append({
                'iface': line[1],
                'rx_kb': line[4],
                'tx_kb': line[5]
                })
        return networks
    except subprocess.CalledProcessError as e:
        print("Failed to run sar:", e)
        return {'error': str(e)}


def main():
    init_db()
    while True:
        # data = collect_sysstat()
        temp = get_cpu_temp()
        print(f"CPU Temp: {temp} °C")
        cpu_load = get_per_cpu_load()
        print(f"CPU Load: {cpu_load}")
        memory_stats = get_memory_stats()
        print("Memory Stats: ", memory_stats)
        disk_stats = monitor_disk()
        print("Disk Stats: ", disk_stats)
        network_stats = get_network_stats()
        print("Network Stats: ", network_stats)
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        store_data(timestamp, memory_stats['kbmemfree'], 
                   memory_stats['kbmemused'], memory_stats['memused_percent'],
                   temp, disk_stats, cpu_load, network_stats)
        publish_data({
            "timestamp": timestamp,
            "cpu_temp": temp,
            "cpu_load": cpu_load,
            "memory_stats": memory_stats,
            "disk_stats": disk_stats,
            "network_stats": network_stats
        })
        time.sleep(3)  # Adjust the interval as needed


if __name__ == "__main__":
    main()
