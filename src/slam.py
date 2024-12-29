'''

---ROVER AUTO PARK---
APPROACH 2: Using SLAM and lidar
Uses lidar and SLAM map to localize itself on the map/parking lot and navigate its way to other road points
in the lane to realign and check presence of cars / free parking spots. Also uses roboflow's computer vision api for
car detection

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
        api_key_id="YOUR-API-ID"  # API key ID
    )
    return await RobotClient.at_address('wheeler2-main.te5kvfbjh1.viam.cloud', opts)

# This function checks if a car is present in the image using an inference model
def check_car(CLIENT, image):
    result = CLIENT.infer(image, model_id="vehiclecount/4")  # Use inference model to detect cars
    if result["predictions"]:
        return 1  # Car detected
    return 0  # No car detected

# Calculate the direction and distance to a destination point
async def get_direction_and_distance(current_position, destination_position):
    dx = destination_position[0] - current_position[0]
    dy = destination_position[1] - current_position[1]
    
    distance = math.sqrt(dx**2 + dy**2)  # Euclidean distance
    
    # Calculate angle in degrees
    angle_radians = math.atan2(dy, dx)  
    angle_degrees = math.degrees(angle_radians)
    
    return angle_degrees, distance

# Move the rover to a specific point
async def move_to_point(start, slam, viam_base):
    current_pose = await slam.get_position()  # Get the current position of the rover
    destination_position = start
    while True:
        current_pose = await slam.get_position()
        current_position = [current_pose.x, current_pose.y]
        print(current_pose)

        # Calculate direction and distance to destination
        direction, distance = await get_direction_and_distance(current_position, destination_position)
        if distance < 50:  # Stop if close enough to the destination
            break

        # Adjust direction to account for current orientation
        direction = direction - current_pose.theta
        if direction > 180:
            direction = -(360 - direction)

        # Spin to correct direction
        if abs(direction) > 1:
            await viam_base.spin(int(direction), 10)
            time.sleep(0.5)
        
        print("Going to point:", destination_position)
        print("Direction (theta):", direction)
        print("Distance:", distance)

        # Move towards the destination
        await viam_base.move_straight(int(distance / 2), 1000)
        print(await slam.get_position())

# Realign the rover's orientation (theta) to a reference angle
async def realign_theta(current_angle, slam, viam_base, ref_theta):
    print('\n\n-----------realigning---------\n\n')
    print(current_angle)
    # Calculate angle difference and normalize to [-180, 180]
    angle_diff = current_angle - ref_theta
    if angle_diff > 180:
        angle_diff -= 360
    elif angle_diff < -180:
        angle_diff += 360
    print(angle_diff)

    # Spin to correct alignment
    await viam_base.spin(-angle_diff, 90)
    time.sleep(0.5)

    # Get updated position after spinning
    current_pos = await slam.get_position()
    print("after spin realign: ", current_pos.theta)

# Main function to control the rover
async def main():
    print('Connecting to robot...')
    machine = await connect()
    print('Connected to robot')
    
    my_camera = Camera.from_robot(robot=machine, name="cam")  # Camera resource
    viam_base = Base.from_robot(machine, "viam_base")  # Base resource for movement
    slam = SLAMClient.from_robot(robot=machine, name="slam")  # SLAM resource for position tracking

    CLIENT = InferenceHTTPClient(
        api_url="https://detect.roboflow.com",
        api_key="roboflow-api-key"  # Replace with your actual API key
    )

    motion = MotionClient.from_robot(robot=machine, name="builtin")  # Motion service
    print(viam_base)
    print(motion)

    # Define waypoints for the rover to navigate
    points = [[-290.7, 183.62], [240.69, 201.71], [648.43, 205.84], [1056.17, 217.77]]
    
    i = 0
    start = points[i]
    await move_to_point(start, slam, viam_base)  # Move to the first point
    current_pose = await slam.get_position()
    theta = -5.5  # Target reference angle
    await realign_theta(current_pose.theta, slam, viam_base, theta)

    while True:
        i += 1
        await move_to_point(points[i], slam, viam_base)  # Move to the next point
        current_pose = await slam.get_position()
        await realign_theta(current_pose.theta, slam, viam_base, theta)  # Realign after movement

        await viam_base.spin(90, 90)  # Spin to scan the environment
        time.sleep(0.5)

        # Check for empty parking spots
        car = []
        for j in range(10):
            img = await my_camera.get_image(mime_type="image/jpeg")
            pil_image = viam_to_pil_image(img)
            car.append(check_car(CLIENT, pil_image))
        print(car)
        if sum(car) < 3:  # Spot is empty if fewer than 3 detections
            print("Empty spot found")
            break
        print("Spot occupied")

        await viam_base.spin(-180, 180)  # Spin 180 degrees to scan the opposite direction
        time.sleep(0.5)

        car = []
        for j in range(10):
            img = await my_camera.get_image(mime_type="image/jpeg")
            pil_image = viam_to_pil_image(img)
            car.append(check_car(CLIENT, pil_image))
        print(car)
        if sum(car) < 3:  # Spot is empty if fewer than 3 detections
            print("Empty spot found")
            break
        print("Spot occupied")
        
        await viam_base.spin(90, 90)  # Spin back to original direction
        await viam_base.move_straight(80, 1000)  # Move forward to the next point

        if i == 3: break  # Stop after visiting all points
    
    print("Parking now:")
    for i in range(3):
        await viam_base.move_straight(150, 800)  # Move forward to park
    await machine.close()


if __name__ == '__main__':
    asyncio.run(main())
