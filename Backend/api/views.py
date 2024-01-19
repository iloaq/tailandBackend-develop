from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from .tasks import send_registration_email
from django_filters.rest_framework import DjangoFilterBackend
from django.core.exceptions import ValidationError
from django.db.models import F

from rest_framework_simplejwt.views import TokenViewBase
from rest_framework.response import Response
from rest_framework import status, permissions, generics, filters, serializers
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.pagination import PageNumberPagination
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import os


from .serializers import (
    AllModelsSerializer, ApplicationsUnblockSerializer, BlockUserSerializer, FacilitiesSerializer, RentalServicesSerializer, ServiceSerializer, TypeRoomSerializer, UserSerializer,
    UserRegisterSerializer, HotelSerializer,
    RestaurantSerializer, FaqSerializer,
    NewsSerializer, TransportSerializer, FavoriteListSerializer,
    FavoriteCRUDSerializer,
    TripFolderSerializer, UserInfoSerializer, FeaturesSerializer,
    KitchenSerializer, ConditionsSerializer, InclusiveSerializer,
    ExcursionSerializer, ApplicationOnExcursionSerializer, ApplicationUpdateStatus,
    RemoveFavoriteSerializer, ReviewSerializer, PartnerProfileSerializer, 
    AdminPartnerRegisterSerializer, InfoSerializer
    )
from .scripts import generate_code, get_city
from users.models import User
from .models import (Hotel, Photo, RentalServices, Restaurant, Faq, News,
                     Transport, TripFolder, Favorite, Features,
                     Kitchen, Service, Facilities, TypeRoom,
                     Conditions, Inclusive, Excursion, ApplicationOnExcursion,
                     Review, ApplicationUnblock, Info)
from .permissions import IsPartnerOrAdmin, IsAdmin, IsPartnerOrAdminCreate, IsPartnerOrAdminForApplicationsOnExcursions, IsUser
from .filters import (
    HotelFilter, FavoriteFilter, RestaurantFilter, 
    ReviewFilter, RestaurantFilter, ExcursionFilter, ApplicationOnExcursionFilter, TransportFilterBackend)
from .pagination import Paginator


class RefreshTokenn(APIView):
    """Обновление access токена с помощью refresh"""

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='refresh token'),
            }
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'access': openapi.Schema(type=openapi.TYPE_STRING, description='access token'),
                },
                description='Successful response'
            ),
        }
    )
    def post(self, request):
        refresh = request.data.get('refresh')

        if refresh:
            try:
                token = RefreshToken(refresh)
                access = str(token.access_token)
                return Response({'access': access})
            except Exception as e:
                return Response({'error': str(e)}, status=400)
        else:
            return Response({'error': 'Refresh token is required'}, status=400)


class CustomObtainAuthToken(TokenViewBase):
    """Авторизация"""

    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'login': openapi.Schema(type=openapi.TYPE_STRING, description='Username or email'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
            }
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                    'access': openapi.Schema(type=openapi.TYPE_STRING),
                    'user': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='User ID'),
                            'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
                            'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email'),
                            'role': openapi.Schema(type=openapi.TYPE_INTEGER, description='role of user')
                        }
                    )
                },
                description='Successful response'
            ),
        }
    )
    def post(self, request, *args, **kwargs):
        login = request.data.get('login')
        password = request.data.get('password')
        # Проверяем наличие пользователя по username или email
        user = None
        if '@' in login:
            user = User.objects.filter(email=login).first()
        else:
            user = User.objects.filter(username=login).first()

        if user:
            # Проверяем правильность пароля
            user = authenticate(username=user.username, password=password)
            if user.role == 4:
                return JsonResponse({'message': 'Account is blocked'}, status=status.HTTP_403_FORBIDDEN)
            if user:
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': UserSerializer(user).data
                })

        # Если пользователь или пароль неправильные, возвращаем ошибку
        return Response({'error': 'Неверные данные для входа'},
                        status=status.HTTP_400_BAD_REQUEST)


class RegistrationView(APIView):
    """Регистрация"""
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='email'),
                'full_name': openapi.Schema(type=openapi.TYPE_STRING, description='Name and second name'),
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='username'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='password'),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='phone number'),
                'countyCode': openapi.Schema(type=openapi.TYPE_STRING, description='county code'),
            }
        ),
        responses={
            201: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                description='Successful response'
            ),
        }
    )
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'Пользователь успешно зарегистрирован'},
                status=201
            )
        return Response(serializer.errors, status=400)
    

@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_user(request):
    user = request.user
    user.delete()
    return Response({'message': 'User deleted successfully'})


class SendEmailView(APIView):
    "Отправка письма с кодом"
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='email'),               
            }
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'messege': openapi.Schema(type=openapi.TYPE_STRING, description='Код отправлен'),
                },
                description='Successful response'
            ),
        }
    )
    def post(self, request):
        email = request.data.get('email')
        if not User.objects.filter(email=email).exists():
            return Response({'error': 'Такого пользователя нет'}, status=400)
        if email is None:
            return Response({'error': 'Email обязателен'}, status=400)
        user = User.objects.get(email=email)
        # Генерация случайного 4-значного кода
        code = generate_code()
        image_path = 'https://static.tildacdn.com/tild6630-3165-4937-a531-656233303437/sumit-chinchane-jWKk.jpg' # это нужно чтоб была фотка в письме, потому что если брать свою фотку она не будет показываться т.к. нет SSL серта и домена соответсвенно
        message = render_to_string('index.html', {'first': str(code)[0],
                                                  'second': str(code)[1],
                                                  'third': str(code)[2],
                                                  'fourth': str(code)[3],
                                                  'image_path': image_path,
                                                  'code': code,
                                                  })
        # Отправка кода на почту
        send_mail(
            'Смена пароля',
            message,
            os.getenv('MAIL_LOGIN'),
            [email],
            html_message=message,
            fail_silently=True,
        )

        # Сохранение кода в сессии
        user.code = str(code)
        user.save()
        return Response({'message': 'Код отправлен'},
                        status=status.HTTP_200_OK)

