from rest_framework.exceptions import APIException
from rest_framework import status
from django.core.exceptions import ValidationError
import re


class UserValidation(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'A server error occurred.'

    def __init__(self, detail, field, status_code):
        if status_code is not None:self.status_code = status_code
        if detail is not None:
            self.detail = {field: str((detail))}
        else: self.detail = {'detail': str(self.default_detail)}



class TimeFormatValidator:
    def __init__(self, format):
        self.format = format

    def __call__(self, value):
        if not re.match(self.format, value):
            raise ValidationError('Неверный формат времени.')