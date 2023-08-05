from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, CreateView
from django.core.files.storage import FileSystemStorage
from django.urls import reverse_lazy

from .forms import BookForm
from .models import Book
from .speech2text import SplitWavAudioMubin, OpenaiAPI
import smtplib
from email.mime.text import MIMEText

class Home(TemplateView):
    template_name = 'home.html'



def send_email(subject, body, sender, recipients, password):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
       smtp_server.login(sender, password)
       smtp_server.sendmail(sender, recipients, msg.as_string())
    print("Message sent!")




def upload(request):
    context = {}
    if request.method == 'POST':
        uploaded_file = request.FILES['document']
        language = request.POST['language']
        if language is None or language == '' or language not in ('zh', 'en'):
            language = 'en'
        fs = FileSystemStorage()
        name = fs.save(uploaded_file.name, uploaded_file)
        split_wav = SplitWavAudioMubin('./media', uploaded_file.name)
        split_wav.multiple_split(min_per_split=5)
        openaiapi = OpenaiAPI('./media', uploaded_file.name, split_wav.split_files,  language)
        openaiapi.call()
        subject = f'[Speech2Text] {uploaded_file.name}'
        body = "\n\n\n".join(openaiapi.texts)
        sender = "yadong.liu18@gmail.com"
        recipients = ["yadong.liu18@gmail.com",'liyaning@sph.com.sg']
        #recipients = ["yadong.liu18@gmail.com"]
        password = "srbddcoceoupijnj"
        send_email(subject, body, sender, recipients, password)
        context['url'] = fs.url(name)
    return render(request, 'home.html', context)


def book_list(request):
    books = Book.objects.all()
    return render(request, 'book_list.html', {
        'books': books
    })


def upload_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('book_list')
    else:
        form = BookForm()
    return render(request, 'upload_book.html', {
        'form': form
    })


def delete_book(request, pk):
    if request.method == 'POST':
        book = Book.objects.get(pk=pk)
        book.delete()
    return redirect('book_list')


