import zmq
from time import sleep

import os

from elevenlabs import generate, stream, set_api_key
set_api_key(os.getenv("ELEVENLABS_API_KEY"))

debug = True
SERVER_IP = "127.0.0.1"

X_VELOCITY = 0.5
YAW_VELOCITY = 1.57


context = zmq.Context()

#  Socket to talk to server
print("Connecting to server…")
socket = context.socket(zmq.REQ)
socket.connect("tcp://{}:5555".format(SERVER_IP))

def stand_up():
    send_request(b"stand")
    sleep(1)

def sit_down():
    send_request(b"sit")
    sleep(1)

def go_forward():
    command_velocity(X_VELOCITY, 0, 1.0)

def go_backward():
    command_velocity(-X_VELOCITY, 0, 1.0)

def turn_left():
    command_velocity(0, -YAW_VELOCITY, 1.0)

def turn_right():
    command_velocity(0, YAW_VELOCITY, 1.0)

def command_velocity(x, yaw, time):
    send_request(bytes("move_{}_{}_{}".format(x, yaw, time), "utf-8"))
    sleep(time + 1.0)

def send_request(request):
    print(f"Sending request {request} …")

    if not debug:
        socket.send(request)

        #  Get the reply.
        message = socket.recv()
        print(f"Received reply {request} [ {message} ]")

def say(text, blocking=True):
    audio_stream = generate(
        text=text,
        voice="Rachel",
        stream=True
    )

    stream(audio_stream)

