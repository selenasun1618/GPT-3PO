import zmq
from time import sleep

from elevenlabslib import *

debug = False

user = ElevenLabsUser(API_KEY)
voice = user.get_voices_by_name("Rachel")[0]  # This is a list because multiple voices can have the same name

context = zmq.Context()

#  Socket to talk to server
print("Connecting to server…")
socket = context.socket(zmq.REQ)
socket.connect("tcp://192.168.1.100:5555")

def stand_up():
    send_request(b"stand")
    sleep(1)

def sit_down():
    send_request(b"sit")
    sleep(1)

def go_forward():
    command_velocity(1.0, 0, 1.0)

def go_backward():
    command_velocity(-1.0, 0, 1.0)

def turn_left():
    command_velocity(0, -1.3, 1.0)

def turn_right():  
    command_velocity(0, 1.3, 1.0)

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

def say(text):
    voice.generate_and_stream_audio(text)
