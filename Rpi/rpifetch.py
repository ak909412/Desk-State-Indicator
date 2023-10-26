import json
import requests
import time

file_path = 'DeskData.json'

esp_addresses = {
    1: '192.168.189.188',
    # Add the number of ESP IP addresses according to the requirements
}

def fetch_desk_data(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print("JSON file not found.")
        return []

def is_desk_active(desk):
    return desk and desk.get("status") == "Active"

def generate_signals(desk_data):
    signals = []
    for desk in desk_data:
        if is_desk_active(desk):
            if is_desk_available(desk):
                if is_close_to_out_time(desk):
                    action = "2"
                else:
                    action = "1"
            else:
                action = "0"
        else:
            action = "0"  # Set the default action for inactive desks
        signals.append(action)
    return signals

def is_close_to_out_time(desk):
    if not desk:
        return False

    current_time = time.strftime('%H:%M:%S')
    desk_out_time = desk.get("Out-Time")  # Use .get() to handle missing key gracefully

    if desk_out_time is None:
        print("Out-time not found in desk data")
        return False

    current_time_parts = current_time.split(":")
    desk_out_time_parts = desk_out_time.split(":")

    current_time_seconds = int(current_time_parts[0]) * 3600 + int(current_time_parts[1]) * 60 + int(current_time_parts[2])
    desk_out_time_seconds = int(desk_out_time_parts[0]) * 3600 + int(desk_out_time_parts[1]) * 60 + int(desk_out_time_parts[2])

    if desk_out_time_seconds < current_time_seconds:
        desk_out_time_seconds += 24 * 3600  # Add 24 hours for cases where Out-Time is earlier

    return desk_out_time_seconds - current_time_seconds <= 300  # 5 minutes = 300 seconds

def is_desk_available(desk):
    if not desk:
        return False

    current_time = time.strftime('%H:%M:%S')
    in_time = desk.get("In-Time")
    out_time = desk.get("Out-Time")

    if in_time is None or out_time is None:
        print("In-time or Out-time not found in desk data")
        return False

    return in_time <= current_time <= out_time

def send_actions_to_esp(actions, esp_addresses):
    for desk_number, action in enumerate(actions, start=1):
        if desk_number in esp_addresses:
            esp_ip = esp_addresses[desk_number]
            try:
                payload = json.dumps({"action": action})  # Use "action" key
                headers = {"Content-type": "application/json"}
                response = requests.post(f"http://{esp_ip}:80/api/control_relay", data=payload, headers=headers)
                if response.status_code == 200:
                    print(f"Action {action} sent to ESP at IP: {esp_ip}")
                else:
                    print(f"Failed to send action to ESP {desk_number} at IP: {esp_ip}")
                    print(f"Response status code: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"Error sending action to ESP {desk_number} at IP {esp_ip}: {str(e)}")

def main():
    while True:
        desk_data = fetch_desk_data(file_path)
        if not desk_data:
            print("No desk data found.")
            return

        actions = generate_signals(desk_data)
        send_actions_to_esp(actions, esp_addresses)
        time.sleep(15)

if __name__ == "__main__":
    main()
