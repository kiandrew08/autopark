# Autopark

Autopark is an autonomous navigation and parking system designed for Viam-based rovers. The project leverages the sensors and modules available in the Viam Rover, including LiDAR, SLAM, and color detection, to create an efficient autoparking system.

## Video
Here is a quick video of the project:

[Watch the video here](https://youtu.be/r6XGrPIw9kE)

## Method and Solution

### Environment Generation
To simulate a parking lot, we use printed images of cars like the one below:

![Car Image Example](https://media.istockphoto.com/id/1145720458/photo/3d-illustration-of-generic-red-car-front-view.jpg?s=612x612&w=0&k=20&c=GeLrH7n-UMTX6l1ULskxQG9_6D_PTlW3m96RMAQzErU=)

Here is a diagram representing our parking lot:

![Diagram](https://raw.githubusercontent.com/kiandrew08/autopark/refs/heads/main/diagram.jpg)

### Our Solution
To detect empty spots in the parking lot, we utilized a Roboflow model called 'vehiclecount' to detect vehicles. We perform inference 10 times to mitigate the model's inaccuracy.

For navigation, we leveraged SLAM and color detection models of the Viam Rover using two approaches:

1. **SLAM**: We utilized the lidar of to leverage SLAM capabilities of the Viam Rover to navigate the parking lot and find an empty spot. The script for SLAM is available at **/src/slam.py**.

2. **Color Detection**: We utilized the color detection feature of the Viam Rover to align and navigate around the parking lot. The script for color detection is available at **/src/color-detection.py**.

### Navigation Process
1. The rover navigates through the parking lot lane.
2. At each spot, the rover performs the following steps:
   - Rotates 90 degrees to the left and then 90 degrees to the right to scan the parking spot.
   - Uses object detection to determine if the spot is empty or occupied by detecting a car object.
   - Aligns to the guiding lines and then parks itself.
3. This process repeats until the rover identifies an empty parking spot.

## How to Run

### Prerequisites
- Viam Rover with Viam SDK
- Python
- Roboflow API

### Steps
1. Clone this repository and navigate to the repository directory:
   ```bash
   git clone https://github.com/kiandrew08/autopark.git
   cd autopark
   ```
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Update your VIAM keys and Roboflow API key in the scripts and run the scripts.

- Run the SLAM script:
   ```bash
   python3 slam.py
   ```
- Run the color detection script:
   ```bash
   python3 color-detection.py
   ```

## Limitations
- The model might not be reliable.
- We do not have efficient obstacle detection.
- Additional limitations may exist.

## Contributors
- Ashok Timsina
- Kian Busico