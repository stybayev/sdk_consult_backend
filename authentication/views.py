from random import randint

from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import AUTH_HEADER_TYPES
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from .exceptions import IncorrectPhoneVerificationCodeException, SmsSendingError, InvalidTokenAPIException
from authentication import serializers
import environ
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponsePermanentRedirect, FileResponse, HttpResponse
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import smart_str, smart_bytes
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from authentication import messages
from .models import User
from authentication import services
from .services import get_user_data, get_user, send_code_email
from .utils import Util

env = environ.Env()
environ.Env.read_env()


class CustomRedirect(HttpResponsePermanentRedirect):
    allowed_schemes = [env('APP_SCHEME'), 'http', 'https']


class RegisterView(generics.GenericAPIView):
    serializer_class = serializers.RegistrationSerializer

    @staticmethod
    def get_access_token(serializer):
        tokens = serializer.data.get('tokens', None)
        token = tokens.get('access', None)
        return token

    def post(self, request):
        user = request.data
        serializer = self.serializer_class(data=user)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        user_data = get_user_data(serializer)
        user = get_user(user_data)

        email_verification_code = str(randint(1000, 9999))
        user.email_verification_code = email_verification_code
        user.save()

        send_code_email(user=user, code=email_verification_code)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LoginAPIView(generics.GenericAPIView):
    serializer_class = serializers.LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = get_user_model().objects.get(email=serializer.data.get('email', None))
        return Response(serializer.data, status=status.HTTP_200_OK)


class VerifyEmailView(generics.GenericAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = serializers.EmailVerificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):  # noqa
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email_verification_code = serializer.data.get('email_verification_code', None)
        user = request.user
        services.email_already_confirmed(user=user)

        if not user.email_verified and (
                email_verification_code == user.email_verification_code):
            user.email_verified = True
            phone_verification_code = services.get_phone_verification_code()

            services.set_phone_verification_code(
                user=user,
                phone_verification_code=phone_verification_code
            )

            return Response(
                {'email': f'{messages.SUCCESSFULLY_ACTIVATED_EMAIL} {user.email}'},
                status=status.HTTP_200_OK)

        elif not user.email_verified and (
                email_verification_code != user.email_verification_code):
            return Response(
                {'error': f'{messages.INCORRECT_EMAIL}'},
                status=status.HTTP_400_BAD_REQUEST)


class LogoutAPIView(generics.GenericAPIView):
    serializer_class = serializers.LogoutSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status.HTTP_204_NO_CONTENT)


class ResendVerificationEmailView(generics.GenericAPIView):
    serializer_class = serializers.ResendVerificationEmailSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializers = self.serializer_class(data=request.data)
        serializers.is_valid(raise_exception=True)
        user = get_user_model().objects.filter(email=request.data.get('email', None)).first()

        if not user:
            return Response({'success': False,
                             'message': f'{messages.USER_EMAIL_NOT_EXISTS}'},
                            status=status.HTTP_400_BAD_REQUEST)

        if user.email_verified:
            return Response({'success': False,
                             'message': f'{messages.EMAIL_VERIFIED}'},
                            status=status.HTTP_400_BAD_REQUEST)

        email_verification_code = services.get_email_verification_code()
        services.set_email_verification_code(
            user=user,
            email_verification_code=email_verification_code)
        services.SendCodeEmailRegister.send_code_email_register(
            user=user,
            code=email_verification_code)

        return Response(
            {'success': True, 'message': f'{messages.CODE_SUCCESSFUL_EMAIL_SENDING}'},
            status=status.HTTP_200_OK)


class UserDetailView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.UserDetailSerializer

    def get(self, request):
        user = request.user
        serializer = self.serializer_class(user, context={'sms_sending_service': 'asdf'})
        return Response(serializer.data, status.HTTP_200_OK)


