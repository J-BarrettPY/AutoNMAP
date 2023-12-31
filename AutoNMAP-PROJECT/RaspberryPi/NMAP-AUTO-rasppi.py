import threading
import subprocess
import requests
import json
import os
import time
import re
from datetime import datetime
from pymongo import MongoClient


client = MongoClient('YOUR LOCAL IP ADDRESS', 27017)
db = client.AUTO_NMAP

if os.geteuid() != 0:
    input("This script needs to be run as root. Please run again with sudo.")
    exit()

def ensure_json_folder():
    json_folder = "JSON"
    if not os.path.exists(json_folder):
        os.makedirs(json_folder)
    return json_folder


def update_url_list(url_to_remove):
    with open('urls.txt', 'r') as file:
        urls = file.readlines()
    urls = [url for url in urls if url.strip() != url_to_remove]
    with open('urls.txt', 'w') as file:
        file.writelines(urls)

def extract_os_details(scan_output):
    os_details = ""
    for line in scan_output.split('\n'):
        if line.startswith("OS details:"):
            os_details = line[len("OS details:"):].strip()
            break
    return os_details

def write_to_json(level, data, full_scan_output=None):
    json_folder = ensure_json_folder()

    today_date = datetime.now().strftime("%m.%d.%y")
    filename = os.path.join(json_folder, f"{today_date}-{level}.json")

    # Add the full scan output to the data if applicable
    if full_scan_output and level in ["medium", "high", "very_high"]:
        data["Full Scan Output"] = full_scan_output

    # Check if the file already exists
    if os.path.exists(filename):
        # Open the file in read mode and load existing data
        with open(filename, "r") as file:
            try:
                existing_data = json.load(file)
            except json.JSONDecodeError:
                # If the file is empty or not a valid JSON, start with an empty list
                existing_data = []

        # Append the new data to the existing data
        existing_data.append(data)

        # Write the updated data back to the file
        with open(filename, "w") as file:
            json.dump(existing_data, file, indent=4)
    else:
        # If the file does not exist, create a new file with the data
        with open(filename, "w") as file:
            json.dump([data], file, indent=4)


def write_to_mongodb(level, data, full_scan_output=None):
    collection = db[level]

    if full_scan_output and level in ["medium", "high", "very_high"]:
        data["Full Scan Output"] = full_scan_output

    collection.insert_one(data)


def extract_aggressive_os_guesses(scan_output):
    for line in scan_output.split('\n'):
        if line.startswith("Aggressive OS guesses:"):
            os_guesses = line.split("Aggressive OS guesses: ", 1)[-1]
            return os_guesses.split(")", 1)[0] + ")"
    return ""


def extract_cve_severity(scan_output):
    cve_pattern = re.compile(r"CVE-\d{4}-\d{4,5}\s+(\d+\.\d+)")
    for line in scan_output.split('\n'):
        match = cve_pattern.search(line)
        if match:
            return float(match.group(1))
    return 0.0

def extract_vulners_data(scan_output):
    vulners_data = []
    vulners_found = False

    for line in scan_output.split('\n'):
        if 'vulners:' in line:
            vulners_found = True
        elif vulners_found:
            if line.startswith('|') or line.startswith('|_'):
                vulners_data.append(line.strip())
            else:
                break

    return '\n'.join(vulners_data)


def extract_other_addresses(scan_output):
    other_addresses = ""
    for line in scan_output.split('\n'):
        if "Other addresses for" in line and "(not scanned):" in line:
            other_addresses = line.split("(not scanned):")[1].strip()
            break
    return other_addresses

def extract_http_grep_data(scan_output):
    http_grep_data = []
    http_grep_found = False

    for line in scan_output.split('\n'):
        if 'http-grep:' in line:
            http_grep_found = True
        elif http_grep_found:
            if line.startswith('|') or line.startswith('|_'):
                http_grep_data.append(line.strip())
            elif re.search(r'\d+/tcp', line):
                break

    return '\n'.join(http_grep_data)



def run_nmap(url):
    print(f"Scanning {url}")

    cmd = f"nmap --script=ftp-anon --script vulners --script-args mincvss=5.0 --script http-grep.nse --script ssl-enum-ciphers -sV -p 22,21,23,20,25,53,69,80,110,111,135,137,138,139,143,161,162,443,445,512,513,514,587,993,995,1433,1434,1521,2049,3306,3389,5060,5061,5900,5985,5986,6000,6379,8443,9200,9300,10000,11211,20000,27017,27018 -O -T3 -v {url}"

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=900)
    except subprocess.TimeoutExpired:
        print(f"Timeout expired for {url}. Moving to next URL.")
        update_url_list(url)
        return

    filename = f"{url.replace('://', '_').replace('/', '_')}.txt"

    with open(filename, 'w') as file:
        file.write(result.stdout)

    upload_to_discord(filename, url, result.stdout)
    update_url_list(url)


