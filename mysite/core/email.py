import smtplib
from email.mime.text import MIMEText
import logging
from mysite.core.util import load_yaml_file


class GMailService():
    def __init__(self, recipients, subject, texts):
        config_file = load_yaml_file('./config/config.yaml')
        self.sender = 'yadong.liu18@gmail.com'
        recipients.append(self.sender)
        self.recipients = ', '.join(recipients)
        self.subject = subject
        self.content = '\n\n\n'.join(texts)
        self.password =  config_file['email_password']

    def send_email(self):
        msg = MIMEText(self.content)
        msg['Subject'] = self.subject
        msg['From'] = self.sender
        msg['To'] = self.recipients
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(self.sender, self.password)
            smtp_server.sendmail(self.sender, self.recipients, msg.as_string())
        logging.info("Message sent!")