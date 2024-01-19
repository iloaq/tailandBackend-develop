from rest_framework_simplejwt.authentication import JWTAuthentication


class JWTMiddleware:
    """забей, это не используется"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, scope, receive, send):
        # Получение JWT токена из заголовка авторизации
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        token_prefix, token = auth_header.split(' ')

        # Проверка и аутентификация токена
        authentication = JWTAuthentication()
        validated_token = authentication.get_validated_token(token)

        # Получение пользователя из токена
        user = authentication.get_user(validated_token)

        # Добавление пользователя в атрибут request
        scope['user'] = user

        return super().__call__(scope, receive, send)