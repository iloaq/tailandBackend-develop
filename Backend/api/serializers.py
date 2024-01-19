import base64
from django.http import JsonResponse
from rest_framework import serializers
from rest_framework import status
from django.core.files.base import ContentFile

from users.models import User
from .models import (ApplicationUnblock, Hotel, Restaurant, Faq, News, Transport,
                     TripFolder, Favorite, Features, Kitchen, Service,
                     TypeRoom, Facilities, Excursion, Conditions, Inclusive,
                     ApplicationOnExcursion, Review, RentalServices, WorkingHours, Info)
from .validators import UserValidation
from chat.models import Room


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role']
        extra_kwargs = {'password': {'write_only': True}}


class UserInfoSerializer(serializers.ModelSerializer):
    """ДЛя получения полной информации о пользователе"""
    avatar = serializers.CharField(write_only=True, required=False, max_length=100000000)
    username = serializers.CharField(required=False)
    full_name = serializers.CharField(required=False)
    new_password = serializers.CharField(required=False)
    country_code = serializers.CharField(required=False)
    phone_code = serializers.CharField(required=False)
    phone_number = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone_number', 'avatar',
                  'full_name', 'new_password', 'phone_code', 'country_code', 'role', 'blocked']
        extra_kwargs = {'new_password': {'write_only': True}, 'role': {'read_only': True}, 'blocked': {'read_only': True}}

    def update(self, instance, validated_data):
        """Переопределение обнволения инфы"""
        full_name = validated_data.pop('full_name', None)
        new_password = validated_data.pop('new_password', None)
        new_email = validated_data.pop('email', None)
        new_avatar = validated_data.pop('avatar', None)
        new_phone = validated_data.pop('phone_number', None)
        new_country_code = validated_data.pop('country_code', None)
        new_phone_code = validated_data.pop('phone_code', None)

        if full_name:  # разбиение фулл нейм на два имени 
            first_name, last_name = full_name.split(' ')
            instance.first_name = first_name
            instance.last_name = last_name

        if new_password:  # обновление пароля и валидация
            if new_password == instance.password:
                raise UserValidation('Duplicate password', 'password', status_code=status.HTTP_409_CONFLICT)
            instance.password = new_password

        if new_email:  # обновление почты и валидация, проверка нет ли еше пользователей с такой почтой
            if User.objects.filter(email=new_email).exclude(id=instance.id).exists():
                raise UserValidation('Such a user already exists', 'email', status_code=status.HTTP_409_CONFLICT)
            instance.email = new_email

        if new_phone:  # то же, что и с почтой
            if User.objects.filter(phone_number=new_phone).exclude(id=instance.id).exists():
                raise UserValidation('Such a user already exists', 'phone_number', status_code=status.HTTP_409_CONFLICT)
            instance.phone_number = new_phone
            instance.phone_code = new_phone_code
            instance.country_code = new_country_code

        if new_avatar:  # При артуре делали через base64, в остальных местах по адекватному фотки грузятся
            avatar = self.process_avatar(new_avatar)
            instance.avatar.save('avatar.png', avatar)
        instance.save()
        return instance

    def process_avatar(self, avatar_data):
        # Раскодирование данных base64 в бинарные данные изображения
        decoded_avatar = base64.b64decode(avatar_data)
        return ContentFile(decoded_avatar, name='avatar.png')
    
    def validate_username(self, value):
        # Проверка, существует ли уже пользователь с заданным именем пользователя
        if User.objects.filter(username=value).exists():
            raise UserValidation('Duplicate Username', 'username', status_code=status.HTTP_409_CONFLICT)
        return value

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class UserRegisterSerializer(serializers.ModelSerializer):
    """сериализватор для регистрации пользоватешля"""
    full_name = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'full_name', 'username', 'password', 'phone_number', 'country_code', 'phone_code']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise UserValidation('A user with this email already exists', 'email', status_code=status.HTTP_409_CONFLICT)
        return value
    
    def validate_phone_number(self, value):
        if User.objects.filter(phone_number=value).exists():
            raise UserValidation('A user with this phone number already exists', 'phone_number', status_code=status.HTTP_409_CONFLICT)
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise UserValidation('A user with this username already exists', 'username', status_code=status.HTTP_409_CONFLICT)
        return value

    def create(self, validated_data):
        full_name = validated_data.pop('full_name')
        name = full_name.split(' ', 1)
        if len(name) < 2:
            raise UserValidation('first or last name not specified', 'full_name', status_code=status.HTTP_400_BAD_REQUEST)
        first_name, last_name = full_name.split(' ', 1)
        user = User.objects.create_user(first_name=first_name,
                                        last_name=last_name, **validated_data)
        return user
    

