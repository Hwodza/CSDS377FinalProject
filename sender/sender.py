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

'''
Please write a python script that will do the following: make a sqlite database, its main table should have a timestamp as its primary key. It also needs to store the following data, kbmemfree, kbmemused, memused_percent
'''

def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_stats (
            timestamp TEXT PRIMARY KEY,
            cpu_usage REAL,
            memory_usage REAL,
            disk_usage REAL,
            network_rx REAL,
            network_tx REAL
        )
    """)
    conn.commit()
    conn.close()


def collect_sysstat():
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    
    # CPU Usage
    cpu_usage = float(subprocess.getoutput("sar 1 1 | grep 'Average' | awk '{print 100 - $NF}'"))
    
    # Memory Usage
    mem_data = subprocess.getoutput("free -m | awk 'NR==2{printf \"%s\", $3*100/$2 }'")
    memory_usage = float(mem_data)
    
    # Disk Usage
    disk_data = subprocess.getoutput("df --output=pcent / | tail -1 | tr -d '%'")
    disk_usage = float(disk_data)
    
    # Network Usage
    net_data = subprocess.getoutput("sar -n DEV 1 1 | grep 'Average.*eth0' | awk '{print $5, $6}'")
    try:
        network_rx, network_tx = map(float, net_data.split())
    except ValueError:
        # Default to 0.0 if parsing fails
        network_rx, network_tx = 0.0, 0.0
    
    return {
        "timestamp": timestamp,
        "cpu_usage": cpu_usage,
        "memory_usage": memory_usage,
        "disk_usage": disk_usage,
        "network_rx": network_rx,
        "network_tx": network_tx
    }


def store_data(data):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO system_stats (timestamp, cpu_usage, memory_usage, disk_usage, network_rx, network_tx)
        VALUES (:timestamp, :cpu_usage, :memory_usage, :disk_usage, :network_rx, :network_tx)
    """, data)
    conn.commit()
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
        result = subprocess.run(['sar', '-r', '1', '1'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            print("Error running sar:", result.stderr)
            return None

        lines = result.stdout.splitlines()

        for line in lines:
            parts = line.split()
            if len(parts) >= 5 and parts[1].isdigit():  # Only process valid data lines
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
    result = subprocess.run(['iostat', '-dx', '1', '2'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output = result.stdout
    stats = parse_iostat_output(output)
    return stats


def get_network_stats():
    try:
        # Run the sar command to get network stats (1 second sample)
        result = subprocess.run(['sar', '-n', 'DEV', '1', '1'], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')

        # Find the header and data lines
        headers = []
        data_lines = []
        for line in lines:
            if 'IFACE' in line:
                headers = line.split()
            elif line and line[0].isdigit():  # Skip timestamped lines
                continue
            elif any(dev in line for dev in ['eth', 'en', 'wl', 'lo']) and line.startswith("Average"):
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
        data = collect_sysstat()
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
        store_data(data)
        publish_data(data)
        time.sleep(3)  # Adjust the interval as needed


if __name__ == "__main__":
    main()

