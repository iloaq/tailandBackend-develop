from django.db import models
from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver
from django.core.validators import RegexValidator

import datetime
from .validators import TimeFormatValidator

from users.models import User
from chat.models import Room


class Faq(models.Model):
    """Модель вопрос-ответ(FAQ)"""
    question = models.CharField(max_length=255)
    answer = models.TextField()

    def __str__(self):
        return self.question


class News(models.Model):
    """Модель новости"""

    title = models.CharField(max_length=255)
    content = models.TextField()
    date_created = models.DateField(null=True, blank=True)
    image = models.ImageField(null=True, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = 'News'


@receiver(pre_save, sender=News)
def set_date_created(sender, instance, **kwargs):
    """Сохраняет текущую дату при создании новости"""

    if not instance.pk:
        instance.date_created = datetime.date.today()  # год-месяц-день


class Features(models.Model):
    """Особенности ресторана"""
    name = models.CharField(max_length=50, unique=True, null=False)

    def __str__(self):
        return self.name


class Kitchen(models.Model):
    """Виды кухни в ресторанах"""
    name = models.CharField(max_length=50, unique=True, null=False)

    def __str__(self):
        return self.name
    

class Service(models.Model):
    """Услуги в отеле"""
    name = models.CharField(max_length=50, unique=True, null=False)

    def __str__(self):
        return self.name
    

class Facilities(models.Model):
    """Оснащенность отеля"""
    name = models.CharField(max_length=50, unique=True, null=False)

    def __str__(self):
        return self.name


class TypeRoom(models.Model):
    """Тип номера"""
    name = models.CharField(max_length=50, unique=True, null=False)

    def __str__(self):
        return self.name
    

class RentalServices(models.Model):
    """Условия аренды"""
    name = models.CharField(max_length=50, unique=True, null=False)

    def __str__(self):
        return self.name
    

class Photo(models.Model):
    photo = models.ImageField()


class WorkingHours(models.Model):
    """Рабочие часы"""
    time_pattern = r'^([01]\d|2[0-3]):([0-5]\d)-([01]\d|2[0-3]):([0-5]\d)$'
    time_validator = RegexValidator(time_pattern, 'Введите время в формате xx:xx-xx:xx.')
    monday = models.CharField(blank=True, null=True, validators=[time_validator])
    tuesday = models.CharField(blank=True, null=True, validators=[time_validator])
    wednesday = models.CharField(blank=True, null=True, validators=[time_validator])
    thursday = models.CharField(blank=True, null=True, validators=[time_validator])
    friday = models.CharField(blank=True, null=True, validators=[time_validator])
    saturday = models.CharField(blank=True, null=True, validators=[time_validator])
    sunday = models.CharField(blank=True, null=True, validators=[time_validator])

    def __str__(self):
        if Hotel.objects.filter(workingDays=self).exists():
            return Hotel.objects.get(workingDays=self).name
        else:
            return self.monday
        # elif Restaurant.objects.filter(workingDays=self).exists():
        #     return Restaurant.objects.filter(workingDays=self).name


class Hotel(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    chat_room = models.ForeignKey(Room, on_delete=models.CASCADE, null=True, blank=True)
    promotion = models.BooleanField(default=False)
    image = models.ImageField(null=True, blank=True)
    photos = models.ManyToManyField(Photo, blank=True, related_name='hotel_images')
    rate = models.FloatField(default=0)
    cost = models.IntegerField(default=0)
    cost_kids = models.IntegerField(default=0)
    location = models.CharField(max_length=50, null=True, blank=True)
    type_room = models.ManyToManyField(TypeRoom, blank=True)
    facilities = models.ManyToManyField(Facilities, blank=True)
    services = models.ManyToManyField(Service, blank=True)
    countBeds = models.IntegerField(default=0)
    latitude = models.FloatField(null=True, blank=True, verbose_name='широта')  # широта
    longitude = models.FloatField(null=True, blank=True, verbose_name='долгота')  # долгота
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
    workingDays = models.ForeignKey(WorkingHours, null=True, blank=True, on_delete=models.DO_NOTHING)
    status = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    

@receiver(pre_delete, sender=Hotel)
def delete_hotel_photos(sender, instance, **kwargs):
    """Сигнал для удаления связанных фоток"""
    instance.photos.all().delete()


class Restaurant(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    chat_room = models.ForeignKey(Room, on_delete=models.CASCADE, null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    promotion = models.BooleanField(default=False)
    image = models.ImageField(null=True, blank=True)
    photos = models.ManyToManyField(Photo, blank=True, related_name='restaurant_images')
    rate = models.FloatField(default=0)
    cost = models.IntegerField(default=0)
    cost_kids = models.IntegerField(default=0)
    location = models.CharField(max_length=50, null=True, blank=True)
    features = models.ManyToManyField(Features, blank=True, related_name='features_restaurant')
    kitchen = models.ManyToManyField(Kitchen, blank=True, related_name='kitchen_restaurant')
    latitude = models.FloatField(null=True, blank=True, verbose_name='широта')  # широта
    longitude = models.FloatField(null=True, blank=True, verbose_name='долгота')  # долгота
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
    workingDays = models.ForeignKey(WorkingHours, null=True, blank=True, on_delete=models.DO_NOTHING)
    status = models.BooleanField(default=False) # поле статус, одобрен ли объект администратором

    def __str__(self):
        return self.name
    

@receiver(pre_delete, sender=Restaurant)
def delete_restaurant_photos(sender, instance, **kwargs):
    instance.photos.all().delete()


class Transport(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(null=True, blank=True)
    photos = models.ManyToManyField(Photo, blank=True, related_name='transport_images')
    rate = models.FloatField(default=0)
    location = models.CharField(max_length=50, null=True, blank=True)
    promotion = models.BooleanField(default=False)
    RentalServices = models.ManyToManyField(RentalServices, blank=True, related_name='rental_services')
    cost = models.IntegerField(default=0)
    latitude = models.FloatField(null=True, blank=True, verbose_name='широта')  # широта
    longitude = models.FloatField(null=True, blank=True, verbose_name='долгота')  # долгота
    workingDays = models.ForeignKey(WorkingHours, null=True, blank=True, on_delete=models.DO_NOTHING)
    status = models.BooleanField(default=False) # поле статус, одобрен ли объект администратором
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name


@receiver(pre_delete, sender=Transport)
def delete_transport_photos(sender, instance, **kwargs):
    instance.photos.all().delete()

class TripFolder(models.Model):
    """
    Модель для папки избранного.
    """
    name = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(null=True, blank=True)
    countFavorites = models.IntegerField(default=0)
    
    def __str__(self):
        return self.name


class Favorite(models.Model):
    """
    Модель избранного
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    hotels = models.ManyToManyField(Hotel, null=True, blank=True)
    folder = models.ForeignKey(TripFolder, on_delete=models.CASCADE, blank=True, null=True)
    restaurants = models.ManyToManyField(Restaurant, null=True, blank=True)
    transport = models.ManyToManyField(Transport, null=True, blank=True)
    excursions = models.ManyToManyField('Excursion', null=True, blank=True)

    def __str__(self):
        return f'{self.user.username}'


# Создание обработчиков сигналов
@receiver(post_save, sender=Hotel)
def create_hotel_chat_room(sender, instance, created, **kwargs):
    """
    Создает комнату чата при создании отеля.
    """
    if created:
        room = Room.objects.create(name=f'hotel_{instance.id}', host=instance.owner)
        instance.chat_room = room
        instance.save()


@receiver(post_save, sender=Restaurant)
def create_restaurant_chat_room(sender, instance, created, **kwargs):
    """
    Создает комнату чата при создании ресторана.
    """
    if created:
        room = Room.objects.create(name=f'restaurant_{instance.id}', host=instance.owner)
        instance.chat_room = room
        instance.save()


class Inclusive(models.Model):
    """что включено в экскурсию"""
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Conditions(models.Model):
    """условия экскурсии"""
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Excursion(models.Model):
    """
    Модель эккурсий
    """
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    description = models.TextField()
    inclusives = models.ManyToManyField(Inclusive, blank=True)
    conditions = models.ManyToManyField(Conditions, blank=True)
    cost = models.IntegerField(default=0)
    cost_kids = models.IntegerField(default=0)
    image = models.ImageField(null=True, blank=True)
    photos = models.ManyToManyField(Photo, blank=True, related_name='excursion_images')
    rate = models.FloatField(default=0)
    location = models.CharField(max_length=50, null=True, blank=True)
    promotion = models.BooleanField(default=False)
    chat_room = models.ForeignKey(Room, on_delete=models.CASCADE, null=True, blank=True)
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
    status = models.BooleanField(default=False) # поле статус, одобрен ли объект администратором
    latitude = models.FloatField(null=True, blank=True, verbose_name='широта')  # широта
    longitude = models.FloatField(null=True, blank=True, verbose_name='долгота')  # долгота

    def __str__(self):
        return f'Name: {self.name}, owner: {self.owner.username}'


@receiver(post_save, sender=Excursion)
def create_excursion_chat_room(sender, instance, created, **kwargs):
    """
    Создает комнату чата при создании экскурсии.
    """
    if created:
        room = Room.objects.create(name=f'Excursion_{instance.id}', host=instance.owner)
        instance.chat_room = room
        instance.save()


@receiver(pre_delete, sender=Excursion)
def delete_excurtsion_photos(sender, instance, **kwargs):
    instance.photos.all().delete()


class ApplicationOnExcursion(models.Model):
    """
    Модель заявок на экскурсию
    """
    excursion = models.ForeignKey(Excursion, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    STATUS_CHOICES = (
        (1, 'Оплачено'),
        (2, 'Отклонена'),
        (3, 'На рассмотрении'),
        (4, 'Ожидание оплаты'),
    )

    status = models.IntegerField(choices=STATUS_CHOICES, default=3)
    countOfAdults = models.IntegerField(default=0)
    countOfKids = models.IntegerField(default=0)
    comment = models.TextField(blank=True, null=False)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Номер телефона должен быть в формате: '+999999999'. Максимальная длина - 15 символов."
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=15,
        blank=False
    )
    date = models.DateField(null=True, blank=True)
    total_amount = models.IntegerField(default=0)
    rejection_reason = models.TextField(null=True, blank=True)  # в случае отказа партнером в экскурсии


class Review(models.Model):
    """модель отзыва"""
    excursion = models.ForeignKey(Excursion, on_delete=models.CASCADE, null=True, blank=True, related_name='reviewsExcursions')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, null=True, blank=True, related_name='reviewsRestaurants')
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, null=True, blank=True, related_name='reviewsHotels')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """
        Переопределение сохранения для обновления 
        рейтинга объекта, на который написали отзыв
        """
        super().save(*args, **kwargs)

        if self.excursion:
            self.excursion.rate = self.calculate_average_rating(self.excursion.reviewsExcursions.all())
            self.excursion.save()
        elif self.restaurant:
            self.restaurant.rate = self.calculate_average_rating(self.restaurant.reviewsRestaurants.all())
            self.restaurant.save()
        elif self.hotel:
            self.hotel.rate = self.calculate_average_rating(self.hotel.reviewsHotels.all())
            self.hotel.save()

    def calculate_average_rating(self, reviews):
        total_rating = sum(review.rating for review in reviews)
        average_rating = total_rating / len(reviews) if len(reviews) > 0 else 0
        return average_rating

    def __str__(self):
        if self.excursion:
            return f'Review for Excursion: {self.excursion.name} by {self.user.username}'
        elif self.restaurant:
            return f'Review for Restaurant: {self.restaurant.name} by {self.user.username}'
        elif self.hotel:
            return f'Review for Hotel: {self.hotel.name} by {self.user.username}'
        else:
            return f'Review by {self.user.username}'
        

class ApplicationUnblock(models.Model):
    """заявка на разблокировку от пользователя, если его заблокировали"""
    APPLICATION_STATUS = (
        (1, 'Ожидает рассмотрения'),
        (2, 'Принята'),
        (3, 'Отклонена')
    )
    status = models.IntegerField(choices=APPLICATION_STATUS, default=1)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rejection_reason = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.user.username
    

class Info(models.Model):
    """Моедлька для информации о приложении"""
    description = models.TextField(null=True, blank=True)
    purpose_first = models.CharField(null=True, blank=True)
    purpose_second = models.CharField(null=True, blank=True)
    purpose_thrid = models.CharField(null=True, blank=True)
    contact_phone_first = models.CharField(null=True, blank=True)
    contact_name_first = models.CharField(null=True, blank=True)
    contact_phone_second = models.CharField(null=True, blank=True)
    contact_name_second = models.CharField(null=True, blank=True)

    def __str__(self):
        return f'contact name 1: {self.contact_name_first}, contact phone 1: {self.contact_phone_first}'