class VerifyCodeView(APIView):
    """проверка кода"""
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'code': openapi.Schema(type=openapi.TYPE_STRING, description='code'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='email'),           
            }
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'messege': openapi.Schema(type=openapi.TYPE_STRING, description='Код верен'),
                },
                description='Successful response'
            ),
            400: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'messege': openapi.Schema(type=openapi.TYPE_STRING, description='Код не верен'),
                },
                description='error'
            ),
        }
    )
    def post(self, request):
        code = request.data.get('code')  
        email = request.data.get('email')
        user = User.objects.get(email=email)
        if code is None:
            return Response({'error': 'Код обязателен для заполнения'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Проверка кода
        if user.code == str(code):
            return Response({'message': 'Код верен'},
                            status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Код не верен'},
                            status=status.HTTP_400_BAD_REQUEST)


class UpdatePasswordView(APIView):
    "Обновляем пароль"
    @swagger_auto_schema(
        operation_description="Обновление пароля после проверки кода",
        operation_summary="Обновление пароля после проверки кода",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='email'),
                'new_password': openapi.Schema(type=openapi.TYPE_STRING, description='new password'),
                'code': openapi.Schema(type=openapi.TYPE_STRING, description='new password')
            }
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'messege': openapi.Schema(type=openapi.TYPE_STRING, description='Пароль успешно изменен'),
                },
                description='Successful response'
            ),
        }
    )
    def post(self, request):
        # Получение нового пароля из запроса
        new_password = request.data.get('new_password')
        email = request.data.get('email')
        code = request.data.get('code')
        if code != request.session.get('code'):
            return Response({'error': 'Неверный код'},
                            status=status.HTTP_400_BAD_REQUEST)
        # Проверка наличия нового пароля в запросе
        if new_password is None:
            return Response({'error': 'Введите новый пароль'},
                            status=status.HTTP_400_BAD_REQUEST)
        if email is None:
            return Response({'error': 'Введите email'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Обновление пароля пользователя
        user = User.objects.get(email=email)
        user.password = make_password(new_password)
        user.save()

        return Response({'message': 'Пароль успешно изменен'},
                        status=status.HTTP_200_OK)


# Пагинация раньше была, с предыдущим разработчиком делали, новый просил убрать
# Дефолтные круд операции без логики особой комментить не буду
class HotelListView(generics.ListAPIView):
    queryset = Hotel.objects.prefetch_related('owner', 'chat_room', 'type_room', 'facilities', 'services').filter(status=True) # фильтрую по статусу чтоб в выдаче были только уже одобренные админом отели (то же самое для прочих объектов)
    serializer_class = HotelSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    # pagination_class = Paginator
    filter_backends = [HotelFilter, filters.OrderingFilter]

    @swagger_auto_schema(
        operation_description="Получение списка отелей. JWT Аутентификация. Доступно всем аутентифицированным.",
        operation_summary="Получение списка отелей",
        manual_parameters=[
            openapi.Parameter(
                name='promotion',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_BOOLEAN,
                description='Фильтр по наличию акции'
            ),
            openapi.Parameter(
                name='min_cost',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                description='Минимальная стоимость номера'
            ),
            openapi.Parameter(
                name='max_cost',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                description='Максимальная стоимость номера'
            ),
            openapi.Parameter(
                name='location',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description='Фильтр по местоположению отеля'
            ),
            openapi.Parameter(
                name='type_rooms',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.TYPE_INTEGER),
                description='Список ID типов комнат для фильтрации'
            ),
            openapi.Parameter(
                name='facilities',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.TYPE_INTEGER),
                description='Список ID удобств для фильтрации'
            ),
            openapi.Parameter(
                name='services',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.TYPE_INTEGER),
                description='Список ID услуг для фильтрации'
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class HotelCreateView(generics.CreateAPIView):
    queryset = Hotel.objects.prefetch_related('owner', 'chat_room', 'type_room', 'facilities', 'services', 'photos')
    serializer_class = HotelSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsPartnerOrAdminCreate]

    def perform_create(self, serializer):
        user = self.request.user
        if 'photos' in self.request.data:
            photos_data = self.request.data.getlist('photos')
        else:
            photos_data = None
        latitude = self.request.data.get('latitude') # получаем широту из запроса
        longitude = self.request.data.get('longitude') # получаем долготу из запроса
        city = str(get_city(latitude=latitude, longitude=longitude))
        hotel = serializer.save(owner=user, location=city)
        if 'photos' in self.request.data:
            for photo_data in photos_data:
                photo = Photo.objects.create(photo=photo_data)
                hotel.photos.add(photo)

        serializer.save(owner=user)


class HotelRetrieveView(generics.RetrieveAPIView):
    queryset = Hotel.objects.prefetch_related('owner', 'chat_room', 'type_room', 'facilities', 'services','photos')
    serializer_class = HotelSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]


class HotelUpdateView(generics.UpdateAPIView):
    queryset = Hotel.objects.prefetch_related('owner', 'chat_room', 'type_room', 'facilities', 'services', 'photos')
    serializer_class = HotelSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsPartnerOrAdmin]