class WorkingHoursSerializer(serializers.ModelSerializer):
    """Сериализатор для рабочих часов"""
    class Meta:
        model = WorkingHours
        fields = '__all__'


class FeaturesSerializer(serializers.ModelSerializer):
    """
    Сериализатор фишек ресторана
    """
    class Meta:
        model = Features
        fields = ['name', 'id']


class KitchenSerializer(serializers.ModelSerializer):
    """
    Сериализатор кухни ресторана
    """
    class Meta:
        model = Kitchen
        fields = ['name', 'id']


class ServiceSerializer(serializers.ModelSerializer):
    """
    Сериализатор услуг отеля
    """
    class Meta:
        model = Service
        fields = ['name', 'id']


class TypeRoomSerializer(serializers.ModelSerializer):
    """
    Сериализатор типов номера
    """
    class Meta:
        model = TypeRoom
        fields = ['name', 'id']


class FacilitiesSerializer(serializers.ModelSerializer):
    """
    Сериализатор оснащенности номера
    """
    class Meta:
        model = Facilities
        fields = ['name', 'id']


class HotelSerializer(serializers.ModelSerializer):
    """сериализатор для отеля"""
    is_favorite = serializers.SerializerMethodField() # добавлен ли отель в избранное пользователем 
    photos = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField() # отзывы 
    workingDays = WorkingHoursSerializer(required=False)
    # distance = serializers.SerializerMethodField()

    class Meta:
        model = Hotel
        fields = ['name', 'description', 'chat_room', 'owner', 'promotion',
                  'image', 'rate', 'cost', 'location', 'is_favorite',
                  'type_room', 'facilities', 'services', 'id', 'countBeds', 'photos', 'reviews', 'latitude', 'longitude',
                  'workingDays', 'phone_number', 'status']
        extra_kwargs = {'chat_room': {'read_only': True},
                        'owner': {'read_only': True}, 'rate': {'read_only': True},
                        'description': {'required': False}, 'name': {'required': False}}

    def get_photos(self, obj):
        return [photo.photo.url for photo in obj.photos.all()]

    def get_is_favorite(self, obj):
        user = self.context['request'].user
        return obj.favorite_set.filter(user=user).exists()  # является ли объект избранным у пользователя
    
    def get_reviews(self, obj):
        reviews = Review.objects.filter(hotel=obj)
        serializer = ReviewSerializer(reviews, many=True)
        return serializer.data

    # говнокод благодаря артуру
    def update(self, instance, validated_data):
        working_days_data = validated_data.pop('workingDays', None)
        instance = super().update(instance, validated_data)
        
        if working_days_data:
            if instance.workingDays:
                # Обновляем данные объекта WorkingHours
                working_days_serializer = self.fields['workingDays']
                working_days_serializer.update(instance.workingDays, working_days_data)
            else:
                # Создаем новый объект WorkingHours и связываем его с отелем
                working_days_serializer = self.fields['workingDays']
                working_days = working_days_serializer.create(working_days_data)
                instance.workingDays = working_days
                instance.save()
        
        return instance
    
    def create(self, validated_data):
        working_days_data = validated_data.pop('workingDays', None)
        instance = super().create(validated_data)

        if working_days_data:
            if instance.workingDays:
                # Обновляем данные объекта WorkingHours
                working_days_serializer = self.fields['workingDays']
                working_days_serializer.update(instance.workingDays, working_days_data)
            else:
                # Создаем новый объект WorkingHours и связываем его с отелем
                working_days_serializer = self.fields['workingDays']
                working_days = working_days_serializer.create(working_days_data)
                instance.workingDays = working_days
                instance.save()
    
        return instance


    def partial_update(self, instance, validated_data):
        working_days_data = validated_data.pop('workingDays', None)
        instance = super().partial_update(instance, validated_data)
        
        if working_days_data:
            if instance.workingDays:
                # Обновляем данные объекта WorkingHours
                working_days_serializer = self.fields['workingDays']
                working_days_serializer.update(instance.workingDays, working_days_data)
            else:
                # Создаем новый объект WorkingHours и связываем его с отелем
                working_days_serializer = self.fields['workingDays']
                working_days = working_days_serializer.create(working_days_data)
                instance.workingDays = working_days
                instance.save()
        
        return instance
    
    # def get_distance(self, obj):
    #     # возвращает расстояние в километрах
    #     return round(obj.distance.km, 2)