def is_critical_port_open(scan_output):
    critical_ports = [22, 21, 23, 20, 25, 53, 69, 110, 111, 135, 137, 138, 139, 143, 161, 162, 445, 512, 513, 514, 587, 993, 995, 1433, 1434, 1521, 2049, 3306, 3389, 5060, 5061, 5900, 5985, 5986, 6000, 6379, 9200, 9300, 10000, 11211, 20000, 27017, 27018]
    open_critical_ports = []
    for port in critical_ports:
        # Fetch port, service, and version
        port_regex = re.compile(f"{port}/tcp +open +([^ ]+) +([^\n]+)")
        match = port_regex.search(scan_output)
        if match:
            service_name = match.group(1)
            service_version = match.group(2).strip()
            open_critical_ports.append(f"{port} ({service_name} :: {service_version})")
    return open_critical_ports


def upload_to_discord(filename, url, scan_output):
    low_webhook = 'WEBHOOK LOW'
    medium_webhook = 'WEBHOOK MEDIUM'
    high_webhook = 'WEBHOOK HIGH'
    veryhigh_webhook = 'WEBHOOK VHIGH'

    open_ports = is_critical_port_open(scan_output)
    anonlogin = "Anonymous FTP login allowed" in scan_output or "ftp-anon:" in scan_output
    found_badenc = "least strength: F" in scan_output or "least strength: D" in scan_output # Weak Encryption

    cve_severity = extract_cve_severity(scan_output)

    if anonlogin:
        webhook_url = veryhigh_webhook
        color = 0xA500FF  # purps
        additional_description = "\n\n[ + ] Anonymous FTP Login Allowed"
    elif found_badenc or cve_severity > 8:
        webhook_url = high_webhook
        color = 0xFF0000  # red
        additional_description = ""
        if found_badenc:
            additional_description += "\n\n[ + ] Weak Encryption Detected"
    elif open_ports or cve_severity > 5:
        webhook_url = medium_webhook
        color = 0xFFA500  # orange (not red basically)
        additional_description = ""
    else:
        webhook_url = low_webhook
        color = 5814783  # default color
        additional_description = ""

    description = f"Nmap result for {url}"

    http_grep_data = extract_http_grep_data(scan_output)
    if http_grep_data:
        description += f"\n\n[ + ] Emails or Hidden IPs Found"

    vulners_data = extract_vulners_data(scan_output)
    if vulners_data:
        description += f"\n\n[ + ] Vulnerabilities Detected"

    os_guesses = extract_aggressive_os_guesses(scan_output)
    if os_guesses:
        description += f"\n\n[ + ] Best OS Guess: {os_guesses}"

    if open_ports:
        description += f"\n\n[ + ] Critical Ports Open:\n{', '.join(map(str, open_ports))}"
    description += additional_description

    other_addresses = extract_other_addresses(scan_output)
    if other_addresses:
        description += f"\n\n[ + ] Other Associated Addresses: {other_addresses}"

    # Json
    json_data = {
        "URL": url,
        "IP Address": re.search(r'\d+\.\d+\.\d+\.\d+', scan_output).group(0) if re.search(r'\d+\.\d+\.\d+\.\d+',
                                                                                          scan_output) else "Not Found",
        "Open Ports": open_ports,
        "Vulners": vulners_data,
        "Aggressive OS guesses": os_guesses,
        "OS Details": extract_os_details(scan_output),
        "Anonymous FTP Login": anonlogin,
        "Weak Encryption": found_badenc,
        "Other Addresses": other_addresses,
        "HTTP Grep Data": http_grep_data,

    }

    level = "low"
    if open_ports or cve_severity > 5:
        level = "medium"
    if found_badenc or cve_severity > 8 or anonlogin:
        level = "high"
    if anonlogin:
        level = "very_high"


    write_to_json(level, json_data, full_scan_output=scan_output if level in ["medium", "high", "very_high"] else None)
    write_to_mongodb(level, json_data,
                     full_scan_output=scan_output if level in ["medium", "high", "very_high"] else None)

    with open(filename, 'rb') as file:
        file_data = {'file': (filename, file, 'text/plain')}
        embed = {
            "embeds": [
                {
                    "title": f"{url}",
                    "description": description,
                    "color": color
                }
            ]
        }
        response = requests.post(webhook_url, files=file_data, data={'payload_json': json.dumps(embed)})

    if response.status_code in [200, 204]:
        print(f"Successfully uploaded the scan result of {url} to Discord.")
    else:
        print(f"Failed to upload the scan result of {url}. Status Code: {response.status_code}")
        print(f"Response content: {response.content}")

    os.remove(filename)


urls = []
with open('urls.txt', 'r') as file:
    urls = file.read().splitlines()

max_threads = 72
threads = []
urls_queue = iter(urls)

while True:
    threads = [t for t in threads if t.is_alive()]

    while len(threads) < max_threads:
        try:
            url = next(urls_queue)
            thread = threading.Thread(target=run_nmap, args=(url,))
            thread.start()
            threads.append(thread)
            # Remove the URL from the list in memory
            urls.remove(url)
        except StopIteration:
            break

    if not threads and next(urls_queue, None) is None:
        break

    time.sleep(10)
