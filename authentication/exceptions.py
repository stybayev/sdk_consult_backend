from rest_framework.exceptions import ValidationError, APIException


class IncorrectEmailVerificationCodeException(Exception):
    pass


class IncorrectPhoneVerificationCodeException(Exception):
    pass


class SmsSendingError(Exception):
    pass


class EmailVerifyError(ValidationError):
    pass


class TokenErrorAPIException(APIException):
    pass


class InvalidTokenAPIException(APIException):
    pass
