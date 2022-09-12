from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView
from .exceptions import IncorrectPhoneVerificationCodeException, SmsSendingError
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
        return Response(serializer.data, status=status.HTTP_201_CREATED)


"""
Вьюха авторизации. Вся логика проходит в сериалайзере.
При авторизации вводится только емайл и пароль пользователя.
Пользователь может авторизоваться не подтверждая емайл и номер телефона.
После успешной авторизации
возвращаются емайл пользователя, которые вводилась при регитрации и поля пользователя
с инфомацией о подтверждении емайла и номера телефона (true or false).
Также возвращается jwt-токен для авторизации пользователя.
При каждой авторизации пользователя определяются его личные данные (Ip, геолокации итд)
и записываются в модель Login.
"""


class LoginAPIView(generics.GenericAPIView):
    serializer_class = serializers.LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = get_user_model().objects.get(email=serializer.data.get('email', None))
        Login.objects.create(**services.get_user_personal_data(user=user, request=request))
        return Response(serializer.data, status=status.HTTP_200_OK)


"""
Вьюха для подтверждения адреса электронной почты.
Есть get запрос который принимает из фронта access токен
пользователя и 4-значный код из письма подтверждения емаила.
Токен дешифруется и из него
выводится user_id. Ищется пользователь по id. Если поиск пользователя проходит успешно и
код подтверждения введен корректно
(то есть производится сверка введенного кода пользователем и кода из пользователя
email_verification_code), то у пользователя меняется свойство
email_verified со значения False (заданное по умолчанию при
создании) на значение True.
"""


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

            if not SystemSettings.objects.get(title='rubilnik_sms').activ:
                services.send_code_phone(user=user, code=phone_verification_code)

            return Response(
                {'email': f'{messages.SUCCESSFULLY_ACTIVATED_EMAIL} {user.email}'},
                status=status.HTTP_200_OK)

        elif not user.email_verified and (
                email_verification_code != user.email_verification_code):
            return Response(
                {'error': f'{messages.INCORRECT_EMAIL}'},
                status=status.HTTP_400_BAD_REQUEST)


"""
Вьюха для подтверждения номера телефона. Есть get запрос который принимает из фронта access токен
пользователя и 4-значный код для подтверждения номера телефона. Токен дешифруется и из него
выводится user_id. Ищется пользователь по id. Если поиск пользователя проходит успешно и
код подтверждения введен корректно (то есть производится сверка введенного кода пользователем
и кода из пользователя phone_verification_code), то у пользователя меняется свойство
phone_verified со значения False (заданное по умолчанию при
создании) на значение True.
"""


class VerifyPhoneView(generics.GenericAPIView):
    queryset = get_user_model().objects.all()
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.PhoneVerificationSerializer

    def post(self, request, *args, **kwargs):  # noqa
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = request.user
            phone_verification_code = serializer.data.get('phone_verification_code', None)

            if not user.phone_verified and (
                    phone_verification_code == user.phone_verification_code):
                user.phone_verified = True
                user.phone_resend_time = 0
                user.save()

            elif not user.phone_verified and \
                    (phone_verification_code != user.phone_verification_code):
                raise IncorrectPhoneVerificationCodeException('Incorrect code')
            return Response(
                {'phone': f'{messages.MOBILE_VERIFY_SUCCESS} {user.phone_number}'},
                status=status.HTTP_200_OK)
        except IncorrectPhoneVerificationCodeException:
            return Response(
                {'error': f'{messages.INCORRECT_PHONE}'},
                status=status.HTTP_400_BAD_REQUEST)
        except Exception as message:
            error_type = type(message).__name__
            return Response(
                {'error': False,
                 'error_type': f'{error_type}',
                 'message': f"{message}"},
                status=status.HTTP_400_BAD_REQUEST)


"""
Вьюха для логаута.
Вся логика описана в сериалайзере. Со стороны фронта принимает только
refresh токен пользователя и в логике сериалайзера отправляется в blacklist.
"""


class LogoutAPIView(generics.GenericAPIView):
    serializer_class = serializers.LogoutSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status.HTTP_204_NO_CONTENT)


"""
Вьюха для повторной отправки 4-значного кода для подтверждения емайла.
Есть пост запрос который принимает данные
со стороны фронта для обработки (емайл пользователя).
При этом пользователь должен быть авторизованным в системе.
Данные передаются сериалайзеру где и ищется пользователь.
Затем напочту пользователя повторно отправляется 4-значный код подтверждения емайла.
В случае успеха возвращается статус HTTP_200_OK,
что означает об отправке кода на почту пользователя.
"""


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


