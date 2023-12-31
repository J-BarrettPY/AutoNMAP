# AUTO-NMAP

## Overview
AUTO-NMAP is a Python-based automated network scanning tool, developed in 2023. This tool was prominently featured in the 2023 AUTO-NMAP Project report, which successfully audited over 1 million addresses, demonstrating its efficiency and reliability in network security analysis.

## Features
- **Automated Network Scanning**: Scans and audits IP addresses within specified subnets.
- **MongoDB Integration**: Stores scan results in a MongoDB database for easy data management and retrieval.
- **JSON Data Management**: Provides an option to save scan data in JSON format, enhancing data portability.
- **Discord Integration**: Allows users to upload scan results to Discord channels using webhooks, facilitating real-time alerting and reporting.
- **Multi-threading Support**: Maximizes efficiency by running multiple scanning processes simultaneously.
- **CVE Severity Analysis**: Identifies and rates vulnerabilities based on CVE scores.
- **Customizable Scan Levels**: Offers different levels of scanning (low, medium, high, very high), depending on the detected vulnerabilities and open ports.

## Usage
- **Start AUTO-NMAP**: Run the main script to initiate the scanning process.
- **Configure IP Range**: Set the desired IP range in the script for targeted scanning.
- **Webhook Configuration**: Update the Discord webhook URLs in the script for notifications.

## Requirements
- Python 3.x
- MongoDB
- Network access to the target IP range
- Discord account and a server for notifications (optional)

## Contributions
Contributions made by Jest.

## Disclaimer
AUTO-NMAP is intended for legal and ethical use only. Users are responsible for complying with all applicable laws and regulations in their respective jurisdictions.

## License
Distributed under the MIT License. 
