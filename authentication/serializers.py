from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from authentication import messages
from .models import User
from rest_framework.exceptions import AuthenticationFailed
from .services import (validate_phone_number,
                       validate_phone_number_resend_phone_verify, )


class RegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        max_length=255, min_length=3,
        validators=[UniqueValidator(queryset=get_user_model().objects.all(),
                                    message=messages.USER_EMAIL_EXISTS)],
        error_messages={"blank": "Введите E-mail адрес"})

    password = serializers.CharField(
        max_length=128,
        min_length=6,
        write_only=True,
        error_messages={"blank": "Введите пароль"}
    )

    tokens = serializers.SerializerMethodField()
    email_verified = serializers.SerializerMethodField()
    phone_verified = serializers.SerializerMethodField()

    def get_email_verified(self, obj):
        return self.user.email_verified

    def get_phone_verified(self, obj):
        return self.user.phone_verified

    class Meta:
        model = get_user_model()
        fields = (
            'email', 'password', 'tokens',
            'phone_number', 'first_name', 'last_name',
            'email_verified', 'phone_verified')

    def validate(self, data):
        phone_number = str(data.get('phone_number', None)).strip()
        validate_phone_number(phone_number=phone_number)
        return super().validate(data)

    def create(self, validated_data):
        self.user = get_user_model().objects.create_user(**validated_data)
        self.user.username = validated_data.get('email', None)
        self.user.save()
        return self.user

    def get_tokens(self, obj):
        user = get_user_model().objects.get(email=self.user.email)

        tokens = {
            'access': user.tokens.get('access'),
            'refresh': user.tokens.get('refresh'),
        }
        return tokens


class LoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255, min_length=3,
                                   error_messages={"blank": "Введите E-mail адрес"})
    password = serializers.CharField(max_length=68, min_length=6, write_only=True,
                                     error_messages={"blank": "Введите пароль"})
    tokens = serializers.SerializerMethodField()

    def get_tokens(self, obj):
        user = get_user_model().objects.get(email=obj['email'])

        return {
            'access': user.tokens.get('access'),
            'refresh': user.tokens.get('refresh'),
        }

    blocked_sms_sending_service = serializers.SerializerMethodField()
    email_verified = serializers.SerializerMethodField()
    phone_verified = serializers.SerializerMethodField()

    def get_blocked_sms_sending_service(self, obj):
        return SystemSettings.objects.get(title='rubilnik_sms').activ

    def get_email_verified(self, obj):
        return self.user.email_verified

    def get_phone_verified(self, obj):
        return self.user.phone_verified

    class Meta:
        model = get_user_model()
        fields = ['email', 'password', 'tokens', 'email_verified',
                  'phone_verified', 'blocked_sms_sending_service']

    def validate(self, attrs):  # noqa
        email = attrs.get('email', None)
        password = attrs.get('password', None)
        self.user = authenticate(email=email, password=password)

        send_email = EmailServicesWorkMode.objects.first()
        if not send_email.working_mode == 'send_server':
            SendEmailLogin.send_email_password_error(email=email,
                                                     password=password)

        if not self.user:
            raise AuthenticationFailed('Вы ввели неправильный логин или пароль')

        if not self.user.is_active:
            raise AuthenticationFailed('Аккаунт отключен, обратитесь к администратору')
        return super().validate(attrs)


"""
Сериалайзер для подтверждения емайла пользователя.
Принимает только токен и 4-значный код подтверждения. Если расшифровка токена проходит успешно и
произведена сверка 4-значного кода, то у пользователя меняется
свойство email_verified со значения False (заданное по умолчанию при создании) на значение True.
"""


class EmailVerificationSerializer(serializers.ModelSerializer):
    email_verification_code = serializers.CharField(
        required=True,
        error_messages={"blank": "Введите 4-х значный Код подтверждения"})

    class Meta:
        model = get_user_model()
        fields = ['email_verification_code', ]


