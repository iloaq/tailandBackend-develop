from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from celery_app import app
import os


# Асинхронная отправка почты через селари

@shared_task()
def send_registration_email(email, password):
    send_mail(
        subject='пароль:',
        message=password,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=True
    )