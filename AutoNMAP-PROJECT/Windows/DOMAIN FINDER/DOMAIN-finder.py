import subprocess
import re
import threading
from datetime import datetime

def run_nmap_scan(segment, seen_domains, lock, filename):
    command = f"nmap -sL -R {segment}"

    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    for line in process.stdout:
        line = line.decode('utf-8')

        print(line, end='')

        match = re.search(r'Nmap scan report for ([\w\.-]+\.[a-zA-Z]{2,})', line)
        if match:
            domain = match.group(1)

            with lock:
                if domain not in seen_domains:
                    seen_domains.add(domain)
                    with open(filename, 'a') as file:
                        file.write(domain + '\n')

def main():
    lock = threading.Lock()
    seen_domains = set()

    for subnet in range(10, 50):
        threads = []
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"{today}_URLS.txt"

        for i in range(300):  # Changed this line from 72 to 300
            segment = f"{subnet}.{i*4}.0.0/22"
            thread = threading.Thread(target=run_nmap_scan, args=(segment, seen_domains, lock, filename))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

if __name__ == "__main__":
    main()