class HotelDeleteView(generics.DestroyAPIView):
    queryset = Hotel.objects.prefetch_related('owner', 'chat_room', 'type_room', 'facilities', 'services', 'photos')
    serializer_class = HotelSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsPartnerOrAdmin]


class RestaurantListView(generics.ListAPIView):
    queryset = Restaurant.objects.prefetch_related('chat_room', 'owner', 'features', 'kitchen').filter(status=True)
    serializer_class = RestaurantSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter, RestaurantFilter]
    # pagination_class = Paginator

    @swagger_auto_schema(
        operation_description="Получение списка ресторанов. JWT Аутентификация. Доступно всем аутентифицированным.",
        operation_summary="Получение списка ресторанов",
        manual_parameters=[
            openapi.Parameter('location', openapi.IN_QUERY, description="Фильтр по местоположению", type=openapi.TYPE_STRING),
            openapi.Parameter('promotion', openapi.IN_QUERY, description="Фильтр по акции", type=openapi.TYPE_STRING),
            openapi.Parameter('features', openapi.IN_QUERY, description="Фильтр по особенностям", type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_INTEGER)),
            openapi.Parameter('kitchen', openapi.IN_QUERY, description="Фильтр по кухне", type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_INTEGER)),
            openapi.Parameter('min_cost', openapi.IN_QUERY, description="Фильтр по минимальной стоимости", type=openapi.TYPE_NUMBER),
            openapi.Parameter('max_cost', openapi.IN_QUERY, description="Фильтр по максимальной стоимости", type=openapi.TYPE_NUMBER),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class RestaurantCreateView(generics.CreateAPIView):
    queryset = Restaurant.objects.prefetch_related('chat_room', 'owner', 'features', 'kitchen')
    serializer_class = RestaurantSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsPartnerOrAdminCreate]

    def perform_create(self, serializer):
        user = self.request.user
        if 'photos' in self.request.data:
            photos_data = self.request.data.getlist('photos')
        else:
            photos_data = None
        latitude = self.request.data.get('latitude') # получаем широту из запроса
        longitude = self.request.data.get('longitude') # получаем долготу из запроса
        city = str(get_city(latitude=latitude, longitude=longitude))
        restaurant = serializer.save(owner=user, location=city)
        if photos_data:
            for photo_data in photos_data:
                photo = Photo.objects.create(photo=photo_data)
                restaurant.photos.add(photo)

        serializer.save(owner=user)


class RestaurantRetrieveView(generics.RetrieveAPIView):
    queryset = Restaurant.objects.prefetch_related('chat_room', 'owner', 'features', 'kitchen')
    serializer_class = RestaurantSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]


class RestaurantUpdateView(generics.UpdateAPIView):
    queryset = Restaurant.objects.prefetch_related('chat_room', 'owner', 'features', 'kitchen')
    serializer_class = RestaurantSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsPartnerOrAdmin]


class RestaurantDeleteView(generics.DestroyAPIView):
    queryset = Restaurant.objects.prefetch_related('chat_room', 'owner', 'features', 'kitchen')
    serializer_class = RestaurantSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsPartnerOrAdmin]


class FaqListView(generics.ListAPIView):
    queryset = Faq.objects.all()
    serializer_class = FaqSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]


class FaqCreateView(generics.CreateAPIView):
    queryset = Faq.objects.all()
    serializer_class = FaqSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]


class FaqRetrieveView(generics.RetrieveAPIView):
    queryset = Faq.objects.all()
    serializer_class = FaqSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]


class FaqUpdateView(generics.UpdateAPIView):
    queryset = Faq.objects.all()
    serializer_class = FaqSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]


class FaqDeleteView(generics.DestroyAPIView):
    queryset = Faq.objects.all()
    serializer_class = FaqSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]


class NewsListView(generics.ListAPIView):
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]


class NewsCreateView(generics.CreateAPIView):
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]


class NewsRetrieveView(generics.RetrieveAPIView):
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]


class NewsUpdateView(generics.UpdateAPIView):
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]


class NewsDeleteView(generics.DestroyAPIView):
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]


class TransportListView(generics.ListAPIView):
    queryset = Transport.objects.filter(status=True)
    serializer_class = TransportSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    # pagination_class = Paginator
    filter_backends = [filters.OrderingFilter, TransportFilterBackend]


class TransportCreateView(generics.CreateAPIView):
    queryset = Transport.objects.all()
    serializer_class = TransportSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsPartnerOrAdminCreate]

    def perform_create(self, serializer):
        user = self.request.user
        if 'photos' in self.request.data:
            photos_data = self.request.data.getlist('photos')
        else:
            photos_data = None
        latitude = self.request.data.get('latitude') # получаем широту из запроса
        longitude = self.request.data.get('longitude') # получаем долготу из запроса
        city = str(get_city(latitude=latitude, longitude=longitude))
        transport = serializer.save(location=city)
        if photos_data is not None:
            for photo_data in photos_data:
                photo = Photo.objects.create(photo=photo_data)
                transport.photos.add(photo)
        serializer.save(owner=user)


class TransportRetrieveView(generics.RetrieveAPIView):
    queryset = Transport.objects.all()
    serializer_class = TransportSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]


class TransportUpdateView(generics.UpdateAPIView):
    queryset = Transport.objects.all()
    serializer_class = TransportSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsPartnerOrAdmin]


class TransportDeleteView(generics.DestroyAPIView):
    queryset = Transport.objects.all()
    serializer_class = TransportSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsPartnerOrAdmin]


class TripFolderListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = TripFolderSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        folders = TripFolder.objects.filter(user=self.request.user)
        return folders


class TripFolderRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    queryset = TripFolder.objects.select_related('user')
    serializer_class = TripFolderSerializer


class FavoriteListAPIView(generics.ListAPIView):
    queryset = Favorite.objects.prefetch_related('user', 'hotels', 'folder', 'restaurants', 'transport')
    serializer_class = FavoriteListSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = FavoriteFilter

    def get_queryset(self):
        favorites = self.request.user.favorite_set.all()
        return favorites
    
    @swagger_auto_schema(
        operation_description="Get list of favorites",
        responses={200: FavoriteListSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class FavoriteCreateAPIView(generics.CreateAPIView):
    queryset = Favorite.objects.prefetch_related('user', 'hotels', 'folder', 'restaurants', 'transport')
    serializer_class = FavoriteCRUDSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Create a favorite",
        request_body=FavoriteCRUDSerializer(),
        responses={201: FavoriteCRUDSerializer()})
    # Спасибо артуру за постоянное имзенение логики избранного. 
    # насколько помню, раньше добавлялось в избранное атвоматом в последнюю папку, 
    # потом можно было изменить. last_folder нужен для изменения папки.
    # list_folder для добавления в несколько папок.
    # хз какая сейчас логика, как использует это сардар
    def create(self, request, *args, **kwargs):
        """
        Переопределение метода create для добавления отеля в избранное
        """
        folder_id = request.data.get('folder')
        hotel_id = request.data.get('hotels')
        restaurant_id = request.data.get('restaurants')
        transport_id = request.data.get('transport')
        excursion_id = request.data.get('excursions')
        last_folder_id = request.data.get('last_folder')
        list_folders = request.data.get('list_folders') 

        if list_folders is not None:
            for i in list_folders:
                if hotel_id is not None:
                    favorite = Favorite.objects.get(folder_id=i)
                    favorite.hotels.add(hotel_id)
                    favorite.save()
                if restaurant_id is not None:
                    favorite = Favorite.objects.get(folder_id=i)
                    favorite.restaurants.add(restaurant_id)
                    favorite.save()
                if transport_id is not None:
                    favorite = Favorite.objects.get(folder_id=i)
                    favorite.transport.add(transport_id)
                    favorite.save()
                if excursion_id is not None:
                    favorite = Favorite.objects.get(folder_id=i)
                    favorite.excursion.add(excursion_id)
                    f = TripFolder.objects.get(id=i)
                    f.countFavorites += 1
                    f.save()
                    favorite.save()
                f = TripFolder.objects.get(id=i)
                f.countFavorites += 1
                f.save()
            return JsonResponse({'message': 'Ok'}, status=200)

        if folder_id is None:
            try:
                folder = TripFolder.objects.filter(user=request.user).last()
                folder_id = folder.id
            except AttributeError:
                return JsonResponse({'error': 'the user has no created folders'}, status=404)
        # Проверяем, существует ли уже объект Favorite для данного пользователя и папки
        favorite = Favorite.objects.filter(user=request.user, folder_id=folder_id).first()
        if last_folder_id is not None:
            last_favorite = Favorite.objects.get(folder_id=last_folder_id)
            if hotel_id is not None:
                last_favorite.hotels.remove(hotel_id)
                f = TripFolder.objects.get(id=last_folder_id)
                f.countFavorites -= 1
                f.save()
            if restaurant_id is not None:
                last_favorite.restaurants.remove(restaurant_id)
                f = TripFolder.objects.get(id=last_folder_id)
                f.countFavorites -= 1
                f.save()
            if transport_id is not None:
                last_favorite.transport.remove(transport_id)
                f = TripFolder.objects.get(id=last_folder_id)
                f.countFavorites -= 1
                f.save()
            if excursion_id is not None:
                last_favorite.excursions.remove(excursion_id)
                f = TripFolder.objects.get(id=last_folder_id)
                f.countFavorites -= 1
                f.save()
        if favorite:
            if hotel_id is not None:
                favorite.hotels.add(hotel_id)
            if restaurant_id is not None:
                favorite.restaurants.add(restaurant_id)   
            if transport_id is not None:
                favorite.transport.add(transport_id)
            if excursion_id is not None:
                favorite.excursions.add(excursion_id)
            folder = TripFolder.objects.get(id=folder_id)
            folder.countFavorites += 1
            folder.save()
        else:
            # Если не существует, то создаем новый объект Favorite и добавляем отель в его список отелей
            favorite = Favorite.objects.create(user=request.user, folder_id=folder_id)
            if hotel_id is not None:
                favorite.hotels.add(hotel_id)
            if restaurant_id is not None:
                favorite.restaurants.add(restaurant_id)   
            if transport_id is not None:
                favorite.transport.add(transport_id)
            if excursion_id is not None:
                favorite.excursions.add(excursion_id)
            folder = TripFolder.objects.get(id=folder_id)
            folder.countFavorites += 1
            folder.save()
        serializer = self.get_serializer(favorite)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class FavoriteRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Favorite.objects.prefetch_related('user', 'hotels', 'folder', 'restaurants', 'transport')
    serializer_class = FavoriteCRUDSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('index', openapi.IN_PATH, description='Индекс папки поездки', type=openapi.TYPE_INTEGER),
            openapi.Parameter('hotels', openapi.IN_FORM, description='Индекс отеля', type=openapi.TYPE_INTEGER),
            openapi.Parameter('restaurants', openapi.IN_FORM, description='Индекс ресторана', type=openapi.TYPE_INTEGER),
            openapi.Parameter('transport', openapi.IN_FORM, description='Индекс транспорта', type=openapi.TYPE_INTEGER)
        ],
        responses={
            204: openapi.Response(description='Успешное удаление'),
            400: openapi.Response(description='Некорректные данные'),
            404: openapi.Response(description='Не найден отель, ресторан или транспорт')
        },
        operation_summary="Удаление избранного",
        operation_description="Метод для удаления отеля, ресторана или транспорта из списка избранного по индексу папки поездки."
    )
    def destroy(self, request, *args, **kwargs):
        """Удаление из избранного. Устаревший метод"""
        favorite = self.get_object()
        hotel_id = request.data.get('hotels')
        restaurant_id = request.data.get('restaurants')
        transport_id = request.data.get('transport')
        excursions_id = request.data.get('excursions')

        if (not hotel_id) and (not restaurant_id) and (not transport_id) and (not excursions_id):
            return Response({"message": "required params"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            if hotel_id is not None:
                hotel = Hotel.objects.get(id=hotel_id)
                favorite.hotels.remove(hotel)
            if restaurant_id is not None:
                restaurant = Restaurant.objects.get(id=restaurant_id)
                favorite.restaurants.remove(restaurant)
            if transport_id is not None:
                transport = Transport.objects.get(id=transport_id)
                favorite.transport.remove(transport)
            if excursions_id is not None:
                excursion = Excursion.objects.get(id=excursions_id)
                favorite.excursions.remove(excursion)
        except Hotel.DoesNotExist:
            return Response({"message": "Hotel not found"}, status=status.HTTP_404_NOT_FOUND)
        except Transport.DoesNotExist:
            return Response({"message": "Transport not found"}, status=status.HTTP_404_NOT_FOUND)
        except Restaurant.DoesNotExist:
            return Response({"message": "Restaurant not found"}, status=status.HTTP_404_NOT_FOUND)
        except Excursion.DoesNotExist:
            return Response({"message": "Excursion not found"}, status=status.HTTP_404_NOT_FOUND)

        favorite.save()
        folder = favorite.folder
        folder.countFavorites -= 1
        folder.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DeleteFavoriteAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RemoveFavoriteSerializer
    
    @swagger_auto_schema(
        request_body=RemoveFavoriteSerializer,
        responses={
            204: openapi.Response(description='Успешное удаление'),
            400: openapi.Response(description='Некорректные данные'),
            404: openapi.Response(description='Не найден отель, ресторан, транспорт или экскурсия')
        },
        operation_summary="Удаление избранного",
        operation_description="Метод для удаления отеля, ресторана, транспорта или экскурсии из списка избранного"
    )
    def post(self, request):
        """Удаление из избранного. Активный метод, его использовать для удаления из избранного"""
        hotel_id = request.data.get('hotel_id', None)
        restaurant_id = request.data.get('restaurant_id', None)
        transport_id = request.data.get('transport_id', None)
        excursion_id = request.data.get('excursion_id', None)

        if (not hotel_id) and (not restaurant_id) and (not transport_id) and (not excursion_id):
            return Response({"message": "required params"}, status=status.HTTP_400_BAD_REQUEST)
        if hotel_id is not None:
            hotel = Hotel.objects.get(id=hotel_id)
            favorite = Favorite.objects.get(user=request.user, hotels=hotel)
            favorite.hotels.remove(hotel)
            folder = favorite.folder
            folder.countFavorites -= 1
            folder.save()
        if restaurant_id is not None:
            restaurant = Restaurant.objects.get(id=restaurant_id)
            favorite = Favorite.objects.get(user=request.user, restaurants=restaurant)
            favorite.restaurants.remove(restaurant)
            folder = favorite.folder
            folder.countFavorites -= 1
            folder.save()
        if transport_id is not None:
            transport = Transport.objects.get(id=transport_id)
            favorite = Favorite.objects.get(user=request.user, transport=transport)
            favorite.transport.remove(transport)
            folder = favorite.folder
            folder.countFavorites -= 1
            folder.save()
        if excursion_id is not None:
            excursion = Excursion.objects.get(id=excursion_id)
            favorite = Favorite.objects.get(user=request.user, excursions=excursion)
            favorite.excursions.remove(excursion)
            folder = favorite.folder
            folder.countFavorites -= 1
            folder.save()
        
        favorite.save()

        return Response({"message": "seccess delete"}, status=status.HTTP_204_NO_CONTENT)


class UserInfo(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @swagger_auto_schema(
        operation_description="Get user information",
        operation_summary="Получение информации о текущем пользователе",
        responses={200: UserInfoSerializer()})
    def get(self, request):
        user = request.user
        data = {
            'avatar': user.avatar.url if user.avatar else None,
            'phone_number': user.phone_number,
            'username': user.username,
            'full_name': user.get_full_name(),
            'coutry_code': user.country_code if user.country_code else None,
            'phone_code': user.phone_code if user.phone_code else None,
            'email': user.email,
            'role': user.role,
        }
        return Response(data)

    @swagger_auto_schema(
        operation_description="Update user information",
        request_body=UserInfoSerializer(),
        responses={200: UserInfoSerializer()})
    def put(self, request):
        user = request.user
        serializer = UserInfoSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            # Получение обновленной информации пользователя
            data = {
                'avatar': user.avatar.url if user.avatar else None,
                'phone_number': user.phone_number,
                'username': user.username,
                'full_name': user.get_full_name(),
                'coutry_code': user.country_code if user.country_code else None,
                'phone_code': user.phone_code if user.phone_code else None,
                'email': user.email,
            }
            return Response(data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class FeaturesListApiView(generics.ListAPIView):
    """особенности ресторана по типу еда на вынос, бронирование и т.д."""
    queryset = Features.objects.all()
    serializer_class = FeaturesSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]


class FeaturesRetriveApiView(generics.RetrieveAPIView):
    queryset = Features.objects.all()
    serializer_class = FeaturesSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]


class KitchenListApiView(generics.ListAPIView):
    """кухня ресторана по типу азиматская, европейская и т.д."""
    queryset = Kitchen.objects.all()
    serializer_class = KitchenSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]


class KitchenRetriveApiView(generics.RetrieveAPIView):
    queryset = Kitchen.objects.all()
    serializer_class = KitchenSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]


