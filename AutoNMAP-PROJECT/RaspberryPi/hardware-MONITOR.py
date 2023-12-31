import requests
import psutil
import time
import subprocess

def get_temperature():
    try:
        temp_output = subprocess.check_output(["vcgencmd", "measure_temp"]).decode()
        temp = float(temp_output.split('=')[1].split("'")[0])
        return temp
    except:
        return "Unable to get temperature"

def post_to_discord(webhook_url, cpu, memory, temperature):
    data = {
        "content": f"-------------------\n**CPU Usage:** {cpu}%\n**Memory Usage:** {memory}%\n**Temperature:** {temperature}°F\n-------------------"
    }
    result = requests.post(webhook_url, json=data)
    return result.status_code

def monitor_and_report():
    webhook_url = 'HARDWARE WEBHOOK'

    while True:
        cpu_usage = psutil.cpu_percent(interval=60)
        memory_usage = psutil.virtual_memory().percent
        temperature = get_temperature()

        post_to_discord(webhook_url, cpu_usage, memory_usage, temperature)
        time.sleep(120) 

if __name__ == "__main__":
    monitor_and_report()
