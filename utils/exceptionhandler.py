from rest_framework.exceptions import NotAuthenticated, AuthenticationFailed, MethodNotAllowed
from rest_framework.response import Response
from rest_framework.views import exception_handler
from authentication import messages
from authentication.exceptions import (EmailVerifyError,
                                       TokenErrorAPIException,
                                       InvalidTokenAPIException)


def get_full_details(detail, response):  # noqa
    if isinstance(detail, list):
        for item in detail:
            return get_full_details(item, response)

    elif isinstance(detail, dict):
        return {key: get_full_details(value, response) for key, value in detail.items()}

    if detail == 'Token is invalid or expired' or detail == 'token_not_valid':
        error_payload = {
            'status_code': 401,
            'message': messages.TEXT_UNAUTHORIZED,
        }
        return error_payload

    error_payload = {
        'status_code': 0,
        'message': detail,
    }
    status_code = response.status_code
    error_payload['status_code'] = status_code
    return error_payload


class Responses:

    @staticmethod
    def error_response(error_messages, status_code):
        return Response({
            'error': {
                'message': error_messages,
                'status_code': status_code}
        }, status=status_code)


def custom_exception_handler(exc, context):  # noqa
    response = exception_handler(exc, context)

    if response is not None:
        response.data = get_full_details(detail=exc.detail, response=response)

        if isinstance(exc, NotAuthenticated):
            return Responses.error_response(error_messages=messages.TEXT_ERROR_UNAUTHORIZED,
                                            status_code=401)

        if isinstance(exc, AuthenticationFailed):
            return Responses.error_response(error_messages=messages.TEXT_AUTHENTICATION_FAILED,
                                            status_code=401)

        if isinstance(exc, EmailVerifyError):
            return Responses.error_response(error_messages=messages.EMAIL_VERIFIED,
                                            status_code=401)

        if isinstance(exc, TokenErrorAPIException):
            return Responses.error_response(error_messages=messages.TEXT_UNAUTHORIZED,
                                            status_code=401)

        if isinstance(exc, InvalidTokenAPIException):
            return Responses.error_response(error_messages=messages.TEXT_UNAUTHORIZED,
                                            status_code=401)

        if isinstance(exc, MethodNotAllowed):
            return Responses.error_response(
                error_messages=MethodNotAllowed.get_full_details(exc)['message'],
                status_code=MethodNotAllowed.status_code)

        error_response = dict()
        for key, value in response.data.items():
            error = {'field': key,
                     'message': value['message'],
                     'status_code': value['status_code']}
            error_response['error'] = error
        response.data = error_response

    return response
