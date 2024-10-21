import cv2
import numpy as np
import socket
import time

# Setup the socket
server_ip = '192.168.115.173'  # Replace with the server's IP address
server_port = 12345
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Load YOLO model
net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")
with open("coco.names", "r") as f:
    classes = [line.strip() for line in f.readlines()]

layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

# Load the video feed
cap = cv2.VideoCapture("ambulance_video.mp4")

# Variables for detecting flashing lights
flashing_lights_detected = False
flashing_lights_timer = 0  # Timer for how long flashing lights are detected
detection_time = 1  # Time in seconds to wait before sending a message (set to 1 second)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    height, width, _ = frame.shape

    # Preprocess the image for YOLO
    blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)

    class_ids = []
    confidences = []
    boxes = []

    # Process each detection
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]

            # Detect vehicles
            if confidence > 0.98 and classes[class_id] in ["car", "truck", "bus"]:
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)

                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    # Non-maxima suppression to filter overlapping boxes
    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

    # Detect flashing lights (red/blue)
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Define color ranges for flashing lights
    lower_blue = np.array([100, 150, 0])
    upper_blue = np.array([140, 255, 255])
    lower_red1 = np.array([0, 70, 50])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 70, 50])
    upper_red2 = np.array([180, 255, 255])

    # Create masks
    blue_mask = cv2.inRange(hsv_frame, lower_blue, upper_blue)
    red_mask1 = cv2.inRange(hsv_frame, lower_red1, upper_red1)
    red_mask2 = cv2.inRange(hsv_frame, lower_red2, upper_red2)
    light_mask = cv2.bitwise_or(blue_mask, red_mask1)
    light_mask = cv2.bitwise_or(light_mask, red_mask2)

    # Find contours of flashing lights
    contours, _ = cv2.findContours(light_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Check for detected vehicles and flashing lights
    flashing_lights_detected = False  # Reset this flag for each frame
    for i in range(len(boxes)):
        if i in indexes:
            x, y, w, h = boxes[i]
            label = str(classes[class_ids[i]])
            color = (0, 255, 0)  # Green for vehicles

            # Draw the bounding box for detected vehicles
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

            # Check for flashing lights near the vehicle
            for contour in contours:
                if cv2.contourArea(contour) > 700:  # Adjust based on size
                    cx, cy, cw, ch = cv2.boundingRect(contour)
                    if (x < cx + cw and x + w > cx and y < cy + ch and y + h > cy):
                        flashing_lights_detected = True
                        cv2.putText(frame, "Flashing Lights Detected", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                                    (0, 0, 255), 2)

    # Handle flashing lights detection timing
    if flashing_lights_detected:
        flashing_lights_timer += 1 / 30  # Assuming the video is 30 FPS
        if flashing_lights_timer >= detection_time:
            # Send message to the server
            message = "AMBULANCE_DETECTED"
            sock.sendto(message.encode(), (server_ip, server_port))
            flashing_lights_timer = 0  # Reset timer after sending
    else:
        flashing_lights_timer = 0  # Reset timer if no flashing lights detected

    # Show the frame
    cv2.imshow("Ambulance Detection", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
sock.close()
cv2.destroyAllWindows()
