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


import argparse
import struct
import wave

from pvrecorder import PvRecorder
import pvporcupine

# AccessKey obtained from Picovoice Console (https://console.picovoice.ai/)
access_key = "${ACCESS_KEY}"

handle = pvporcupine.create(access_key=access_key, keywords=['porcupine'])

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--show_audio_devices",
        help="List of audio devices currently available for use.",
        action="store_true")

    parser.add_argument(
        "--audio_device_index",
        help="Index of input audio device.",
        type=int,
        default=-1)

    parser.add_argument(
        "--output_path",
        help="Path to file to store raw audio.",
        default=None)

    args = parser.parse_args()

    if args.show_audio_devices:
        devices = PvRecorder.get_audio_devices()
        for i in range(len(devices)):
            print("index: %d, device name: %s" % (i, devices[i]))
    else:
        device_index = args.audio_device_index
        output_path = args.output_path

        recorder = PvRecorder(device_index=device_index, frame_length=512)
        print("pvrecorder.py version: %s" % recorder.version)

        recorder.start()
        print("Using device: %s" % recorder.selected_device)

        wavfile = None

        try:
            if output_path is not None:
                wavfile = wave.open(output_path, "w")
                # noinspection PyTypeChecker
                wavfile.setparams((1, 2, 16000, 512, "NONE", "NONE"))

            while True:
                pcm = recorder.read()
                if wavfile is not None:
                    wavfile.writeframes(struct.pack("h" * len(pcm), *pcm))

        except KeyboardInterrupt:
            print("Stopping...")
        finally:
            recorder.delete()
            if wavfile is not None:
                wavfile.close()


if __name__ == "__main__":
    main()