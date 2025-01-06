from djoser.email import ActivationEmail as DjoserActivationEmail
from djoser.email import (
    PasswordResetEmail as DjoserPasswordResetEmail,
    ConfirmationEmail as DjoserConfirmationEmail
)


class ActivationEmail(DjoserActivationEmail):
    template_name = 'emails/activation.html'


class PasswordResetEmail(DjoserPasswordResetEmail):
    template_name = "emails/password_reset.html"


class ConfirmationEmail(DjoserConfirmationEmail):
    template_name = "emails/confirmation.html"
