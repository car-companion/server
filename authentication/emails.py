from django.conf import settings
from django.template.loader import render_to_string
from djoser.email import ActivationEmail

class CustomActivationEmail(ActivationEmail):
    template_name='emails/activation.html'

    def get_subject(self):
        # Custom subject line for the activation email
        return "Activate Your Account - Car Companion"

    def render(self):
        context = self.get_context_data()
        rendered_body = render_to_string(self.template_name, context)
        self.body = rendered_body