"""
Вьюха для повторной отправки 4-значного кода для подтверждения номера телефона.
Есть пост запрос который принимает данные
со стороны фронта для обработки (номер телефона пользователя).
При этом пользователь должен быть авторизованным в системе.
Данные передаются сериалайзеру где и ищется пользователь. Затем на указанный номер телефона
пользователя повторно отправляется 4-значный код для подтверждения номера. В случае успеха
возвращается статус HTTP_200_OK, что означает о повторной отправке кода на номер пользователя.
"""


class ResendVerificationPhoneView(generics.GenericAPIView):
    serializer_class = serializers.ResendVerificationPhoneSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):  # noqa
        try:
            serializers = self.serializer_class(data=request.data)
            serializers.is_valid(raise_exception=True)

            user = request.user

            services.set_phone_country(
                user=user,
                country_iso_code=request.data.get('country_iso_code', None).upper())

            phone_verification_code = services.get_phone_verification_code()
            services.set_phone_verification_code(user=user,
                                                 phone_verification_code=phone_verification_code)
            user.save()

            response = services.phone_country_check(
                user=user,
                phone_verification_code=phone_verification_code)

            return Response(response, status=status.HTTP_200_OK)

        except Country.DoesNotExist:
            return Response({'success': False,
                             'message': f'{messages.TEXT_COUNTRY_NOT_EXISTS}'},
                            status=status.HTTP_400_BAD_REQUEST)
        except RegularExpressionPhoneNumber.DoesNotExist:
            return Response({'success': False,
                             'message': f'{messages.TEXT_COUNTRY_NOT_EXISTS}'},
                            status=status.HTTP_400_BAD_REQUEST)
        except SmsSendingError as message:
            return Response(
                {'error': {'success': False,
                           'status_code': status.HTTP_400_BAD_REQUEST,
                           'message': f'{message.args[0]}'},
                 },
                status=status.HTTP_400_BAD_REQUEST)


"""
Вьюха для получения подробной информации о текущем пользователе.
Вся логика описана в сериалайзере. Выводяся поля из модели пользователя.
"""


class UserDetailView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.UserDetailSerializer

    def get(self, request):
        user = request.user
        serializer = self.serializer_class(user, context={'sms_sending_service': 'asdf'})
        return Response(serializer.data, status.HTTP_200_OK)


"""
Вьюха для изменения пароля пользователя из личного кабинета.
Принимается текущий пароль и новый пароль. Если текущий пароль проходит проверку то новый
пароль применяется как основной.
"""


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
            services.send_message_phone_password_change(user=user)
            return Response(
                {'success': True, 'message': f'{messages.PASSWORD_RESET_SUCCESS}'},
                status=status.HTTP_200_OK)

        return Response({'old_password': {'status_code': 400,
                                          'details': f'{messages.OLD_PASSWORD_NOT_CORRECT}'}},
                        status=status.HTTP_400_BAD_REQUEST)


"""
Вьюха для изменения данных пользователя из личного кабинета.
Принимаются новые данные и сохраняются в модели пользователя.
"""


class UpdateProfileView(generics.UpdateAPIView):
    queryset = get_user_model().objects.all()
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.UpdateProfileSerializer
    http_method_names = ["patch", ]

    @staticmethod
    def update_fields_user(user, request):
        user.profile_filled = request.data.get('profile_filled')
        user.first_name_cyrillic = request.data.get('first_name_cyrillic')
        user.last_name_cyrillic = request.data.get('last_name_cyrillic')
        user.first_name_latin = request.data.get('first_name_latin')
        user.last_name_latin = request.data.get('last_name_latin')
        user.patronymic = request.data.get('patronymic')
        user.iin_number = request.data.get('iin_number')
        user.country_of_residence = request.data.get('country_of_residence')
        user.city_of_residence = request.data.get('city_of_residence')
        user.postcode = request.data.get('postcode')
        user.address_of_residence = request.data.get('address_of_residence')
        user.citizenship_country = request.data.get('citizenship_country')
        user.verification_document_number = request.data.get('verification_document_number')
        user.verification_document_expires_date = request.data.get(
            'verification_document_expires_date')
        user.verification_document = request.data.get('verification_document')
        user.save()

    def patch(self, request, *args, **kwargs):
        self.serializer_class(data=request.data)
        user = request.user

        self.update_fields_user(user=user, request=request)

        return Response(
            {'success': True, 'message': f'{messages.UPDATE_SUCCESS}'},
            status=status.HTTP_200_OK)


