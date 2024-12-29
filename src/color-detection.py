'''
---ROVER AUTO PARK---
APPROACH 1: Using Color Detection
Uses color detection to realign itself on the road/lane in the parking lot and uses roboflow's api 
as computer vision to detect cars

'''

import asyncio
from viam.robot.client import RobotClient
from viam.components.base import Base
from viam.services.slam import SLAMClient, Pose
from viam.services.motion import MotionClient
from viam.services.vision import VisionClient
from viam.components.camera import Camera
import random
from inference_sdk import InferenceHTTPClient
from viam.media.utils.pil import viam_to_pil_image
import math
import time



# Connect to the robot
async def connect():
    opts = RobotClient.Options.with_api_key(
        api_key='YOUR-API-KEY',  # API key for authentication
        api_key_id='YOUR-API-ID'  # API ID
    )
    return await RobotClient.at_address('wheeler-main.d4e6mcnnuf.viam.cloud', opts)

# Function to check if a car is detected in the image
def check_car(CLIENT, image):
    result = CLIENT.infer(image, model_id="vehiclecount/4")  # Inference model to detect vehicles
    if result["predictions"]:
        return 1  # Car detected
    return 0  # No car detected

# Determine if an object is on the left, right, or centered based on its bounding box
def leftOrRight(detections, midpoint):
    largest_area = 0
    largest = {"x_max": 0, "x_min": 0, "y_max": 0, "y_min": 0}  # Default bounding box
    if not detections:  # If no detections are found
        print("nothing detected :(")
        return -1
    for d in detections:  # Find the largest detected object
        a = (d.x_max - d.x_min) * (d.y_max - d.y_min)  # Calculate area of the bounding box
        if a > largest_area:
            a = largest_area
            largest = d
    centerX = (largest.x_min + largest.x_max) / 2  # Calculate center X coordinate
    if centerX < midpoint - midpoint / 10:  # Object is to the left
        return 0
    if centerX > midpoint + midpoint / 10:  # Object is to the right
        return 2
    else:
        return 1  # Object is centered

# Spin the robot until it finds an object
async def find_colored_object(detector, base, direction):
    a = 0
    found = False
    while not found:
        detections = await detector.get_detections_from_camera('cam')  # Get detections from the camera
        if detections:
            found = True  # Stop spinning if an object is detected
            print('object found')
            break
        if direction == 0:  # Determine spin direction
            a = 1
        else:
            a = -1
        await base.spin(velocity=10, angle=a * 10)  # Spin robot incrementally
    return detections

# Rotate the robot until the object is centered in the camera view
async def rotate_until_object_on_center(detector, base, found_object, midpoint):
    print("Rotating to put on center")
    vel = 10
    angle = 1
    found_objects = []
    global global_direction
    direction = leftOrRight(found_object, midpoint)  # Determine if object is left, right, or centered
    while direction != 1:  # Keep rotating until the object is centered
        if direction == 0:  # Object is on the left
            global_direction = 0
            print("left")
            await base.spin(angle, vel)
        if direction == 2:  # Object is on the right
            global_direction = 2
            print("right")
            await base.spin(-1 * angle, vel)
        found_objects = await find_colored_object(detector, base, direction)  # Check again for the object
        print("Found objects: ", found_objects)
        direction = leftOrRight(found_objects, midpoint)
    print("Done")
    return True

# Main logic for the robot to find and park in an empty spot
async def main():
    print('Connecting to robot...')
    machine = await connect()  # Establish connection with the robot
    print('Connected to robot')
    my_camera = Camera.from_robot(robot=machine, name="cam")  # Initialize camera
    viam_base = Base.from_robot(machine, "viam_base")  # Initialize robot base for movement

    CLIENT = InferenceHTTPClient(
        api_url="https://detect.roboflow.com",
        api_key="roboflow-api-key"  # Replace with your actual API key
    )

    num_rows = 3  # Number of rows to scan
    curr_row = 0
    await viam_base.move_straight(400, 1000)  # Move forward to start scanning

    # Initialize the vision detector
    my_detector = VisionClient.from_robot(machine, "vision")
    frame = await my_camera.get_image(mime_type="image/jpeg")
    pil_frame = viam_to_pil_image(frame)  # Convert camera frame to PIL format

    # Find and center a detected object
    found_objects = await find_colored_object(my_detector, viam_base, 0)
    rotate = await rotate_until_object_on_center(my_detector, viam_base, found_objects, pil_frame.size[0] / 2)

    # Loop through rows to find an empty parking spot
    while curr_row < num_rows:
        found_objects = await find_colored_object(my_detector, viam_base, 0)
        rotate = await rotate_until_object_on_center(my_detector, viam_base, found_objects, pil_frame.size[0] / 2)
        await viam_base.spin(90, 90)  # Rotate to scan for parking spots

        car = []
        for j in range(10):  # Take multiple frames to check for cars
            img = await my_camera.get_image(mime_type="image/jpeg")
            pil_image = viam_to_pil_image(img)
            car.append(check_car(CLIENT, pil_image))
        print(car)
        if sum(car) < 3:  # If fewer than 3 cars are detected, the spot is empty
            print("Empty spot found")
            break
        print("Spot occupied")

        await viam_base.spin(-180, 180)  # Scan in the opposite direction
        car = []
        for j in range(10):
            img = await my_camera.get_image(mime_type="image/jpeg")
            pil_image = viam_to_pil_image(img)
            isCarPresent = check_car(CLIENT, pil_image)
            car.append(isCarPresent)
        print(car)
        if sum(car) < 3:  # Check again for empty spots
            print("Empty spot found")
            break
        print("Spot occupied")
        
        await viam_base.spin(90, 90)  # Return to original direction
        await viam_base.move_straight(400, 1000)  # Move to the next row

        curr_row += 1
    
    print("Parking now:")
    await viam_base.move_straight(400, 1000)  # Move forward to park
    await machine.close()  # Close connection with the robot


if __name__ == '__main__':
    asyncio.run(main())
