#
# Copyright 2021-2022 Picovoice Inc.
#
# You may not use this file except in compliance with the license. A copy of the license is located in the "LICENSE"
# file accompanying this source.
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
# an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
#

import os
import struct
import wave
from datetime import datetime
import time

import openai
openai.api_key =  os.getenv("OPENAI_API_KEY")
import pvporcupine
import pvkoala
from pvrecorder import PvRecorder
# from led import *
# import zmq
from elevenlabslib import *

SERVER_IP = "127.0.0.1"
API_KEY = os.getenv("ELEVENLABS_API_KEY")
user = ElevenLabsUser(API_KEY)
voice = user.get_voices_by_name("Rachel")[0]  # This is a list because multiple voices can have the same name


# led_context = zmq.Context()
# led_socket = led_context.socket(zmq.REQ)
# led_socket.connect("tcp://{}:5557".format(SERVER_IP))

def say(text):
    voice.generate_and_play_audio(text, playInBackground=False)

def play_file(file):
    os.system("ffplay -nodisp -autoexit {}".format(file))

def record():

    access_key = os.getenv("PICOVOICE_API_KEY")
    keyword_paths = ['/home/pi/GPT-3PO/Hey_Rhea/Hey-Rhea_en_raspberry-pi_v2_2_0.ppn', '/home/pi/GPT-3PO/Thanks/Thanks_en_raspberry-pi_v2_2_0.ppn']
    sensitivities = [1.0, 1.0]
    audio_device_index = 2
    output_path = 'recording.wav'

    try:
        porcupine = pvporcupine.create(
            access_key=access_key,
            keyword_paths=keyword_paths,
            sensitivities=sensitivities)
        koala = pvkoala.create(access_key=access_key)
    except pvporcupine.PorcupineInvalidArgumentError as e:
        print("If all other arguments seem valid, ensure that '%s' is a valid AccessKey" % access_key)
        raise e
    except pvporcupine.PorcupineActivationError as e:
        print("AccessKey activation error")
        raise e
    except pvporcupine.PorcupineActivationLimitError as e:
        print("AccessKey '%s' has reached it's temporary device limit" % access_key)
        raise e
    except pvporcupine.PorcupineActivationRefusedError as e:
        print("AccessKey '%s' refused" % access_key)
        raise e
    except pvporcupine.PorcupineActivationThrottledError as e:
        print("AccessKey '%s' has been throttled" % access_key)
        raise e
    except pvporcupine.PorcupineError as e:
        print("Failed to initialize Porcupine")
        raise e

    keywords = list()
    for x in keyword_paths:
        keyword_phrase_part = os.path.basename(x).replace('.ppn', '').split('_')
        if len(keyword_phrase_part) > 6:
            keywords.append(' '.join(keyword_phrase_part[0:-6]))
        else:
            keywords.append(keyword_phrase_part[0])

    print('Porcupine version: %s' % porcupine.version)
    recorder = PvRecorder(
        device_index=audio_device_index,
        frame_length=koala.frame_length)
    recorder.start()

    begin_time = time.time()

    wav_file = None
    if output_path is not None:
        wav_file = wave.open(output_path, "w")
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
    frames = []
    print('Listening ... (press Ctrl+C to exit)')
    hey_rhea_detected = False
    try:
        while True:
            audio_frame = []
            for _ in range(2):
                pcm = recorder.read()
                pcm = koala.process(pcm)
                audio_frame.extend(pcm)
            result = porcupine.process(audio_frame)
            frames.extend(audio_frame)
            #if wav_file is not None:
                #wav_file.writeframes(struct.pack("h" * len(pcm), *pcm))

            if result >= 0:
                print('[%s] Detected %s' % (str(datetime.now()), keywords[result]))
                if keywords[result] == "Hey-Rhea":
                    start_timestamp = time.time() - begin_time
                    hey_rhea_detected = True
                    #say("What.")
                    play_file("start_listen.mp3")
                    frames = []
                elif keywords[result] == "Thanks" or keywords[result] == "Thank-you" and hey_rhea_detected:
                    end_timestamp = time.time() - begin_time
                    hey_rhea_detected = False
                    #say("Ughhh, ok. Gimme a sec.")
                    play_file("stop_listen.mp3")
                    break
                elif keywords[result] == "Thanks" and not hey_rhea_detected:
                    say("I didn't hear what you said. Say, Hey Rhea, to get my attention. Say, Thanks, when you're done talking.")
        
        wav_file.close()
        with wave.open(output_path, "r") as wav_file:
            params = wav_file.getparams()
            frame_rate = 16000
            start_frame = int(start_timestamp * frame_rate)
            end_frame = int(end_timestamp * frame_rate)

            #wav_file.setpos(start_frame)
            #frames = wav_file.readframes(end_frame - start_frame)

        with wave.open(output_path, "w") as wav_file:
            wav_file.setparams(params)
            wav_file.writeframes(struct.pack("h" * len(frames), *frames))
            #wav_file.writeframes(frames)

        audio_file= open(output_path, "rb")
        transcription = openai.Audio.transcribe("whisper-1", audio_file).text
        # with wave.open(output_path, "rb") as wav_file:
        #     transcription = openai.Audio.transcribe("whisper-1", wav_file).text

        recorder.delete()
        porcupine.delete()
        koala.delete()
        if wav_file is not None:
            wav_file.close()
        print(transcription)
        return transcription
    except:
        recorder.delete()
        porcupine.delete()
        koala.delete()
        if wav_file is not None:
            wav_file.close()
        assert False
        return ""


if __name__ == '__main__':
    record()
