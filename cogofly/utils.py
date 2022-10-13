from django.template.loader import render_to_string
from django.core.mail import EmailMessage

def send_mail(email, subject, template, context = None, attachements = None):
    if context is None:
        context = {}
    if attachements is not None:
        email = EmailMessage(subject, render_to_string(template, context), to=[email])
        email.content_subtype = 'html'
        email.attach_file(attachements)
        email.send()
    email = EmailMessage(subject, render_to_string(template, context), to=[email])
    email.content_subtype = 'html'
    email.send()