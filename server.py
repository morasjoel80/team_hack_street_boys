import socket
import time
import threading

# Setup the socket
host = '0.0.0.0'  # Listen on all interfaces
port = 12345
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((host, port))

# Traffic light states
traffic_light_state = {"side1": "RED", "side2": "GREEN"}  # Initial state (side1 is ambulance side)
lights_operational = True  # Indicates whether the traffic lights are operational
ambulance_detected = False  # Flag to track ambulance detection
ambulance_pass_duration = 10  # Duration for ambulance to pass in seconds

# Function to handle normal traffic light sequence
def traffic_light_sequence():
    global traffic_light_state
    while True:
        if not ambulance_detected and lights_operational:
            # Cycle through normal traffic light operation
            print("Normal traffic operation. side1: RED, side2: GREEN")
            traffic_light_state["side1"] = "RED"
            traffic_light_state["side2"] = "GREEN"
            time.sleep(10)  # Duration for side2 to be green

            # Switch side2 to yellow and prepare side1 for green
            print("Switching side2 to YELLOW, preparing side1 to GREEN.")
            traffic_light_state["side2"] = "YELLOW"
            time.sleep(3)  # Yellow light duration

            print("Switching side1 to GREEN, side2 to RED.")
            traffic_light_state["side1"] = "GREEN"
            traffic_light_state["side2"] = "RED"
            time.sleep(10)  # Duration for side1 to be green

            # Switch side1 to yellow before turning red
            print("Switching side1 to YELLOW, preparing side2 to GREEN.")
            traffic_light_state["side1"] = "YELLOW"
            time.sleep(3)  # Yellow light duration

        time.sleep(1)  # Avoid tight loops during checks

# Start the normal traffic light sequence in a separate thread
threading.Thread(target=traffic_light_sequence, daemon=True).start()

print("Server is waiting for a connection...")

def notify_police(message):
    """Function to notify the traffic police (prints the message)."""
    print(f"Notification to Traffic Police: {message}")

while True:
    # Wait for a message from the client
    message, client_address = server_socket.recvfrom(1024)
    message = message.decode()
    print(f"Received message: '{message}' from {client_address}")

    if message == "AMBULANCE_DETECTED":
        if not lights_operational:
            print("Traffic lights are malfunctioning! Notify police to manage traffic.")
            notify_police("Traffic lights malfunctioning! Please allow ambulance to pass manually.")
        else:
            if not ambulance_detected:
                print("Ambulance detected! Switching side1 to GREEN for ambulance.")
                traffic_light_state["side1"] = "GREEN"
                traffic_light_state["side2"] = "RED"  # Stop other side

                ambulance_detected = True
                # Allow the ambulance to pass for the set duration
                time.sleep(ambulance_pass_duration)

                print("Ambulance has passed. Resuming normal traffic operation.")
                ambulance_detected = False  # Reset flag to return to normal operation
    elif message == "LIGHTS_NOT_WORKING":
        lights_operational = False
        print("Traffic lights are not operational! Notifying traffic police.")
        notify_police("Traffic lights malfunctioning at the intersection. Manual traffic control needed.")
    elif message == "LIGHTS_WORKING":
        lights_operational = True
        print("Traffic lights have been restored to operational status.")
