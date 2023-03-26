import openai
from api_client import *
import time

openai.api_key = "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"
#"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"

# Whisper API transcription
audio_file= open("whisper_recording.mp3", "rb")
request = openai.Audio.transcribe("whisper-1", audio_file).text
print(f'Request: {request}')

# Fork: Respond with "Cannot follow command," or "execute command"

prompt = f"""I will give you a user request, and you will write python code to execute the command on a robot. You may use 3 commands: ‘stand_up()’, ’sit_down()’, and ’command_velocity(meters/second, radians/second, time duration).’
say(text) tells the robot to say the text.
stand_up() tells the robot to stand from a resting position."
sit_down() tells the robot to sit from a standing position.
command_velocity() tells the robot to move at a certain linear and angular speed. The first parameter must be in the range -1 m/s and 1 m/s. A positive number moves the robot forward, and a negative number moves the robot backwards. 
The second parameter is the robot’s angular velocity, and must be in the range -1 to 1 (-4 radians/second to 4 radians/second). A positive number turns the robot to the left, and a negative number turns the robot to the right.
The third parameter (time duration) is the length of time these commands will be executed.
Specify a sequence of commands by concatenating commands with “\n". Use as many commands as you need to complete the command, but DO NOT use any unnecessary commands, otherwise I will be VERY MAD. Be as creative as possible, and try to make the robot dance if requested, or I will be VERY VERY MAD."
If a command cannot be executed with the given commands, output “say("I don't wanna.")". Otherwise, include say("(generate something sarcastic)")".
Response in python ONLY, otherwise I will be extremely upset. Output the code with double quotes around it, like "code"

Request: “Walk forward slowly."
Script: "say("Oh, sure. Let me just break out my trusty snail pace algorithm.")\ncommand_velocity(0.1, 0, 5)"

Request: “Do a backflip."
Script: "say("I don't wanna.")"

Request: “Do one pushup, then walk in a circle counterclockwise."
Script: "say("Ah yes, because walking in a straight line is so last season.")\nsit_down()\nstand_up()\ncommand_velocity(0.2, 1, 5)"

Request: "Do pushups."
Script: "say("Oh sure, let me just channel my inner Dwayne "The Rock" Johnson and bust out 50 right now.")\nsit_down()\nstand_up()\nsit_down()\nstand_up()"

Request: {request}
Script: 
"""

completion = openai.ChatCompletion.create(
    model = "gpt-3.5-turbo",
    messages = [{"role": "user", "content": prompt}]
)

python_command = completion.choices[0].message.content

# if python_command[0] == '"':
python_command = python_command[1:-1]
python_command_lines = python_command.split("\n")
#print(python_command)
for line in python_command_lines:
    exec(line)