class ServiceListApiView(generics.ListAPIView):
    """Услуги отеля по типу бесплатная парковка, бассейн и т.д."""
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]


class ServiceRetriveApiView(generics.RetrieveAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]


class TypeRoomListApiView(generics.ListAPIView):
    """тип номера по типу сесмейный номер, 4 спальных места и т.д."""
    queryset = TypeRoom.objects.all()
    serializer_class = TypeRoomSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]


class TypeRoomRetriveApiView(generics.RetrieveAPIView):
    queryset = TypeRoom.objects.all()
    serializer_class = TypeRoomSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]


class FacilitiesListApiView(generics.ListAPIView):
    """оснащененность номера по типу сейф, тв и т.д."""
    queryset = Facilities.objects.all()
    serializer_class = FacilitiesSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]


class FacilitiesRetriveApiView(generics.RetrieveAPIView):
    queryset = Facilities.objects.all()
    serializer_class = FacilitiesSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]


class RentalServicesRetriveApiView(generics.RetrieveAPIView):
    queryset = RentalServices.objects.all()
    serializer_class = RentalServicesSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]


class RentalServicesListApiView(generics.ListAPIView):
    """Условия аренды транспорта"""
    queryset = RentalServices.objects.all()
    serializer_class = RentalServicesSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]


