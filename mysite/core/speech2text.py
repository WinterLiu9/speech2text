import openai
import pydub.playback
from pydub import AudioSegment
import math
import smtplib
from email.mime.text import MIMEText
import logging
import platform
import concurrent.futures
from mysite.core.util import _write_file, load_yaml_file


class SplitWavAudioMubin():
    def __init__(self, folder, filename):
        self.folder = folder
        self.filename = filename
        self.filepath = folder + '/' + filename
        system_info = platform.version()
        if system_info.find('Darwin Kernel') != -1:
            pydub.AudioSegment.converter = '/opt/homebrew/bin/ffmpeg'
        else:
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
            logging.info(str(i) + ' Done')
            if i == total_mins - min_per_split:
                logging.info('All splited successfully')

class OpenaiAPI():
    def __init__(self, folder, file, files, language, need_translation):
        config_file = load_yaml_file('./config/config.yaml')
        self.folder = folder
        self.file = file
        self.files = [open(folder + '/' + f, 'rb') for f in files]
        self.texts = []
        self.translated_texts = []
        self.api_key = config_file['api_token']
        self.language = language
        self.need_translation = need_translation
    
    def translate_text(self, text):
        prompt = f"Translate the following English text to Chinese: {text[1]}"

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that translates text."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=3000,
            n=1,
            stop=None,
            temperature=0.5,
        )

        translation = response.choices[0].message.content.strip()
        logging.info(translation)
        return text[0], translation

    def speech2text(self):
        openai.api_key = self.api_key
        texts = []  # Initialize an empty list for texts
        translated_texts = []  # Initialize an empty list for translated texts

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            translation_futures = []

            for i, file in enumerate(self.files):
                futures.append(
                    executor.submit(self.transcribe, (i, file))
                )

            # Wait for all the futures to complete
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result is not None:
                    texts.append(result)
                    if self.language == 'en' and self.need_translation:
                        translation_futures.append(
                            executor.submit(self.translate_text, result)
                        )

            for future in concurrent.futures.as_completed(translation_futures):
                translation_result = future.result()
                if translation_result is not None:
                    translated_texts.append(translation_result)

            def sort_key(obj):
                return obj[0]
            self.texts = [obj[1] for obj in sorted(texts, key=sort_key)]
            self.translated_texts = [obj[1] for obj in sorted(translated_texts, key=sort_key)]
            self.save_file()

    def save_file(self):
        _write_file(
            self.folder + '/' + self.file.replace('.mp3', '.txt').replace('.m4a', '.txt').replace('.ogg', '.txt'),
            "\n\n\n".join(self.texts))
        if self.language == 'en' and self.need_translation:
            _write_file(
                self.folder + '/' + self.file.replace('.mp3', '_en_to_zh.txt').replace('.m4a', '_en_to_zh.txt').replace(
                    '.ogg', '_en_to_zh.txt'), "\n\n\n".join(self.translated_texts))

    def transcribe(self, file):
        transcript = openai.Audio.transcribe("whisper-1", file[1], language=self.language)
        td = transcript.to_dict()
        logging.info(td)
        return (file[0], td.get('text'))