class RestaurantSerializer(serializers.ModelSerializer):
    is_favorite = serializers.SerializerMethodField()
    photos = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()
    workingDays = WorkingHoursSerializer(required=False)

    class Meta:
        model = Restaurant
        fields = ['name', 'description', 'chat_room', 'owner', 'promotion',
                  'image', 'rate', 'cost', 'location', 'is_favorite',
                  'features', 'kitchen', 'photos', 'reviews', 'id', 'latitude', 'longitude', 'workingDays', 'phone_number', 'status']
        extra_kwargs = {'chat_room': {'read_only': True},
                        'owner': {'read_only': True}, 'rate': {'read_only': True},
                        'description': {'required': False}, 'name': {'required': False}}
        
    def get_photos(self, obj):
        return [photo.photo.url for photo in obj.photos.all()]
        
    def get_is_favorite(self, obj):
        user = self.context['request'].user
        return obj.favorite_set.filter(user=user).exists()
    
    def get_reviews(self, obj):
        reviews = Review.objects.filter(restaurant=obj)
        serializer = ReviewSerializer(reviews, many=True)
        return serializer.data
    
    def update(self, instance, validated_data):
        working_days_data = validated_data.pop('workingDays', None)
        instance = super().update(instance, validated_data)
        
        if working_days_data:
            if instance.workingDays:
                # Обновляем данные объекта WorkingHours
                working_days_serializer = self.fields['workingDays']
                working_days_serializer.update(instance.workingDays, working_days_data)
            else:
                # Создаем новый объект WorkingHours и связываем его с отелем
                working_days_serializer = self.fields['workingDays']
                working_days = working_days_serializer.create(working_days_data)
                instance.workingDays = working_days
                instance.save()
        
        return instance

    def partial_update(self, instance, validated_data):
        working_days_data = validated_data.pop('workingDays', None)
        instance = super().partial_update(instance, validated_data)
        
        if working_days_data:
            if instance.workingDays:
                # Обновляем данные объекта WorkingHours
                working_days_serializer = self.fields['workingDays']
                working_days_serializer.update(instance.workingDays, working_days_data)
            else:
                # Создаем новый объект WorkingHours и связываем его с отелем
                working_days_serializer = self.fields['workingDays']
                working_days = working_days_serializer.create(working_days_data)
                instance.workingDays = working_days
                instance.save()
        
        return instance
    
    def create(self, validated_data):
        working_days_data = validated_data.pop('workingDays', None)
        instance = super().create(validated_data)

        if working_days_data:
            if instance.workingDays:
                # Обновляем данные объекта WorkingHours
                working_days_serializer = self.fields['workingDays']
                working_days_serializer.update(instance.workingDays, working_days_data)
            else:
                # Создаем новый объект WorkingHours и связываем его с отелем
                working_days_serializer = self.fields['workingDays']
                working_days = working_days_serializer.create(working_days_data)
                instance.workingDays = working_days
                instance.save()
    
        return instance


class FaqSerializer(serializers.ModelSerializer):
    class Meta:
        model = Faq
        fields = '__all__'


class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = '__all__'