class InclusiveListApiView(generics.ListAPIView):
    """что включено в экскурсию"""
    queryset = Inclusive.objects.all()
    serializer_class = InclusiveSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]


class InclusiveRetriveApiView(generics.RetrieveAPIView):
    queryset = Inclusive.objects.all()
    serializer_class = InclusiveSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]


class ConditionsListApiView(generics.ListAPIView):
    """условия экскурсии по типу бесплатная отмена, длительность и т.д."""
    queryset = Conditions.objects.all()
    serializer_class = ConditionsSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]


class ConditionsRetriveApiView(generics.RetrieveAPIView):
    queryset = Conditions.objects.all()
    serializer_class = ConditionsSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]


class ExcursionListView(generics.ListAPIView):
    queryset = Excursion.objects.prefetch_related('inclusives', 'conditions','owner').filter(status=True)
    serializer_class = ExcursionSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [ExcursionFilter, filters.OrderingFilter, filters.SearchFilter]
    # pagination_class = Paginator

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('inclusives', in_=openapi.IN_QUERY, description="List of inclusives IDs", type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_INTEGER), required=False, collectionFormat='multi'),
        openapi.Parameter('conditions', in_=openapi.IN_QUERY, description="List of conditions IDs", type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_INTEGER), required=False, collectionFormat='multi'),
        openapi.Parameter('location', in_=openapi.IN_QUERY, description="Location filter", type=openapi.TYPE_STRING, required=False),
        openapi.Parameter('promotion', in_=openapi.IN_QUERY, description="Promotion filter", type=openapi.TYPE_STRING, required=False),
        openapi.Parameter('min_cost', in_=openapi.IN_QUERY, description="Minimum cost filter", type=openapi.TYPE_INTEGER, required=False),
        openapi.Parameter('max_cost', in_=openapi.IN_QUERY, description="Maximum cost filter", type=openapi.TYPE_INTEGER, required=False),
        openapi.Parameter('lat', in_=openapi.IN_QUERY, description="Latitude for location-based filter", type=openapi.TYPE_NUMBER, required=False),
        openapi.Parameter('lng', in_=openapi.IN_QUERY, description="Longitude for location-based filter", type=openapi.TYPE_NUMBER, required=False),
        openapi.Parameter('min_rate', in_=openapi.IN_QUERY, description="Minimum rate filter", type=openapi.TYPE_NUMBER, required=False),
    ])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ExcursionCreateView(generics.CreateAPIView):
    queryset = Excursion.objects.prefetch_related('inclusives', 'conditions', 'owner')
    serializer_class = ExcursionSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsPartnerOrAdminCreate]

    def perform_create(self, serializer):
        user = self.request.user
        if 'photos' in self.request.data:
            photos_data = self.request.data.getlist('photos')
        else:
            photos_data = None
        excursion = serializer.save()
        if photos_data is not None:
            for photo_data in photos_data:
                photo = Photo.objects.create(photo=photo_data)
                excursion.photos.add(photo)

        serializer.save(owner=user)

    @swagger_auto_schema(
        operation_description="создание экскурсии",
        request_body=ExcursionSerializer,
        responses={201: 'OK'},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class ExcursionRetrieveView(generics.RetrieveAPIView):
    queryset = Excursion.objects.prefetch_related('inclusives', 'conditions', 'owner')
    serializer_class = ExcursionSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsPartnerOrAdmin]


class ExcursionUpdateView(generics.UpdateAPIView):
    queryset = Excursion.objects.prefetch_related('inclusives', 'conditions', 'owner')
    serializer_class = ExcursionSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsPartnerOrAdmin]


