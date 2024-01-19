from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.contrib.auth.hashers import make_password


class User(AbstractUser):
    ROLE_CHOICES = (
        (1, 'Пользователь'),
        (2, 'Партнер'),
        (3, 'Админ'),
    )

    role = models.IntegerField(choices=ROLE_CHOICES, default=1)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Номер телефона должен быть в формате: '+999999999'. Максимальная длина - 15 символов."
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=15,
        blank=True,
        null=True
    )
    avatar = models.ImageField(null=True, blank=True)
    code = models.CharField(null=True, blank=True)
    country_code = models.CharField(null=True, blank=True, max_length=10)
    phone_code = models.CharField(null=True, blank=True, max_length=10)
    blocked = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        """Для шифрования пароля
        при создании пользователя через админку"""

        if not self.password.startswith('pbkdf2_sha256'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username
    




