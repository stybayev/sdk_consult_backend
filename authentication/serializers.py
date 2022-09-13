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

    email_verified = serializers.SerializerMethodField()
    phone_verified = serializers.SerializerMethodField()

    def get_email_verified(self, obj):
        return self.user.email_verified

    def get_phone_verified(self, obj):
        return self.user.phone_verified

    class Meta:
        model = get_user_model()
        fields = ['email', 'password', 'tokens', 'email_verified',
                  'phone_verified', ]

    def validate(self, attrs):  # noqa
        email = attrs.get('email', None)
        password = attrs.get('password', None)
        self.user = authenticate(email=email, password=password)

        if not self.user:
            raise AuthenticationFailed('Вы ввели неправильный логин или пароль')

        if not self.user.is_active:
            raise AuthenticationFailed('Аккаунт отключен, обратитесь к администратору')
        return super().validate(attrs)


class EmailVerificationSerializer(serializers.ModelSerializer):
    email_verification_code = serializers.CharField(
        required=True,
        error_messages={"blank": "Введите 4-х значный Код подтверждения"})

    class Meta:
        model = get_user_model()
        fields = ['email_verification_code', ]


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


class ResendVerificationEmailSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        max_length=255, min_length=3,
        error_messages={"blank": "Введите E-mail адрес"})

    class Meta:
        model = get_user_model()
        fields = ['email', ]


class UserDetailSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(min_length=2)
    is_superuser = serializers.BooleanField()
    email_verified = serializers.BooleanField()
    is_active = serializers.BooleanField()
    is_staff = serializers.BooleanField()
    phone_number = serializers.CharField()
    phone_verified = serializers.BooleanField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    avatar = serializers.CharField()
    phone_change = serializers.CharField()

    class Meta:
        model = get_user_model()
        fields = ('id', 'email', 'is_superuser',
                  'email_verified', 'is_active', 'is_staff',
                  'phone_number', 'phone_verified', 'first_name',
                  'last_name', 'avatar', 'phone_change')


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
    first_name = serializers.CharField()
    last_name = serializers.CharField()

    class Meta:
        model = User
        fields = ("first_name", "last_name",)


class UpdateUserPhoneNumberSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(
        required=True,
        error_messages={"blank": "Введите Номер телефона."})

    class Meta:
        model = get_user_model()
        fields = ('phone_number',)

    def validate(self, data):
        phone_number = str(data.get('phone_number', None)).strip()
        validate_phone_number(phone_number=phone_number)
        return super().validate(data)


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


class AddingImageUserSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(error_messages={"blank": 'Выберите рисунок'},
                                    required=True)

    class Meta:
        model = get_user_model()
        fields = ['avatar', ]