"""
Вьюха для изменения номера телефона пользователя из личного кабинета.
Принимает только номер телефона. Как только на апи приходит запрос
о верификации телефона пользователя
в поле phone_verification_code записывается случайное четырехзначное число.
Это четырехзначное число отправляется в SMS для подтверждения номера телефона.
"""


class UpdateUserPhoneNumberView(generics.UpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.UpdateUserPhoneNumberSerializer
    http_method_names = ["post", ]

    def post(self, request):  # noqa

        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)

            user = request.user
            phone_number = services.get_phone_number(request)
            phone_verification_code = services.get_phone_verification_code()

            services.set_phone_country(
                user=user,
                country_iso_code=request.data.get('country_iso_code', None))
            services.set_phone_change(user=user,
                                      phone_number=phone_number)
            services.set_phone_verification_code(user=user,
                                                 phone_verification_code=phone_verification_code)
            user.save()
            response = services.phone_country_check_phone_update(
                user=user,
                phone_verification_code=phone_verification_code)

            return Response(response, status=status.HTTP_200_OK)

        except Country.DoesNotExist:
            return Response({'success': False,
                             'message': f'{messages.TEXT_COUNTRY_NOT_EXISTS}'},
                            status=status.HTTP_400_BAD_REQUEST)

        except RegularExpressionPhoneNumber.DoesNotExist:
            return Response({'success': False,
                             'message': f'{messages.TEXT_COUNTRY_NOT_EXISTS}'},
                            status=status.HTTP_400_BAD_REQUEST)

        except SmsSendingError as message:
            return Response(
                {'error': {'success': False,
                           'status_code': status.HTTP_400_BAD_REQUEST,
                           'message': f'{message.args[0]}'},
                 },
                status=status.HTTP_400_BAD_REQUEST)


class VerifyPhoneChangeView(generics.GenericAPIView):
    queryset = get_user_model().objects.all()
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.PhoneVerificationSerializer

    def post(self, request, *args, **kwargs):  # noqa
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = request.user
            phone_verification_code = serializer.data.get('phone_verification_code', None)

            if phone_verification_code == user.phone_verification_code:
                user.phone_number = user.phone_change
                user.save()
                user.phone_verified = True
                user.phone_resend_time = 0
                user.save()
            elif phone_verification_code != user.phone_verification_code:
                raise IncorrectPhoneVerificationCodeException('Неверный код')
            return Response(
                {'phone': f'{messages.MOBILE_VERIFY_SUCCESS} {user.phone_number}'},
                status=status.HTTP_200_OK)
        except IncorrectPhoneVerificationCodeException:
            return Response(
                {'error': f'{messages.INCORRECT_PHONE}'},
                status=status.HTTP_400_BAD_REQUEST)
        except Exception as message:
            error_type = type(message).__name__
            return Response(
                {'error': False,
                 'error_type': f'{error_type}',
                 'message': f"{message}"},
                status=status.HTTP_400_BAD_REQUEST)


"""
Вьюха для запроса на восстановление пароля.
Пост запрос принимает почту. На основе почты ищется пользователь. На основе его данных
формируется токен и uid код. Затем все это отправляется пользователю на указанную почту.
"""


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


"""
На этой вьюхе и проходит проверка корректности uid кода и токена. Если все хорошо то
возвращается статус 200, в противном случае 400
"""


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


"""
Вьюха для создания нового пароля при сбросе старого. Вся логика описана в сериалайзере
"""


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


"""
Представление для выдачи конфигурационных настороек для andriod и ios платформ (deep limking)
"""


class SendDeepLinkFileView(APIView):
    def get(self, request, filename):
        if 'json' not in filename:
            response = HttpResponse(
                open(f'static/json/{filename}', 'rb'),
                content_type='text/plain; charset=UTF-8')
            return response
        response = FileResponse(open(f'static/json/{filename}', 'rb'))
        return response


"""
Представление для проверки почты в БД
"""


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


'''
Представление добавления аватарки для пользователя
'''


class AddingImageUser(generics.GenericAPIView):
    serializer_class = serializers.AddingImageUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser,)

    @swagger_auto_schema(operation_description='Upload file...', )
    @action(detail=False, methods=['post'])
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response({'success': f'{messages.TEXT_SUCCESSFUL_AVATAR_CHANGE}'},
                        status=status.HTTP_200_OK)
