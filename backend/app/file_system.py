"""Module to interface with the os filesystem"""

import os
import csv
import hashlib
import subprocess
import os
from subprocess import DEVNULL
from .protocol import response

corpus_name = "transcript.v.1.4.txt"

prompts_dir = prompts_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "../prompts/"
)
os.makedirs(prompts_dir, exist_ok=True)
prompts_path = os.path.join(
    prompts_dir,
    "../prompts",
    corpus_name
)

audio_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "../audio_files/"
)
os.makedirs(audio_dir, exist_ok=True)

temp_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "../tmp/"
)
os.makedirs(temp_path, exist_ok=True)


class AudioFS:
    """API Class for audio handling."""

    @staticmethod
    def save_audio(path: str, audio: bytes):
        """Save audio after ffmpeg conversion (stereo, samplerate 44.100Hz) to disk.

        Args:
            path (str): Directory where recordings are saved (./backend/audio_files/<user-id>).
            audio (bytes): Raw audio data.
        """
        webm_file_name = path + ".webm"

        with open(webm_file_name, 'wb+') as f:
            f.write(audio)
        
        subprocess.call(
            'ffmpeg -i {} -ab 160k -ac 2 -ar 44100 -vn {}.wav -y'.format(
                webm_file_name, path
            ),
            shell=True
        )
        os.remove(webm_file_name)

    @staticmethod
    def save_meta_data(file_dir, wav_file_id, prompt):
        """Write a line for every saved recording in metadata.csv file.

        CSV file format is Audio file path|Original script|Expanded script|Decomposed script|Audio duration (seconds)|English translation

        Args:
            uuid: user-id.
            wav_file_id (str): unique id of wavefile.
            prompt (str): Text of recorded phrase.
        """
        path = os.path.join(audio_dir, 'transcript.v.1.4.txt')
        data = "{}|{}|{}|{}|{}|{}\n".format(f'{file_dir}/{wav_file_id}', prompt, prompt, prompt, 0, '')

        same = False
        if os.path.isfile(path):
            with open(path, 'r+') as f:
                lines = f.readlines()
                if len(lines) > 0 and lines[-1] == data:
                    same = True

        if not same:
            with open(path, 'a') as f:
                f.write(data)

    @staticmethod
    def save_skipped_data(user_audio_dir, uuid, prompt):
        """Write text phrase for every skipped recording in userid-skipped.txt file.

        Args:
            user_audio_dir (str): Base directory for user recordings.
            uuid (str): user-id.
            prompt (str): Text phrase that has been skipped.
        """
        path = os.path.join(user_audio_dir, '%s-skipped.txt' % uuid)
        data = "{}\n".format(prompt.lstrip('___SKIPPED___'))

        with open(path, 'a') as f:
            f.write(data)


    @staticmethod
    def get_audio_path(uuid: str) -> str:
        return os.path.join(audio_dir, uuid)

    @staticmethod
    def create_file_name(prompt: str):
        return hashlib.md5(prompt.encode("utf-8")).hexdigest()


class PromptsFS:
    """API Class for Prompt handling."""
    def __init__(self):
        self.data = []
        self.file_path = []
        _1 = []
        _2 = []
        _3 = []
        _4 = []
        with open(prompts_path, 'r', encoding='utf8') as f:
            prompts = csv.reader(f, delimiter="|")
            for p in prompts:
                if p[0][0] == '1':
                    _1.append(p)
                elif p[0][0] == '2':
                    _2.append(p)
                elif p[0][0] == '3':
                    _3.append(p)
                elif p[0][0] == '4':
                    _4.append(p)

            while True:
                if _1:
                    element = _1.pop(0)
                    self.file_path.append(element[0])
                    self.data.append(element[2])
                if _2:
                    element = _2.pop(0)
                    self.file_path.append(element[0])
                    self.data.append(element[2])
                if _3:
                    element = _3.pop(0)
                    self.file_path.append(element[0])
                    self.data.append(element[2])
                if _4:
                    element = _4.pop(0)
                    self.file_path.append(element[0])
                    self.data.append(element[2])
                if not _1 and not _2 and not _3 and not _4:
                    break

    def get(self, prompt_number: int) -> response:
        """Get text from corpus by prompt number.
        If end of corpus file is reached then '___CORPUS_END___' is returned as phrase.

        Args:
            prompt_number (int): Number of requested prompt from corpus.

        Returns:
            response: Text phrase from corpus, length of prompt.
        """
        try:
            d = {
                "prompt": self.data[prompt_number],
                "file_path": self.file_path[prompt_number],
                "total_prompt": len(self.data)
            }
        except IndexError as e:
            d = {
                "prompt": "___CORPUS_END___",
                "file_path": "",
                "total_prompt": 0
            }            
        return response(True, data=d)
