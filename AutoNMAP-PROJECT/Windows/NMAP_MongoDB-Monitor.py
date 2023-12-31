import time
import requests
from pymongo import MongoClient

def get_document_count(collection):
    return collection.count_documents({})

def post_to_discord(webhook_url, message):
    data = {"content": message}
    response = requests.post(webhook_url, json=data)
    return response

def main():
    # Connect to MongoDB
    client = MongoClient('192.168.1.244', 27017)

    # Specify the database and collections
    db = client['AUTO_NMAP']
    low_collection = db['low']
    medium_collection = db['medium']
    high_collection = db['high']
    vhigh_collection = db['very_high']

    # Set your Discord webhook URL here
    webhook_url = "YOUR WEBHOOK"

    try:
        while True:
            # Get the current document count for each collection
            low_count = get_document_count(low_collection)
            medium_count = get_document_count(medium_collection)
            high_count = get_document_count(high_collection)
            vhigh_count = get_document_count(vhigh_collection)

            # Calculate the total count
            total_count = low_count + medium_count + high_count + vhigh_count

            # Create messages
            low_message = f"------------------\n**Low         :** {low_count}\n**Medium :** {medium_count}\n**High        :** {high_count}\n**V High    :** {vhigh_count}\n**Total       :** {total_count}\n------------------"

            # Post the messages to Discord
            post_to_discord(webhook_url, low_message)

            # Wait for a specified time interval (e.g., 60 seconds)
            time.sleep(600)
    except KeyboardInterrupt:
        print("Monitoring stopped.")

if __name__ == "__main__":
    main()