class ExcursionDeleteView(generics.DestroyAPIView):
    queryset = Excursion.objects.prefetch_related('inclusives', 'conditions', 'owner')
    serializer_class = ExcursionSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsPartnerOrAdmin]


class UserApplicationsView(generics.ListAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ApplicationOnExcursionSerializer

    def get_queryset(self):
        user = self.request.user
        return ApplicationOnExcursion.objects.filter(user=user).annotate(title=F('excursion__name')) # добавление имени экскурсии в выдачу


class UserCreateApplicationView(generics.CreateAPIView):
    queryset = ApplicationOnExcursion.objects.select_related('user', 'excursion')
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ApplicationOnExcursionSerializer

    def perform_create(self, serializer):
        user = self.request.user
        excursion_id = self.request.data.get('excursion')
        count_of_adults = self.request.data.get('countOfAdults', 0)
        count_of_kids = self.request.data.get('countOfKids', 0)

        try:
            excursion = Excursion.objects.get(id=excursion_id)
            total_amount = excursion.cost * count_of_adults + excursion.cost_kids * count_of_kids
            serializer.save(user=user, total_amount=total_amount)
        except Excursion.DoesNotExist:
            raise serializers.ValidationError("Excursion does not exist.")
        except Exception as e:
            raise serializers.ValidationError(str(e))


class ApplicationUpdateStatus(generics.UpdateAPIView):
    """обновление статуса заявки на экскурсию"""
    queryset = ApplicationOnExcursion.objects.select_related('user', 'excursion')
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsPartnerOrAdminForApplicationsOnExcursions]
    serializer_class = ApplicationUpdateStatus


class PartnerApplicationListView(generics.ListAPIView):
    """получение партнером своих заявок(на свои экскурсии)"""
    serializer_class = ApplicationOnExcursionSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsPartnerOrAdminForApplicationsOnExcursions]
    filterset_class = ApplicationOnExcursionFilter

    def get_queryset(self):
        user = self.request.user
        return ApplicationOnExcursion.objects.filter(excursion__owner=user).annotate(title=F('excursion__name'))
    
    @swagger_auto_schema(
        operation_description="receiving all applications from a partner",
        responses={200: 'OK'},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class PartnerApplicationRetrieveView(generics.RetrieveAPIView):
    serializer_class = ApplicationOnExcursionSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsPartnerOrAdminForApplicationsOnExcursions]

    def get_queryset(self):
        user = self.request.user
        return ApplicationOnExcursion.objects.filter(excursion__owner=user)

    @swagger_auto_schema(
        operation_description="getting a specific application from a partner",
        responses={200: 'OK'},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class RewiewCreateView(generics.CreateAPIView):
    queryset = Review.objects.select_related('excursion', 'user', 'restaurant', 'hotel')
    serializer_class = ReviewSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsUser]

    def perform_create(self, serializer):
        user = self.request.user
        hotel_id = self.request.data.get('hotel', None)
        restaurant_id = self.request.data.get('restaurant', None)
        excursion_id = self.request.data.get('excursion', None)
        if hotel_id:
            existing_review = Review.objects.filter(hotel=hotel_id, user=user).first()
        elif restaurant_id is not None:
            existing_review = Review.objects.filter(restaurant=restaurant_id, user=user).first()
        elif excursion_id:
            existing_review = Review.objects.filter(excursion=excursion_id, user=user).first()
        else:
            existing_review = None

        if existing_review is not None:
            raise ValueError()
        if not existing_review:
            serializer.save(user=user)


class ReviewListView(generics.ListAPIView):
    queryset = Review.objects.select_related('excursion', 'user', 'restaurant', 'hotel')
    serializer_class = ReviewSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = ReviewFilter
    pagination_class = PageNumberPagination
    page_size = 1


class StatisticsView(APIView):
    """Получение статистики для админа по приложениям"""
    permission_classes = [IsAdmin]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        # Получаем количество всех пользователей
        count_users = User.objects.filter(role=1).count()

        # Получаем количество партнеров
        partners = User.objects.filter(role=3)
        count_partners = partners.count()

        # Получаем количество услуг каждого типа (экскурсии, рестораны, отели, транспорт)
        count_excursions = Excursion.objects.count()
        count_restaurants = Restaurant.objects.count()
        count_hotels = Hotel.objects.count()
        count_transport = Transport.objects.count()

        # Возвращаем данные в формате JSON
        data = {
            'count_users': count_users,
            'count_partners': count_partners,
            'count_excursions': count_excursions,
            'count_restaurants': count_restaurants,
            'count_hotels': count_hotels,
            'count_transport': count_transport
        }
        return Response(data)


class PartnerRegisterView(generics.CreateAPIView):
    """Регистрация партенров администратором"""
    permission_classes = [IsAdmin]
    serializer_class = AdminPartnerRegisterSerializer
    authentication_classes = [JWTAuthentication]

    def perform_create(self, serializer):
        if serializer.is_valid():
            serializer.save()
            # Отправка кода на почту
            email = self.request.data.get('email')
            password = self.request.data.get('password')
            send_registration_email.delay(email, password)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)


class PartnerProfileView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdmin]
    queryset = User.objects.filter(role=2)
    serializer_class = PartnerProfileSerializer
    authentication_classes = [JWTAuthentication]


class BlockedUser(generics.UpdateAPIView):
    permission_classes = [IsAdmin]
    queryset = User.objects.all()
    serializer_class = BlockUserSerializer
    authentication_classes = [JWTAuthentication]


