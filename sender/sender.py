import sqlite3
import subprocess
import json
import paho.mqtt.client as mqtt
import time

db_path = "sysstat_data.db"
mqtt_broker = "localhost"  # Change to your MQTT broker
mqtt_topic = "sender/status"
mqtt_port = 1883

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

def main():
    init_db()
    while True:
        data = collect_sysstat()
        store_data(data)
        publish_data(data)
        time.sleep(3)  # Adjust the interval as needed

if __name__ == "__main__":
    main()