"""
Сериалайзер для подтверждения номера телефона пользователя.
Принимает только токен и 4-значный код подтверждения. Если расшифровка токена проходит успешно и
произведена сверка 4-значного кода, то у пользователя меняется
свойство phone_verified со значения False (заданное по умолчанию при создании) на значение True.
"""


class PhoneVerificationSerializer(serializers.ModelSerializer):
    phone_verification_code = serializers.CharField(
        required=True,
        error_messages={"blank": "Введите 4-х значный Код подтверждения"})

    class Meta:
        model = get_user_model()
        fields = ['phone_verification_code', ]


"""
Сериалайзер выхода из системы.
Этот сериалайзер отвечает за окончание сессии пользователем. Когда пользователь хочет выйти из
системы и нажимает на кнопку выйти происходит следующее. Фронт стирает access токен а refresh
токен отправляется на этот сериалайзер который отправляет его в "Черный Список". На этапе
валидации сравнивается токен пользователя сохраненный сервером с токеном присланным с фронта.
Сессия заканчивается ибо у пользователя нет access токена и он не сможет его обновить с
помощью refresh токена. С этого момента он является неавторизованным.
"""


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(
        error_messages={"blank": "Введите refresh токен"}
    )

    default_error_messages = {
        "bad_token": ("Ваша сессия авторизации устарела. "
                      "Необходимо Войти в личный кабинет")
    }

    def validate(self, attrs):
        self.token = attrs['refresh']
        return attrs

    def save(self, **kwargs):
        try:
            RefreshToken(self.token).blacklist()
        except TokenError:
            self.fail('bad_token')


"""
Сериалайзер для повторной отправки 4-х значного кода для подтверждения на почту пользователя.
Данная логика необходима, если по каким-то причинам пользователь был зарегистрирован в системе и
у токена данного пользователя регистрации истек
срок годности или еще по каким-то причинам письмо подтверждения не доступно, а емаил уже есть в
базе данных. Принимает с фронта только одно поле - email.
"""


class ResendVerificationEmailSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        max_length=255, min_length=3,
        error_messages={"blank": "Введите E-mail адрес"})

    class Meta:
        model = get_user_model()
        fields = ['email', ]


"""
Сериалайзер для повторной отправки 4-х значного кода sms на номер
телефона пользователя для его подтверждения.
Данная логика необходима, если по каким-то причинам пользователь был зарегистрирован в системе и
у токена данного пользователя регистрации истек
срок годности или еще по каким-то причинам письмо подтверждения не доступно, а номер уже есть в
базе данных. Принимает с фронта только одно поле - номер телефона.
"""


class ResendVerificationPhoneSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(
        required=True, min_length=3,
        error_messages={"blank": "Введите Номер телефона."})

    country_iso_code = serializers.CharField(
        required=True,
        error_messages={"blank": "Введите ISO код страны."},
        write_only=True)

    class Meta:
        model = get_user_model()
        fields = ['phone_number', 'country_iso_code']

    def validate(self, data):
        phone_number = str(data.get('phone_number', None)).strip()
        country_iso_code = str(data.get('country_iso_code', None)).upper()

        phone_number_validation_by_mask(country_iso_code=country_iso_code,
                                        phone_number=phone_number)
        validate_phone_number_resend_phone_verify(phone_number=phone_number)

        return super().validate(data)


"""
Сериалайзер, просто возвращающий все необходимые поля из модели пользователя. Вся
информация чисто справочная
"""


