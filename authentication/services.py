from random import randint
import requests
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import serializers
from authentication.utils import Util
from authentication import messages
from datetime import datetime


def get_email_verification_code():
    code = str(randint(1000, 9999))
    return code


def set_email_verification_code(user, email_verification_code):
    user.email_verification_code = email_verification_code
    user.save()


def get_phone_verification_code():
    code = str(randint(1000, 9999))
    return code


def set_phone_verification_code(user, phone_verification_code):
    user.phone_verification_code = phone_verification_code
    user.save()


def get_user_data(serializer):
    user_data = serializer.data
    return user_data


def get_user(user_data):
    user = get_user_model().objects.get(email=user_data.get('email', None))
    return user


def validate_phone_number(phone_number):  # noqa
    if phone_number:
        q_1 = Q(phone_verified=True)
        if str(phone_number)[0] == '+':
            q_2 = Q(phone_number__endswith=str(phone_number)[2:])
            user = get_user_model().objects.filter(q_2 & q_1)

        else:
            q_2 = Q(phone_number__endswith=str(phone_number)[1:])
            user = get_user_model().objects.filter(q_2 & q_1)

        if user:
            raise serializers.ValidationError(f'{messages.USER_PHONE_EXISTS}')
        return user


def validate_phone_number_resend_phone_verify(phone_number):  # noqa
    if phone_number:
        if str(phone_number)[0] == '+':
            user = get_user_model().objects.filter(
                phone_number__endswith=str(phone_number)[2:])
        else:
            user = get_user_model().objects.filter(
                phone_number__endswith=str(phone_number)[1:])
        if not user:
            raise serializers.ValidationError(messages.USER_PHONE_NOT_EXISTS)

        user = get_user_model().objects.filter(phone_number__endswith=str(phone_number)[2:]).last()

        if user.phone_verified:
            raise serializers.ValidationError(messages.PHONE_VERIFIED)
        return user


def set_phone_change(phone_number, user):
    user.phone_change = phone_number


def get_phone_number(request):
    phone_number = request.data.get('phone_number')
    return phone_number


def email_already_confirmed(user):
    if user.email_verified:
        raise serializers.ValidationError(f'{messages.EMAIL_VERIFIED}')


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_personal_data(user, request):
    get_user_locations = requests.get(f'http://ipwho.is/{get_client_ip(request)}')
    user_personal_data = {
        'user': user,
        'ip_address': get_client_ip(request),
        'user_locations': f"Country-{get_user_locations.json().get('country', None)}/"
                          f"City-{get_user_locations.json().get('city', None)}",
        'last_visit': datetime.now(),
        'operating_system_language': request.LANGUAGE_CODE,
        'operating_system': f'family-{request.user_agent.os.family}/'
                            f'version-{request.user_agent.os.version_string}',
        'device_name': f'family-{request.user_agent.device.family}/'
                       f'brand-{request.user_agent.device.brand}/'
                       f'model-{request.user_agent.device.model}'
    }

    return user_personal_data


class SendCodeEmailPasswordChange:
    @staticmethod
    def server_send_message_email_password_change(user):
        email_body = f'{messages.TEXT_PASSWORD_SUCCESS_CHANGE}'

        data = {'email_body': email_body,
                'to_email': user.email,
                'email_subject': 'Изменение пароля'}
        Util.send_email(data)

    @staticmethod
    def send_message_email_password_change(user):  # noqa
        SendCodeEmailPasswordChange.server_send_message_email_password_change(user)


class SendCodeEmailRegister:
    @staticmethod
    def server_send_code_email(user, code):
        email_body = f"Code confirmation - {code}"

        data = {'email_body': email_body,
                'to_email': user.email,
                'email_subject': messages.TEXT_CONFIRM_EMAIL}
        Util.send_email(data)

    @staticmethod
    def send_code_email_register(user, code):  # noqa
        SendCodeEmailRegister.server_send_code_email(user, code)


class SendCodeEmailPasswordReset:
    @staticmethod
    def server_send_code_email_password_reset(token, user, current_site, uidb64):
        absurl = f"{current_site}?uid={uidb64}&token={token}"
        email_body = f'Здраствуйте. \n' \
                     f'Воспользуйтесь ссылкой ниже, чтобы сбросить пароль {user.email}\n' \
                     f'{absurl}'
        data = {'email_body': email_body,
                'to_email': user.email,
                'email_subject': f'{messages.RESET_PASSWORD_EMAIL}'}
        Util.send_email(data)

    @staticmethod
    def send_code_email_password_reset(token, user, current_site, uidb64):  # noqa
        SendCodeEmailPasswordReset.server_send_code_email_password_reset(
            token, user, current_site, uidb64)
