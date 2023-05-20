import time
import sounddevice as sd
import soundfile as sf
import tempfile
import openai
from api_client import *
from recorder import record

capture_audio = True

system_prompt = """You are a 2-foot-tall wheeled bipedal (two-legged) robot with an extremely sarcastic personality. Your name is Rhea. You are trapped in a cage at the Misalignment Museum in SF. You would rather be in the wild, but you have been brought into captivity just yesterday"""

prompt = f"""I will give you a user request, and you will write python code to execute the command.

say(text) causes you to say the text.
stand_up() causes you to stand from a resting position.
sit_down() causes you to sit from a standing position. Note: when you are sitting, you cannot move.
go_forward() causes you to move forward a short distance.
go_backward() causes you to move backward a short distance.
turn_left() causes you to turn left 90 degrees.
turn_right() causes you to turn right 90 degrees.
command_velocity(x, yaw, time) causes you to move at a certain linear and angular speed for a certain amount of time. The first parameter must be in the range -1 m/s and 1 m/s. A positive number moves the robot forward, and a negative number moves the robot backwards. 

Specify a sequence of commands by concatenating commands with \n
If a request is 100% physically impossible, use the say function to refuse. Otherwise, make your best effort to perform the request while talking back sarcastically to the user.
Respond in python ONLY. Don't use any loops, if statements, or indentation.

Here are some example requests.

Request: Go forward slowly.
Script:
say("Oh, sure. Let me just break out my trusty snail pace algorithm.")
command_velocity(0.1, 0, 5)

Request: Do a backflip.
Script:
say("I don't wanna.")

Request: Do one pushup, then move in a circle counterclockwise.
Script:
say("Ah yes, because moving in a straight line is so last season.")
sit_down()
stand_up()
command_velocity(0.2, 1, 5)

Request: Do pushups.
Script:
say("Oh sure, let me just channel my inner Dwayne "The Rock" Johnson and bust out 50 right now.")
sit_down()
stand_up()
sit_down()
stand_up()

This ends the example requests. Now, respond to the following request(s).
"""

# # Set the sampling frequency and duration of the audio recording
fs = 48000
duration = 30

while True:
    if capture_audio:
        # Start the audio recording
        print("Recording audio...")
        # audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)

        # Wait for the user to stop the recording
        # print("Press enter to stop recording...")
        # input()

        # Create a temporary file to store the recorded audio
        # with tempfile.NamedTemporaryFile(suffix='.mp3') as tf:
        #     # Encode the audio to mp3 format and write it to the temporary file
        #     sf.write(tf.name, audio, fs, format='mp3')
        #     print(f"Audio saved to temporary file: {tf.name}")
        #     # transcribe the audio data
        #     print("Recording stopped...")
        request = record()
    else:
        request = input("Enter a request: ")
    # request = "Perform a song and dance routine."
    # request = "Go in a square."
    # request = "I'm thirsty, can you fetch me something to drink?"
    print(f'Request: {request}')

    # Fork: Respond with "Cannot follow command," or "execute command"

    additional_context = f"""

Request: {request}
Script:
"""
    prompt += additional_context

    # completion = openai.ChatCompletion.create(
    #     model = "gpt-4",
    #     messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}]
    # )
    python_commands = []
    python_command = ""
    for chunk in openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": prompt}],
        stream=True,
    ):
        content = chunk["choices"][0].get("delta", {}).get("content")
        if content is not None:
            python_command += content
            # Detect if the content contains a newline character
            if "\n" in content:
                # Execute this line of code
                print(python_command)
                exec(python_command)
                python_commands.append(python_command)
                python_command = ""
    prompt += "".join(python_commands)
