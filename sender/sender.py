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

        # Check for errors
        if result.returncode != 0:
            print("Error running sar:", result.stderr)
            return None

        # Parse the output
        lines = result.stdout.splitlines()

        for line in reversed(lines):
            if re.search(r'\d{2}:\d{2}:\d{2}', line):  # Look for timestamped lines (data lines)
                parts = line.split()
                if len(parts) >= 5:
                    return {
                        'time': parts[0],
                        'kbmemfree': int(parts[1]),
                        'kbmemused': int(parts[2]),
                        'memused_percent': float(parts[3])
                    }

        print("No memory data found.")
        return None

    except FileNotFoundError:
        print("sar command not found. Make sure sysstat is installed.")
        return None


def parse_iostat_output(output):
    lines = output.strip().split('\n')
    # Find the device lines (skip CPU stats and headers)
    for i, line in enumerate(lines):
        if line.strip().startswith('Device'):
            device_lines = lines[i+1:]
            break
    else:
        return []

    stats = []
    for line in device_lines:
        parts = line.split()
        if len(parts) >= 12:
            device = parts[0]
            await = float(parts[9])
            util = float(parts[11])
            stats.append({
                'device': device,
                'await': await,
                'util': util
            })
    return stats

def monitor_disk():
    result = subprocess.run(['iostat', '-dx', '1', '2'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output = result.stdout
    stats = parse_iostat_output(output)
    return stats
def main():
    init_db()
    while True:
        data = collect_sysstat()
        temp = get_cpu_temp()
        print(f"CPU Temp: {temp} °C")
        cpu_load = get_per_cpu_load()
        print("Per-CPU Load (%):")
        for i, load in enumerate(cpu_load):
            print(f"CPU {i}: {load}%")
        memory_stats = get_memory_stats()
        print("Memory Stats: ", memory_stats)
        disk_stats = monitor_disk()
        print("Disk Stats: ", disk_stats)
        store_data(data)
        publish_data(data)
        time.sleep(3)  # Adjust the interval as needed


if __name__ == "__main__":
    main()

