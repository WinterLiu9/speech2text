import openai
import pydub.playback
from pydub import AudioSegment
import math
import yaml
import os
from pathlib import Path

def load_yaml_file(path):
    with open(path, 'r') as f:
        res = yaml.safe_load(f)
    return res

def _write_file(path, file_content):
    root = os.path.split(path)[0]
    Path(root).mkdir(parents=True, exist_ok=True)
    print(f'Writing text to {path}')
    with open(path, "w") as f:
        f.write(file_content)

class SplitWavAudioMubin():
    def __init__(self, folder, filename):
        self.folder = folder
        self.filename = filename
        self.filepath = folder + '/' + filename
        pydub.AudioSegment.converter = '/usr/bin/ffmpeg'
        # self.audio = AudioSegment.from_mp3(self.filepath)
        self.audio = AudioSegment.from_file(self.filepath)
        self.split_files = []

    def get_duration(self):
        return self.audio.duration_seconds

    def single_split(self, from_min, to_min, split_filename):
        t1 = from_min * 60 * 1000
        t2 = to_min * 60 * 1000
        split_audio = self.audio[t1:t2]
        split_audio.export(self.folder + '/' + split_filename, format="mp3")

    def multiple_split(self, min_per_split):
        total_mins = math.ceil(self.get_duration() / 60)
        for i in range(0, total_mins, min_per_split):
            split_fn = str(i) + '_' + self.filename
            self.single_split(i, i + min_per_split, split_fn)
            self.split_files.append(split_fn)
            print(str(i) + ' Done')
            if i == total_mins - min_per_split:
                print('All splited successfully')

class OpenaiAPI():
    def __init__(self, folder, file, files, language):
        self.folder = folder
        self.file = file
        self.files = [open(folder + '/' + f, 'rb') for f in files]
        self.texts = []
        self.api_key = load_yaml_file('/software/django-upload/config/token.yaml')['token']
        self.language = language

    def call(self):
        openai.api_key = self.api_key
        for file in self.files:
            transcript = openai.Audio.transcribe("whisper-1", file, language=self.language)
            print(transcript.to_dict())
            td = transcript.to_dict()
            self.texts.append(td.get('text'))
        _write_file(self.folder + '/' + self.file.replace('.mp3', '.txt').replace('.m4a', '.txt'), "\n\n\n".join(self.texts))


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    folder = ''
    file = 'Marina Bay Link Mall.m4a'
    split_wav = SplitWavAudioMubin(folder, file)
    split_wav.multiple_split(min_per_split=12)
    openaiapi = OpenaiAPI(folder, file, split_wav.split_files,'en')
    openaiapi.call()