class ChangePasswordView(generics.UpdateAPIView):
    queryset = get_user_model().objects.all()
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.UpdatePasswordSerializer
    http_method_names = ["patch", ]

    @staticmethod
    def get_old_password(request):
        old_password = request.data.get('old_password')
        return old_password

    @staticmethod
    def get_new_password(request):
        new_password = request.data.get('new_password')
        return new_password

    @staticmethod
    def password_status(user, password):
        return user.check_password(password)

    def patch(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user

        old_password = self.get_old_password(request)
        new_password = self.get_new_password(request)

        old_password_status = self.password_status(user=user, password=old_password)

        if old_password_status:
            user.set_password(new_password)
            user.save()
            services.SendCodeEmailPasswordChange.send_message_email_password_change(user=user)
            return Response(
                {'success': True, 'message': f'{messages.PASSWORD_RESET_SUCCESS}'},
                status=status.HTTP_200_OK)

        return Response({'old_password': {'status_code': 400,
                                          'details': f'{messages.OLD_PASSWORD_NOT_CORRECT}'}},
                        status=status.HTTP_400_BAD_REQUEST)


class UpdateProfileView(generics.UpdateAPIView):
    queryset = get_user_model().objects.all()
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.UpdateProfileSerializer
    http_method_names = ["patch", ]

    @staticmethod
    def update_fields_user(user, request):
        user.first_name = request.data.get('first_name')
        user.last_name = request.data.get('last_name')
        user.save()

    def patch(self, request, *args, **kwargs):
        self.serializer_class(data=request.data)
        user = request.user

        self.update_fields_user(user=user, request=request)
        user.save()

        return Response(
            {'success': True, 'message': f'{messages.UPDATE_SUCCESS}'},
            status=status.HTTP_200_OK)


class UpdateUserPhoneNumberView(generics.UpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.UpdateUserPhoneNumberSerializer
    http_method_names = ["post", ]

    def post(self, request):  # noqa

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        phone_number = services.get_phone_number(request)
        services.set_phone_change(user=user,
                                  phone_number=phone_number)
        user.save()
        response = {'success': True,
                    'message': f'Смена телефона выполнена успешно!'}
        return Response(response, status=status.HTTP_200_OK)


class RequestPasswordResetEmailView(generics.GenericAPIView):
    serializer_class = serializers.RequestPasswordResetEmailSerializer

    @staticmethod
    def get_current_site(request, redirect_url):
        if redirect_url:
            current_site = redirect_url
        else:
            current_site = get_current_site(request=request).domain
        return current_site

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = request.data.get('email', None)

        if get_user_model().objects.filter(email=email).exists():
            user = get_user_model().objects.get(email=email)
            uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            redirect_url = request.data.get('redirect_url', None)
            current_site = self.get_current_site(request=request, redirect_url=redirect_url)

            services.SendCodeEmailPasswordReset.send_code_email_password_reset(
                token=token, user=user, current_site=current_site, uidb64=uidb64)

            return Response(
                {'success': f'{messages.TEXT_LINK_RESET_PASSWORD}'},
                status=status.HTTP_200_OK)

        return Response({'error': f'{messages.TEXT_EMAIL_NOT_FOUND}'},
                        status=status.HTTP_404_NOT_FOUND)


class PasswordTokenCheckView(generics.GenericAPIView):
    serializer_class = serializers.PasswordTokenCheckSerializer

    @staticmethod
    def get_user(uidb64):  # noqa
        try:
            user_id = smart_str(urlsafe_base64_decode(uidb64))
            user = get_user_model().objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'success': False,
                             'message': f'{messages.USER_NOT_EXISTS_OR_DATA_INVALID}'},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_type = type(e).__name__
            return Response(
                {'success': False, 'message': f"{error_type}\n{e}"},
                status=status.HTTP_400_BAD_REQUEST)
        return user

    def get(self, request, *args, **kwargs):  # noqa
        try:
            uidb64 = self.kwargs.get('uidb64', None)
            user = self.get_user(uidb64)
            token = self.kwargs.get('token', None)

            if PasswordResetTokenGenerator().check_token(user, token):
                return Response(
                    {'success': True,
                     'message': f'{messages.SUCCESS_TOKEN_AND_UID}'},
                    status=status.HTTP_200_OK)
            return Response(
                {'success': False, 'message': f'{messages.ERROR_TOKEN_AND_UID}'},
                status=status.HTTP_400_BAD_REQUEST)
        except AttributeError:
            return Response(
                {'success': False, 'message': f'{messages.ERROR_TOKEN_AND_UID}'},
                status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_type = type(e).__name__
            return Response(
                {'success': False,
                 'message': f"{error_type}\n{e}"},
                status=status.HTTP_400_BAD_REQUEST)


class SetNewPasswordView(generics.UpdateAPIView):
    serializer_class = serializers.SetNewPasswordSerializer
    http_method_names = ["patch", ]

    @staticmethod
    def get_user(request):
        uidb64 = request.data.get('uidb64', None)
        user_id = smart_str(urlsafe_base64_decode(uidb64))
        user = get_user_model().objects.get(id=user_id)
        return user

    def patch(self, request, *args, **kwargs):  # noqa
        try:
            user = self.get_user(request)

            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)

            services.SendCodeEmailPasswordChange.send_message_email_password_change(user=user)
            return Response({'success': True, 'message': f'{messages.PASSWORD_RESET_SUCCESS}'},
                            status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'success': False, 'message': f'{messages.USER_NOT_EXISTS}'},
                            status=status.HTTP_400_BAD_REQUEST)
        except AuthenticationFailed:
            return Response({'success': False, 'message': f'{messages.TEXT_LINK_RESET_INVALID}'},
                            status=status.HTTP_400_BAD_REQUEST)
        except ValidationError:
            return Response(
                {'success': False,
                 'message': f'{messages.TEXT_SIX_CHARACTERS}'},
                status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_type = type(e).__name__
            return Response(
                {'success': False, 'message': f"{error_type}\n{e}"},
                status=status.HTTP_400_BAD_REQUEST)


class CheckEmailForUniquenessView(generics.GenericAPIView):
    serializer_class = serializers.CheckEmailForUniquenessSerializer
    http_method_names = ["post", ]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.data.get('email', None)

        if get_user_model().objects.filter(email=email).exists():
            return Response({'success': f'{messages.USER_EMAIL_EXISTS}'},
                            status=status.HTTP_200_OK)
        return Response({'error': f'{messages.USER_EMAIL_NOT_EXISTS}'},
                        status=status.HTTP_404_NOT_FOUND)


class AddingImageUser(generics.GenericAPIView):
    serializer_class = serializers.AddingImageUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser,)

    @swagger_auto_schema(operation_description='Upload file...', )
    @action(detail=False, methods=['post'])
    def post(self, request):
        serializer = self.serializer_class(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'success': f'{messages.TEXT_SUCCESSFUL_AVATAR_CHANGE}'},
                        status=status.HTTP_200_OK)



class RefreshTokenView(generics.GenericAPIView):
    permission_classes = ()
    authentication_classes = ()
    serializer_class = TokenRefreshSerializer
    www_authenticate_realm = 'api'

    def get_authenticate_header(self, request):
        return '{0} realm="{1}"'.format(
            AUTH_HEADER_TYPES[0],
            self.www_authenticate_realm,
        )

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError:
            raise InvalidTokenAPIException()

        return Response(serializer.validated_data, status=status.HTTP_200_OK)
