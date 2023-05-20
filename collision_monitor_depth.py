#!/usr/bin/env python3

import cv2
import depthai as dai
import time

import math
import numpy as np

import zmq

TAG_SIZE = 0.03
COLLISION_THRESHOLD = 0.1
SERVER_IP = "127.0.0.1"

context = zmq.Context()

#  Socket to talk to server
print("Connecting to server…")
socket = context.socket(zmq.REQ)
socket.connect("tcp://{}:5556".format(SERVER_IP))
print("Connected to server")

def calculate_distance(tag_corners, tag_size, camera_intrinsics):
    """
    Calculates the distance between a camera and an April tag using its image coordinates.

    Args:
    - tag_corners: A numpy array of shape (4, 2) containing the image coordinates of the tag corners.
    - tag_size: The physical size of the April tag in meters.
    - camera_intrinsics: A numpy array of shape (3, 3) containing the intrinsic parameters of the camera.

    Returns:
    - The distance between the camera and the tag in meters.
    """

    # Calculate the actual size of the tag in pixels using perspective transformation
    actual_tag_size = np.linalg.norm(tag_corners[0] - tag_corners[1])
    tag_pixel_size = actual_tag_size / tag_size

    # Use the pinhole camera model to calculate the distance
    fx = camera_intrinsics[0][0]
    fy = camera_intrinsics[1][1]

    average_focal_length = (fx + fy) / 2.0
    distance = (tag_size * average_focal_length) / (2 * tag_pixel_size)

    return distance * 300 / 5

# Create pipeline
pipeline = dai.Pipeline()

# Define sources and outputs
monoLeft = pipeline.create(dai.node.MonoCamera)
aprilTag = pipeline.create(dai.node.AprilTag)

xoutMono = pipeline.create(dai.node.XLinkOut)
xoutAprilTag = pipeline.create(dai.node.XLinkOut)

xoutMono.setStreamName("mono")
xoutAprilTag.setStreamName("aprilTagData")

# Properties
monoLeft.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
monoLeft.setBoardSocket(dai.CameraBoardSocket.LEFT)

aprilTag.initialConfig.setFamily(dai.AprilTagConfig.Family.TAG_25H9)

# Linking
aprilTag.passthroughInputImage.link(xoutMono.input)
monoLeft.out.link(aprilTag.inputImage)
aprilTag.out.link(xoutAprilTag.input)
# always take the latest frame as apriltag detections are slow
aprilTag.inputImage.setBlocking(False)
aprilTag.inputImage.setQueueSize(1)

# advanced settings, configurable at runtime
aprilTagConfig = aprilTag.initialConfig.get()
aprilTagConfig.quadDecimate = 4
aprilTagConfig.quadSigma = 0
aprilTagConfig.refineEdges = True
aprilTagConfig.decodeSharpening = 0.25
aprilTagConfig.maxHammingDistance = 1
aprilTagConfig.quadThresholds.minClusterPixels = 5
aprilTagConfig.quadThresholds.maxNmaxima = 10
aprilTagConfig.quadThresholds.criticalDegree = 10
aprilTagConfig.quadThresholds.maxLineFitMse = 10
aprilTagConfig.quadThresholds.minWhiteBlackDiff = 5
aprilTagConfig.quadThresholds.deglitch = False
aprilTag.initialConfig.set(aprilTagConfig)

# Connect to device and start pipeline
with dai.Device(pipeline) as device:

    # Output queue will be used to get the mono frames from the outputs defined above
    monoQueue = device.getOutputQueue("mono", 8, False)
    aprilTagQueue = device.getOutputQueue("aprilTagData", 8, False)

    calibData = device.readCalibration()
    intrinsics = calibData.getCameraIntrinsics(dai.CameraBoardSocket.LEFT)

    color = (0, 255, 0)

    startTime = time.monotonic()
    counter = 0
    fps = 0

    while(True):
        inFrame = monoQueue.get()

        counter+=1
        current_time = time.monotonic()
        if (current_time - startTime) > 1 :
            fps = counter / (current_time - startTime)
            counter = 0
            startTime = current_time

        monoFrame = inFrame.getFrame()
        # frame = cv2.cvtColor(monoFrame, cv2.COLOR_GRAY2BGR)

        aprilTagData = aprilTagQueue.get().aprilTags
        for aprilTag in aprilTagData:
            topLeft = aprilTag.topLeft
            topRight = aprilTag.topRight
            bottomRight = aprilTag.bottomRight
            bottomLeft = aprilTag.bottomLeft

            center = (int((topLeft.x + bottomRight.x) / 2), int((topLeft.y + bottomRight.y) / 2))

            # cv2.line(frame, (int(topLeft.x), int(topLeft.y)), (int(topRight.x), int(topRight.y)), color, 2, cv2.LINE_AA, 0)
            # cv2.line(frame, (int(topRight.x), int(topRight.y)), (int(bottomRight.x), int(bottomRight.y)), color, 2, cv2.LINE_AA, 0)
            # cv2.line(frame, (int(bottomRight.x), int(bottomRight.y)), (int(bottomLeft.x), int(bottomLeft.y)), color, 2, cv2.LINE_AA, 0)
            # cv2.line(frame, (int(bottomLeft.x), int(bottomLeft.y)), (int(topLeft.x), int(topLeft.y)), color, 2, cv2.LINE_AA, 0)

            tag_corners = np.array([[topLeft.x, topLeft.y], [topRight.x, topRight.y], [bottomRight.x, bottomRight.y], [bottomLeft.x, bottomLeft.y]])
            distance = calculate_distance(tag_corners, TAG_SIZE, intrinsics)

            if distance < COLLISION_THRESHOLD:
            #     # Send collision message to the robot
                socket.send(bytes("collision", "utf-8"))
                #  Get the reply.
                message = socket.recv()
                print(f"Received reply [ {message} ]")
            # print("Distance: {:.2f}mm".format(distance * 1000))

            # idStr = "ID: " + str(aprilTag.id) + " z: {:.2f}mm".format(distance * 1000)
            # cv2.putText(frame, idStr, center, cv2.FONT_HERSHEY_TRIPLEX, 0.5, color)

        # cv2.putText(frame, "Fps: {:.2f}".format(fps), (2, frame.shape[0] - 4), cv2.FONT_HERSHEY_TRIPLEX, 0.4, (255,255,255))

        # cv2.imshow("mono", frame)

        if cv2.waitKey(1) == ord('q'):
            break