class ApplicationUnblockListView(generics.ListAPIView):
    """Список заявок на разблокировку"""
    queryset = ApplicationUnblock.objects.all()
    permission_classes = [IsAdmin]
    serializer_class = ApplicationsUnblockSerializer
    authentication_classes = [JWTAuthentication]


class ApplicationUnblockCreateView(generics.CreateAPIView):
    """Создание заявки на разблокировку"""
    queryset = ApplicationUnblock.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ApplicationsUnblockSerializer
    authentication_classes = [JWTAuthentication]

    @swagger_auto_schema(
        request_body=None,
        responses={
            201: openapi.Response('OK'),
            403: openapi.Response('Forbidden'),
            404: openapi.Response('Not Found'),
        },)
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
        
    def perform_create(self, serializer):
        user = self.request.user

        if not user.blocked:
            return JsonResponse({'error': 'You are not blocked'}, status=status.HTTP_403_FORBIDDEN)
        serializer.save(user=user)


class ApplicationUnblockUpdateView(generics.UpdateAPIView):
    """Обновление статуса заявки на разблокировку"""

    queryset = ApplicationUnblock.objects.all()
    permission_classes = [IsAdmin]
    serializer_class = ApplicationsUnblockSerializer
    authentication_classes = [JWTAuthentication]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'status': openapi.Schema(type=openapi.TYPE_INTEGER),
            }
        ),
        responses={
            200: openapi.Response('OK'),
            400: openapi.Response('Bad Request'),
            401: openapi.Response('Unauthorized'),
            403: openapi.Response('Forbidden'),
            404: openapi.Response('Not Found'),
        },)
    def update(self, request, *args, **kwargs):
        application = self.get_object()
        application.status = request.data.get('status', application.status)
        if application.status == 2:
            user = application.user
            user.blocked = False
            user.save()
        application.save()
        return Response(status=status.HTTP_200_OK)


class InfoViewSet(ModelViewSet):
    queryset = Info.objects.all()
    serializer_class = InfoSerializer
    authentication_classes = [JWTAuthentication]  

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [IsAdmin]

        return [permission() for permission in permission_classes]


class ObjectsWithFalseStatusListView(generics.ListAPIView):
    """Получение всех объектов, которые нужно одобрить"""
    permission_classes = [IsAdmin]
    authentication_classes = [JWTAuthentication]
    serializer_class = AllModelsSerializer

    def get_queryset(self):
        objects_model1 = Hotel.objects.prefetch_related('owner', 'chat_room', 'type_room', 'facilities', 'services', 'photos').filter(status=False)
        objects_model2 = Restaurant.objects.prefetch_related('chat_room', 'owner', 'features', 'kitchen').filter(status=False)
        objects_model3 = Transport.objects.filter(status=False)
        objects_model4 = Excursion.objects.prefetch_related('inclusives', 'conditions', 'owner').filter(status=False)

        return {
            'Hotels': objects_model1,
            'Restaurants': objects_model2,
            'Transports': objects_model3,
            'Excursions': objects_model4,
        }
    
    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset)
        return Response(serializer.data)




@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'hotels': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID отеля'),
            'restaurants': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID ресторана'),
            'transport': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID транспорта'),
            'excursions': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID экскурсии'),
            'new_status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Новый статус'),
        },
    ),
    responses={
        200: 'Success - объект изменен',
        404: 'Not Found - объект с указанным ID не найден',
    }
)
@api_view(['POST'])
@permission_classes([IsAdmin])
@authentication_classes([JWTAuthentication])
def change_status(request):
    """изменние статуса заявки на добавление чего-то"""
    hotel_id = request.data.get('hotels')
    restaurant_id = request.data.get('restaurants')
    transport_id = request.data.get('transport')
    excursion_id = request.data.get('excursions')
    new_status = request.data.get('new_status')

    if hotel_id:
        try:
            hotel = Hotel.objects.get(id=hotel_id)
            hotel.status = new_status
            hotel.save()
        except Hotel.DoesNotExist:
            return Response({'error': 'Отель с указанным id не найден.'}, status=404)
    if restaurant_id:
        try:
            restaurant = Restaurant.objects.get(id=restaurant_id)
            restaurant.status = new_status
            restaurant.save()
        except Restaurant.DoesNotExist:
            return Response({'error': 'Ресторан с указанным id не найден.'}, status=404)
    if transport_id:
        try:
            transport = Transport.objects.get(id=transport_id)
            transport.status = new_status
            transport.save()
        except Transport.DoesNotExist:
            return Response({'error': 'Транспорт с указанным id не найден.'}, status=404)
    if excursion_id:
        try:
            excursion = Excursion.objects.get(id=excursion_id)
            excursion.status = new_status
            excursion.save()
        except Excursion.DoesNotExist:
            return Response({'error': 'Экскурсия с указанным id не найдена.'}, status=404)

    return Response({'success': 'changed'}, status=200)

class BaseUserInfoView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    @swagger_auto_schema(
        operation_description="Получает информацию о пользователях заданной роли.",
        operation_summary="Информация о пользователях по роли",
        responses={200: UserInfoSerializer(many=True)})

    def get(self, request):
        users = User.objects.filter(role=self.role)
        serializer = UserInfoSerializer(users, many=True)
        return Response(serializer.data)

# Представление для обычных пользователей
class UserUserInfoView(BaseUserInfoView):
    role = 1  # Роль для обычных пользователей

# Представление для партнеров
class PartnerUserInfoView(BaseUserInfoView):
    role = 2  # Роль для партнеров

# Представление для администраторов
class AdminUserInfoView(BaseUserInfoView):
    role = 3  # Роль для администраторов