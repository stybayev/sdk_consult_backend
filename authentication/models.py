from django.contrib.auth import get_user_model
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin)
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib import auth
from django.apps import apps
from django.contrib.auth.hashers import (
    make_password,
)
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """

        if email is None:
            raise TypeError('Users should have a email')

        email = self.normalize_email(email)

        apps.get_model(
            self.model._meta.app_label, self.model._meta.object_name
        )
        user = self.model(email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)

    def with_perm(  # noqa: C901
            self, perm, is_active=True, include_superusers=True, backend=None, obj=None
    ):  # noqa: C901
        if backend is None:
            backends = auth._get_backends(return_tuples=True)
            if len(backends) == 1:
                backend, _ = backends[0]
            else:
                raise ValueError(
                    "You have multiple authentication backends configured and "
                    "therefore must provide the `backend` argument."
                )
        elif not isinstance(backend, str):
            raise TypeError(
                "backend must be a dotted import path string (got %r)." % backend
            )
        else:
            backend = auth.load_backend(backend)
        if hasattr(backend, "with_perm"):
            return backend.with_perm(
                perm,
                is_active=is_active,
                include_superusers=include_superusers,
                obj=obj,
            )
        return self.none()


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=255, unique=True, db_index=True, null=False, blank=False)
    email_verified = models.BooleanField(default=False)
    email_verification_code = models.CharField(max_length=255, null=True, blank=True)
    username = models.CharField(max_length=255, db_index=True, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    profile_filled = models.BooleanField(default=False)
    kyc_verification_status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    phone_number = models.CharField(max_length=255, null=True, blank=True)
    phone_change = models.CharField(max_length=255, null=True, blank=True, default='')
    phone_verified = models.BooleanField(default=False)
    phone_verification_code = models.CharField(max_length=255, null=True, blank=True)

    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    patronymic = models.CharField(max_length=255, null=True, blank=True)
    iin_number = models.CharField(max_length=12, null=True, blank=True)

    avatar = models.ImageField(
        null=True,
        blank=False,
        upload_to='images/user_pics/',
        verbose_name='Фото пользователя',
        default='images/user_pics/default.png'
    )

    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.full_name

    objects = UserManager()

    @property
    def full_name(self):
        if self.first_name and self.last_name:
            name = f'{self.first_name} {self.first_name}'
        else:
            name = self.email
        return name

    @property
    def tokens(self):
        return self._generate_jwt_token()

    def get_short_name(self):
        return self.last_name

    def _generate_jwt_token(self):
        refresh = RefreshToken.for_user(self)
        token = {
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }
        return token

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "01 Пользователи"


