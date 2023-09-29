from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.core.files.storage import FileSystemStorage
from mysite.core.email import GMailService

from mysite.core.util import is_valid_email, load_yaml_file

from .speech2text import SplitWavAudioMubin, OpenaiAPI

from django.http import JsonResponse

class Home(TemplateView):
    template_name = 'home.html'

def upload(request):
    context = {}
    if request.method == 'POST':
        need_translation = bool(int(request.POST['traslation']))
        token = request.POST['token']
        config_token = load_yaml_file("./config/config.yaml")['token']
        if token != config_token:
            context['url'] = 'Please enter the correct token.'
            return render(request, 'home.html', context)
        uploaded_file = request.FILES['document']
        language = request.POST['language']
        email = request.POST['email']
        if not is_valid_email(email):
            context['url'] = 'Please enter the correct email address.'
            return render(request, 'home.html', context)

        fs = FileSystemStorage()
        fs.save(uploaded_file.name, uploaded_file)

        # split into small file
        split_wav = SplitWavAudioMubin('./media', uploaded_file.name)
        split_wav.multiple_split(min_per_split=5)

        openai = OpenaiAPI('./media', uploaded_file.name, split_wav.split_files, language, need_translation)
        openai.speech2text()

        en_res = openai.texts
        zh_res = openai.translated_texts

        mail = GMailService([email], f'[Speech2Text] {uploaded_file.name}', en_res+zh_res)
        mail.send_email()

        context['url'] = 'You have successfully uploaded your file. Please check your email.'

    return render(request, 'home.html', context)




def upload_internal(request):
    if request.method == 'POST':
        need_translation = request.POST['traslation']
        uploaded_file_folder = request.POST['folder']
        uploaded_file_name = request.POST['file_name']
        language = request.POST['language']
        email = request.POST['email']

        # split into small file
        split_wav = SplitWavAudioMubin(uploaded_file_folder, uploaded_file_name)
        split_wav.multiple_split(min_per_split=5)

        openai = OpenaiAPI(uploaded_file_folder, uploaded_file_name, split_wav.split_files, language, need_translation)
        openai.speech2text()

        en_res = openai.texts
        zh_res = openai.translated_texts

        mail = GMailService([email], f'[Speech2Text] {uploaded_file_name}', en_res+zh_res)
        mail.send_email()
    response_data = {}
    response_data['result'] = 'success'
    response_data['message'] = 'success'
    return JsonResponse(response_data)