class TransportSerializer(serializers.ModelSerializer):
    is_favorite = serializers.SerializerMethodField()
    photos = serializers.SerializerMethodField()
    workingDays = WorkingHoursSerializer(required=False)

    class Meta:
        model = Transport
        fields = ['name', 'description', 'image', 'rate', 'location', 'owner',
                  'promotion', 'is_favorite', 'cost', 'photos', 'latitude', 'longitude', 'workingDays', 'status', 'id']
        extra_kwargs = {'rate': {'read_only': True}, 
                        'description': {'required': False}, 'name': {'required': False}}

    def get_is_favorite(self, obj):
        user = self.context['request'].user
        return obj.favorite_set.filter(user=user).exists()
    
    def get_photos(self, obj):
        return [photo.photo.url for photo in obj.photos.all()]
    
    def update(self, instance, validated_data):
        working_days_data = validated_data.pop('workingDays', None)
        instance = super().update(instance, validated_data)
        
        if working_days_data:
            if instance.workingDays:
                # Обновляем данные объекта WorkingHours
                working_days_serializer = self.fields['workingDays']
                working_days_serializer.update(instance.workingDays, working_days_data)
            else:
                # Создаем новый объект WorkingHours и связываем его с отелем
                working_days_serializer = self.fields['workingDays']
                working_days = working_days_serializer.create(working_days_data)
                instance.workingDays = working_days
                instance.save()
        
        return instance

    def partial_update(self, instance, validated_data):
        working_days_data = validated_data.pop('workingDays', None)
        instance = super().partial_update(instance, validated_data)
        
        if working_days_data:
            if instance.workingDays:
                # Обновляем данные объекта WorkingHours
                working_days_serializer = self.fields['workingDays']
                working_days_serializer.update(instance.workingDays, working_days_data)
            else:
                # Создаем новый объект WorkingHours и связываем его с отелем
                working_days_serializer = self.fields['workingDays']
                working_days = working_days_serializer.create(working_days_data)
                instance.workingDays = working_days
                instance.save()
        
        return instance
    
    def create(self, validated_data):
        working_days_data = validated_data.pop('workingDays', None)
        instance = super().create(validated_data)

        if working_days_data:
            if instance.workingDays:
                # Обновляем данные объекта WorkingHours
                working_days_serializer = self.fields['workingDays']
                working_days_serializer.update(instance.workingDays, working_days_data)
            else:
                # Создаем новый объект WorkingHours и связываем его с отелем
                working_days_serializer = self.fields['workingDays']
                working_days = working_days_serializer.create(working_days_data)
                instance.workingDays = working_days
                instance.save()
    
        return instance


class TripFolderSerializer(serializers.ModelSerializer):
    """Сериализатор папок для избранного"""
    class Meta:
        model = TripFolder
        fields = ['user', 'name', 'id', 'image', 'countFavorites']
        extra_kwargs = {'user': {'required': False}, 'countFavorites': {'read_only': True}}


class InclusiveSerializer(serializers.ModelSerializer):

    class Meta:
        model = Inclusive
        fields = '__all__'


class ConditionsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Conditions
        fields = '__all__'


class ExcursionSerializer(serializers.ModelSerializer):
    is_favorite = serializers.SerializerMethodField()
    photos = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()

    class Meta:
        model = Excursion
        fields = '__all__'

    def get_is_favorite(self, obj):
        user = self.context['request'].user
        return obj.favorite_set.filter(user=user).exists()
    
    def get_photos(self, obj):
        return [photo.photo.url for photo in obj.photos.all()]
    
    def get_reviews(self, obj):
        reviews = Review.objects.filter(excursion=obj)
        serializer = ReviewSerializer(reviews, many=True)
        return serializer.data


class ApplicationOnExcursionSerializer(serializers.ModelSerializer):
    """Заявки на экскурсии"""
    title = serializers.CharField(required=False, read_only=True) # поле для аннотирования(имя экскурсии в выдаче списка заявок)

    class Meta:
        model = ApplicationOnExcursion
        fields = '__all__'
        extra_kwargs = {'status': {'read_only': True}, 'user': {'required': False}}


class ApplicationUpdateStatus(serializers.ModelSerializer):
    """Обновление статуса заявки на разблокировку"""

    class Meta:
        model = ApplicationOnExcursion
        fields = ['id', 'status', 'rejection_reason']

    
class FavoriteListSerializer(serializers.ModelSerializer):
    """избранное"""
    hotels = HotelSerializer(many=True, required=False)
    restaurants = RestaurantSerializer(many=True, required=False)
    transport = TransportSerializer(many=True, required=False)
    excursions = ExcursionSerializer(many=True, required=False)

    class Meta:
        model = Favorite
        fields = ['hotels', 'folder', 'restaurants', 'transport', 'excursions', 'id']


