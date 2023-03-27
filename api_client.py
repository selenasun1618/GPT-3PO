import zmq
from time import sleep

from elevenlabslib import *

API_KEY = "2d876cea3d5fefadc247d37f6926daae"

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

def command_velocity(x, yaw, time):
    send_request(bytes("move_{}_{}_{}".format(x, yaw, time), "utf-8"))
    sleep(time)

def send_request(request):
    print(f"Sending request {request} …")
    socket.send(request)

    #  Get the reply.
    message = socket.recv()
    print(f"Received reply {request} [ {message} ]")

def say(text):
    voice.generate_and_stream_audio(text)
