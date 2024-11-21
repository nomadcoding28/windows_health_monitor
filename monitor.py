import psutil
import GPUtil
from datetime import datetime, timezone
import time

# Alert thresholds
THRESHOLDS = {
    "cpu": 80,  # in percentage
    "memory": 80,  # in percentage
    "disk": 90,  # in percentage
    "temperature": 80,  # in Celsius
    "gpu": 80,  # in percentage
    "gpu_memory": 80,  # in percentage
}

# Function to log and monitor metrics
def log_and_monitor_metrics():
    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_usage = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage('/').percent

        # Get network usage
        net_io = psutil.net_io_counters()
        bytes_sent = net_io.bytes_sent / (1024 * 1024)  # Convert to MB
        bytes_recv = net_io.bytes_recv / (1024 * 1024)  # Convert to MB

        # Get number of processes and top CPU-consuming process
        num_processes = len(psutil.pids())
        processes = sorted(psutil.process_iter(['pid', 'name', 'cpu_percent']), key=lambda p: p.info['cpu_percent'], reverse=True)
        top_process = processes[0].info if processes else {"pid": "N/A", "name": "N/A", "cpu_percent": 0}

        # Get battery status
        battery = psutil.sensors_battery()
        battery_status = f"{battery.percent}% {'Charging' if battery.power_plugged else 'Discharging'}" if battery else "N/A"

        # Get system uptime
        uptime_seconds = time.time() - psutil.boot_time()
        uptime = str(datetime.fromtimestamp(uptime_seconds, tz=timezone.utc).strftime('%H:%M:%S'))

        # Fetch temperature with fallback
        try:
            temperatures = psutil.sensors_temperatures()
            cpu_temp = max((temp.current for temp in temperatures.get('coretemp', [])), default="N/A")
        except AttributeError:
            cpu_temp = "N/A"  # Handle systems without temperature support

        # GPU Analytics
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu = gpus[0]
            gpu_util = gpu.load * 100
            gpu_mem_util = gpu.memoryUtil * 100
            gpu_temp = gpu.temperature
        else:
            gpu_util = gpu_mem_util = gpu_temp = "N/A"

        # Create log entry
        log_entry = (
            f"{timestamp} | CPU: {cpu_usage}% | Memory: {memory_usage}% | Disk: {disk_usage}% | "
            f"Net Sent: {bytes_sent:.2f} MB | Net Received: {bytes_recv:.2f} MB | Processes: {num_processes} | "
            f"Top Process: [PID={top_process['pid']}, Name={top_process['name']}, CPU={top_process['cpu_percent']}%] | "
            f"Battery: {battery_status} | Uptime: {uptime} | CPU Temp: {cpu_temp}°C | "
            f"GPU Util: {gpu_util}% | GPU Memory: {gpu_mem_util}% | GPU Temp: {gpu_temp}°C"
        )

        # Print log to terminal
        print(log_entry)

        # Trigger alerts for thresholds
        if cpu_usage > THRESHOLDS["cpu"]:
            alert_message = f"High CPU Usage: {cpu_usage}% (Threshold: {THRESHOLDS['cpu']}%)"
            print(f"[ALERT] {alert_message}")
        if memory_usage > THRESHOLDS["memory"]:
            alert_message = f"High Memory Usage: {memory_usage}% (Threshold: {THRESHOLDS['memory']}%)"
            print(f"[ALERT] {alert_message}")
        if disk_usage > THRESHOLDS["disk"]:
            alert_message = f"High Disk Usage: {disk_usage}% (Threshold: {THRESHOLDS['disk']}%)"
            print(f"[ALERT] {alert_message}")
        if cpu_temp != "N/A" and cpu_temp > THRESHOLDS["temperature"]:
            alert_message = f"High CPU Temperature: {cpu_temp}°C (Threshold: {THRESHOLDS['temperature']}°C)"
            print(f"[ALERT] {alert_message}")
        if gpus and gpu_util > THRESHOLDS["gpu"]:
            alert_message = f"High GPU Usage: {gpu_util}% (Threshold: {THRESHOLDS['gpu']}%)"
            print(f"[ALERT] {alert_message}")
        if gpus and gpu_mem_util > THRESHOLDS["gpu_memory"]:
            alert_message = f"High GPU Memory Usage: {gpu_mem_util}% (Threshold: {THRESHOLDS['gpu_memory']}%)"
            print(f"[ALERT] {alert_message}")

        time.sleep(5)  # Wait for 5 seconds before next monitoring cycle

if __name__ == "__main__":
    print("Monitoring system metrics with detailed analytics... Press Ctrl+C to stop.")
    try:
        log_and_monitor_metrics()
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