class FavoriteCRUDSerializer(serializers.ModelSerializer):
    folder_name = serializers.SerializerMethodField()

    def get_folder_name(self, obj):
        return obj.folder.name

    class Meta:
        model = Favorite
        fields = ['hotels', 'folder', 'folder_name', 'restaurants', 'transport', 'excursions', 'id']


class RemoveFavoriteSerializer(serializers.Serializer):
    hotel_id = serializers.IntegerField(required=False)
    restaurant_id = serializers.IntegerField(required=False)
    transport_id = serializers.IntegerField(required=False)
    excursion_id = serializers.IntegerField(required=False)


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'
        extra_kwargs = {'user': {'required': False}}


class AdminPartnerRegisterSerializer(serializers.ModelSerializer):
    """Сериализатор для создания новых партнеров администратором"""
    full_name = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'full_name', 'password', 'role']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('A user with this email already exists')
        return value
    
    def validate_phone_number(self, value):
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError('A user with this phone number already exists')
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('A user with this username already exists')
        return value

    def create(self, validated_data):
        full_name = validated_data.pop('full_name')
        first_name, last_name = full_name.split(' ', 1)
        role = validated_data.pop('role')
        username = validated_data.pop('email')
        email = username
        user = User.objects.create_user(first_name=first_name,
                                        last_name=last_name, role=role, **validated_data, username=username, email=email)
        return user


class PartnerProfileSerializer(serializers.ModelSerializer):
    """получение партнеров"""
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'phone_number', 'country_code', 'phone_code', 'role']


class BlockUserSerializer(serializers.ModelSerializer):
    """Блокировка пользователя"""
    class Meta:
        model = User
        fields = ['id', 'blocked']


class ApplicationsUnblockSerializer(serializers.ModelSerializer):
    """заявка на разблокировку"""
    user = UserInfoSerializer()

    class Meta:
        model = ApplicationUnblock
        fields = ['id', 'status', 'user', 'rejection_reason']
        extra_kwargs = {'user': {'read_only': True}}


class RentalServicesSerializer(serializers.ModelSerializer):
    """Условия аренды"""
    class Meta:
        model = RentalServices
        fields = '__all__'


class InfoSerializer(serializers.ModelSerializer):
    """инфа о приложении"""
    class Meta:
        model = Info
        fields = '__all__'

#  заявки на создание объектов


class HotelStatusSerializer(serializers.ModelSerializer):
    owner = UserInfoSerializer()

    class Meta:
        model = Hotel
        fields = ['id', 'name', 'owner', 'status']
        extra_kwargs = {'name': {'read_only': True}, 'owner': {'read_only': True}}




class RestaurantStatusSerializer(serializers.ModelSerializer):
    owner = UserInfoSerializer()

    class Meta:
        model = Restaurant
        fields = ['id', 'name', 'owner', 'status']
        extra_kwargs = {'name': {'read_only': True}, 'owner': {'read_only': True}}


class ExcursionStatusSerializer(serializers.ModelSerializer):
    owner = UserInfoSerializer()

    class Meta:
        model = Excursion
        fields = ['id', 'name', 'owner', 'status']
        extra_kwargs = {'name': {'read_only': True}, 'owner': {'read_only': True}}


class TransportStatusSerializer(serializers.ModelSerializer):
    owner = UserInfoSerializer()

    class Meta:
        model = Transport
        fields = ['id', 'name', 'owner', 'status']
        extra_kwargs = {'name': {'read_only': True}, 'owner': {'read_only': True}}


class AllModelsSerializer(serializers.Serializer):
    """Получение всех объектов"""
    hotels = HotelStatusSerializer(many=True)
    restaurants = RestaurantStatusSerializer(many=True)
    transports = TransportStatusSerializer(many=True)
    excursions = ExcursionStatusSerializer(many=True)

    def to_representation(self, instance):
        request = self.context.get('request', None) 
        return {
            'hotels': HotelStatusSerializer(instance['Hotels'], many=True, context={'request': request}).data,
            'restaurants': RestaurantStatusSerializer(instance['Restaurants'], many=True, context={'request': request}).data,
            'transports': TransportStatusSerializer(instance['Transports'], many=True, context={'request': request}).data,
            'excursions': ExcursionStatusSerializer(instance['Excursions'], many=True, context={'request': request}).data,
        }