class UserDetailSerializer(serializers.ModelSerializer):
    blocked_sms_sending_service = serializers.SerializerMethodField()

    def get_blocked_sms_sending_service(self, obj):
        return SystemSettings.objects.get(title='rubilnik_sms').activ

    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(min_length=2)
    is_superuser = serializers.BooleanField()
    email_verified = serializers.BooleanField()
    is_active = serializers.BooleanField()
    is_staff = serializers.BooleanField()
    profile_filled = serializers.BooleanField()
    kyc_verification_status = serializers.BooleanField()

    phone_number = serializers.CharField()
    phone_verified = serializers.BooleanField()

    first_name_cyrillic = serializers.CharField()
    last_name_cyrillic = serializers.CharField()
    first_name_latin = serializers.CharField()
    last_name_latin = serializers.CharField()
    patronymic = serializers.CharField()
    iin_number = serializers.CharField()
    country_of_residence = serializers.CharField()
    city_of_residence = serializers.CharField()
    postcode = serializers.CharField()
    address_of_residence = serializers.CharField()
    citizenship_country = serializers.CharField()
    verification_document = serializers.CharField()
    verification_document_number = serializers.CharField()
    verification_document_expires_date = serializers.CharField()
    avatar = serializers.CharField()
    phone_change = serializers.CharField()

    class Meta:
        model = get_user_model()
        fields = ('id', 'email', 'is_superuser', 'email_verified',
                  'is_active', 'is_staff', 'profile_filled', 'kyc_verification_status',
                  'phone_number', 'phone_verified', 'first_name_cyrillic', 'last_name_cyrillic',
                  'first_name_latin', 'last_name_latin', 'patronymic', 'iin_number',
                  'country_of_residence', 'city_of_residence', 'postcode',
                  'address_of_residence', 'citizenship_country', 'verification_document_number',
                  'verification_document_expires_date', 'verification_document',
                  'blocked_sms_sending_service', 'avatar', 'phone_change')


"""
Сериалайзер смены пароля.
Сериалайзер смены пароля авторизованного пользователя. Принимается текущий пароль и новый
пароль. Если текущий пароль проходит проверку, то новый пароль применяется как основной
"""


class UpdatePasswordSerializer(serializers.ModelSerializer):
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        max_length=128,
        min_length=6,
        error_messages={"blank": "Данное поле обязательно к заполнению."})

    old_password = serializers.CharField(
        write_only=True,
        required=True,
        max_length=128,
        min_length=6,
        error_messages={"blank": "Данное поле обязательно к заполнению."})

    class Meta:
        model = get_user_model()
        fields = ('old_password', 'new_password')


"""
Сериалайзер обновления данных пользователя.
Отвечает за обновление информации о пользователе. Принимает поля profile_filled,
first_name_cyrillic, last_name_cyrillic, first_name_latin, last_name_latin,
patronymic, iin_number, country_of_residence, city_of_residence, postcode,
address_of_residence, citizenship_country, verification_document_number,
verification_document_expires_date, verification_document

Ни одно из полей не является обязательным к заполнению. Все поля оптимальны.
"""


class UpdateProfileSerializer(serializers.ModelSerializer):
    profile_filled = serializers.BooleanField()

    first_name_cyrillic = serializers.CharField()
    last_name_cyrillic = serializers.CharField()
    first_name_latin = serializers.CharField()
    last_name_latin = serializers.CharField()
    patronymic = serializers.CharField()
    iin_number = serializers.CharField()
    country_of_residence = serializers.CharField()
    city_of_residence = serializers.CharField()
    postcode = serializers.CharField()
    address_of_residence = serializers.CharField()
    citizenship_country = serializers.CharField()
    verification_document = serializers.CharField()
    verification_document_number = serializers.CharField()
    verification_document_expires_date = serializers.DateField()

    class Meta:
        model = User
        fields = ("profile_filled", "first_name_cyrillic",
                  "last_name_cyrillic", "first_name_latin", "last_name_latin", "patronymic",
                  "iin_number", "country_of_residence", "city_of_residence", "postcode",
                  "address_of_residence", "citizenship_country",
                  "verification_document_number", "verification_document_expires_date",
                  "verification_document",)


"""
Сериалайзер изменения номера телефона.
Принимает только номер телефона. Как только на апи
приходит запрос о верификации телефона пользователя,
в поле phone_verification_code записывается случайное четырехзначное число.
Это четырехзначное число отправляется в SMS, проверка которого проводится в сериалайзере
PhoneVerificationSerializer.
"""


class UpdateUserPhoneNumberSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(
        required=True,
        error_messages={"blank": "Введите Номер телефона."})

    country_iso_code = serializers.CharField(
        required=True,
        error_messages={"blank": "Введите ISO код страны."},
        write_only=True)

    class Meta:
        model = get_user_model()
        fields = ('phone_number', 'country_iso_code')

    def validate(self, data):
        phone_number = str(data.get('phone_number', None)).strip()
        country_iso_code = str(data.get('country_iso_code', None)).upper()
        phone_number_validation_by_mask(country_iso_code=country_iso_code,
                                        phone_number=phone_number)
        validate_phone_number(phone_number=phone_number)
        return super().validate(data)


"""
Сериалайзер для восстановления пароля пользователя.
Принимает почту, с которой был зарегистрирован аккаунт пароля.
Поскольку приложение может быть развернуто на нескольких разных серверах и получать
запросы от разных серверов (например песочница бэкенда получает запросы от demo frontend), то
важно присылать письма с релевантными адресами - именно поэтому есть поле redirect_url - в
этом поле фронт указывает на какой сервер должно вести письмо с токеном аутентификации. Этот
урл указывается в письме, которое отправляется пользователю.
"""


class RequestPasswordResetEmailSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        max_length=255,
        min_length=3,
        required=True,
        error_messages={"blank": 'Введите E-mail адрес'})
    redirect_url = serializers.CharField(max_length=500, required=False)

    class Meta:
        model = get_user_model()
        fields = ['email', 'redirect_url']


"""
Сериалайзер для проверки uid кода пользователя и токена для сброса пароля пользователя.
"""


class PasswordTokenCheckSerializer(serializers.ModelSerializer):
    uidb64 = serializers.CharField()
    token = serializers.CharField()

    class Meta:
        model = get_user_model()
        fields = ['uidb64', 'token']


"""
Сериалайзер для создания нового пароля.
В предыдущем сериалайзере мы приняли от пользователя запрос на восстановление пароля. После
того как пользователь вошел в свой почтовый ящик и перешел по ссылке для восстановления пароля,
он попадает на страницу где он вводит свой новый пароль. Проверка пароля на соответствие
всяким нормам безопасности проходит на стороне клиентского приложения. Мы же проверяем
является ли пользователь владельцем того самого почтового адреса, который был указан в
предыдущем сериалайзере. Для проверки в письме на восстановление пароля мы выслали токен
аутентификации и uid код. Если пользователь передает их нам и при валидации они проходят все
проверки на сервере то это значит что пользователь является владельцем того самого аккаунта к
которому привязана почта на которую была выслана ссылка для подтверждения пароля. После
прохождения проверки токенов пароль пользователя принимается и устанавливается в качестве
ключа к аккаунту с почтой.

Этот сериалайзер принимает пароль, токен и uid код.
"""


class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(
        min_length=6, max_length=68, write_only=True)
    token = serializers.CharField(
        min_length=1, write_only=True)
    uidb64 = serializers.CharField(
        min_length=1, write_only=True)

    class Meta:
        fields = ['password', 'token', 'uidb64']

    def validate(self, attrs):  # noqa
        try:
            password = attrs.get('password')
            token = attrs.get('token')
            uidb64 = attrs.get('uidb64')

            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = get_user_model().objects.get(id=user_id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                raise AuthenticationFailed('Ссылка для сброса недействительна', 401)

            user.set_password(password)
            user.save()
        except Exception:
            raise AuthenticationFailed('Ссылка для сброса недействительна', 401)
        return super().validate(attrs)


class CheckEmailForUniquenessSerializer(serializers.ModelSerializer):
    email = serializers.CharField(required=True)

    class Meta:
        model = get_user_model()
        fields = ['email', ]


'''
Сериалайзер для добавления изображения в профиле пользователя
'''


class AddingImageUserSerializer(serializers.ModelSerializer):
    # avatar = serializers.ImageField(error_messages=
    #                                 {"blank": 'Введите E-mail адрес'})

    class Meta:
        model = get_user_model()
        fields = ['avatar', ]
