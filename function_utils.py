import string
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email(subject, body, receiver_email):
    sender_email = "bagagemviagemcadastro@gmail.com"
    password = "byzd pasz ejdi rupp"

    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()

    server.login(sender_email, password)

    text = message.as_string()
    server.sendmail(sender_email, receiver_email, text)

    server.quit()


# Função para gerar uma senha aleatória
def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for i in range(length))
    return password
