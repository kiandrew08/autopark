# Rover AutoParking 

## Problem
The rover needs to be parked, and it is tasked to find an open parking spot and park automatically by itself.

## Solution
1. The rover navigates through the parking lot lane.
2. At each spot, the rover performs the following steps:
   - Rotates 90 degrees to the left and then 90 degrees to the right to scan the parking spot.
   - Uses object detection to determine if the spot is empty or occupied by detecting a car object.
   - After that, the rover aligns to the guiding lines and then parks itself.

3. This process repeats until the rover identifies an empty parking spot.

We plan to use printed images of cars, similar to the example below, to simulate parked vehicles for testing.

![Car Image Example](https://media.istockphoto.com/id/1145720458/photo/3d-illustration-of-generic-red-car-front-view.jpg?s=612x612&w=0&k=20&c=GeLrH7n-UMTX6l1ULskxQG9_6D_PTlW3m96RMAQzErU=
)

## Assumptions
- It is assumed that there is at least one available parking slot in the parking lot.

## How it Works
- The rover will continue scanning the parking lane until it successfully detects an open spot.
- Once an empty spot is found, the rover will autonomously park itself.

---
