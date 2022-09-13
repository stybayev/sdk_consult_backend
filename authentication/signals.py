from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from authentication import services, messages
from authentication.utils import Util


# @receiver(post_save, sender=get_user_model())
# def save_count_publications(created, **kwargs):
#     instance = kwargs['instance']
#     if created:
#         user = instance
#         email_verification_code = services.get_email_verification_code()
#         services.set_email_verification_code(
#             user=user,
#             email_verification_code=email_verification_code)
#
#         email_body = f"Code confirmation - {email_verification_code}"
#         data = {'email_body': email_body,
#                 'to_email': user.email,
#                 'email_subject': messages.TEXT_CONFIRM_EMAIL}
#         Util.send_email(data)

