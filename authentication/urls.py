from django.urls import path

from authentication.views import RegisterView, LoginAPIView, VerifyEmailView, LogoutAPIView, \
    ResendVerificationEmailView, UserDetailView, RefreshTokenView, ChangePasswordView, UpdateProfileView, \
    UpdateUserPhoneNumberView, RequestPasswordResetEmailView, PasswordTokenCheckView, SetNewPasswordView, \
    CheckEmailForUniquenessView, AddingImageUser

urlpatterns = [
    path('registration/',
         RegisterView.as_view(),
         name='user_registration'),

    path('login/',
         LoginAPIView.as_view(),
         name='user_login'),

    path('email_verify/',
         VerifyEmailView.as_view(),
         name='email_verify'),

    path('logout/',
         LogoutAPIView.as_view(),
         name='logout'),

    path('resend_email_verify/',
         ResendVerificationEmailView.as_view(),
         name='resend_email_verify'),


    path('token/refresh/',
         RefreshTokenView.as_view(),
         name='token_refresh'),

    path('user_detail/',
         UserDetailView.as_view(),
         name='user_detail'),

    path('update_password/',
         ChangePasswordView.as_view(),
         name='update_password'),

    path('update_profile/',
         UpdateProfileView.as_view(),
         name='update_profile'),

    path('update_user_phone_number/',
         UpdateUserPhoneNumberView.as_view(),
         name='update_user_phone_number'),

    path('request_reset_password/',
         RequestPasswordResetEmailView.as_view(),
         name='request_reset_password'),

    path('password_reset_confirm/<uidb64>/<token>/',
         PasswordTokenCheckView.as_view(),
         name='password_reset_confirm'),

    path('password_reset_complete/',
         SetNewPasswordView.as_view(),
         name='password_reset_complete'),

    path('check_email_for_uniqueness/',
         CheckEmailForUniquenessView.as_view(),
         name='check_email_for_uniqueness'),

    path('adding_image_user/',
         AddingImageUser.as_view(),
         name='adding_image_user')
]
