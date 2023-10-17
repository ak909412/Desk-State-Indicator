import json
import requests
import time

file_path = 'DeskData.json'

esp_addresses = {
    1: '192.168.1.205',
    #Add the number of esp IP address according to the requirments
}

def fetch_desk_data(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print("JSON file not found.")
        return []

def generate_signals(desk_data):
    signals = []
    for desk in desk_data:
        is_available = is_desk_available(desk)
        signal = f"{2 if is_close_to_out_time(desk) else (1 if is_available else 0)}"
        signals.append(signal)
    return signals

def is_close_to_out_time(desk):
    if not desk:
        return False

    current_time = time.strftime('%H:%M:%S')
    desk_out_time = desk["Out-Time"]
    
    if desk_out_time is None:
        print ("Out-time not found in desk data")
        return False

    current_time_parts = current_time.split(":")
    desk_out_time_parts = desk_out_time.split(":")

    current_time_seconds = int(current_time_parts[0]) * 3600 + int(current_time_parts[1]) * 60 + int(current_time_parts[2])
    desk_out_time_seconds = int(desk_out_time_parts[0]) * 3600 + int(desk_out_time_parts[1]) * 60 + int(desk_out_time_parts[2])

    return desk_out_time_seconds - current_time_seconds <= 300  # 5 minutes = 300 seconds

def is_desk_available(desk):
    if not desk:
        return False

    current_time = time.strftime('%H:%M:%S')
    return desk["In-Time"] <= current_time <= desk["Out-Time"]

def send_signals_to_esp(signals, esp_addresses):
    for desk_number, signal in enumerate(signals, start=1):
        if desk_number in esp_addresses:
            esp_ip = esp_addresses[desk_number]
            try:
                payload = json.dumps({"signal" : signal})
                headers = {"Content-type" : "application/json"}
                response = requests.post(f"http://{esp_ip}:80/api/receive_signal", data=payload, headers=headers)
                if response.status_code == 200:
                    print(f"Signal {signal} sent to ESP at IP: {esp_ip}")
                    
                else:
                    print(f"Failed to send signal to ESP {desk_number} at IP: {esp_ip}")
                    print(f"Response status code: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"Error sending signal to ESP {desk_number} at IP {esp_ip}: {str(e)}")

def main():
    while True:
        desk_data = fetch_desk_data(file_path)
        if not desk_data:
            print("No desk data found.")
            return

        signals = generate_signals(desk_data)
        send_signals_to_esp(signals, esp_addresses)
        time.sleep(15)  

if __name__ == "__main__":
    main()
