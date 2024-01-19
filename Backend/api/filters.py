import django_filters
from django.db.models import F, Func
from django.db import models
from django.db.models.functions import ACos, Sin, Cos, Radians
from rest_framework import filters

from .models import (
    Transport, ApplicationOnExcursion, Excursion, Inclusive, Conditions,
    Favorite, Kitchen, Features, Restaurant, Review, Hotel)


class TransportFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    location = django_filters.CharFilter(lookup_expr='icontains')
    promotion = django_filters.BooleanFilter()

    class Meta:
        model = Transport
        fields = ['name', 'description', 'location', 'promotion']


class ApplicationOnExcursionFilter(django_filters.FilterSet):
    """фильтр по статусу для заявок на экскурсии"""
    status = django_filters.NumberFilter(field_name='status')

    class Meta:
        model = ApplicationOnExcursion
        fields = ['status']


class FavoriteFilter(django_filters.FilterSet):
    """получение избранного для конкретной папки"""
    folder_id = django_filters.NumberFilter(field_name='folder_id')

    class Meta:
        model = Favorite
        fields = ['folder_id']


class TransportFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        """фильтр для транспорта"""
        name = request.query_params.get('name')
        description = request.query_params.get('description')
        location = request.query_params.get('location')
        promotion = request.query_params.get('promotion')

        if name:
            queryset = queryset.filter(name__icontains=name)
        if description:
            queryset = queryset.filter(description__icontains=description)
        if location:
            queryset = queryset.filter(location__icontains=location)
        if promotion:
            queryset = queryset.filter(promotion=promotion)

        return queryset

class RestaurantFilter(django_filters.FilterSet):
    location = django_filters.CharFilter(lookup_expr='icontains')
    promotion = django_filters.BooleanFilter()
    features = django_filters.ModelMultipleChoiceFilter(
        field_name='features__id',
        queryset=Features.objects.all(),
        to_field_name='id',
        conjoined=True
    )
    kitchen = django_filters.ModelMultipleChoiceFilter(
        field_name='kitchen__id',
        queryset=Kitchen.objects.all(),
        to_field_name='id',
        conjoined=True
    )
    min_cost = django_filters.NumberFilter(field_name='cost', lookup_expr='gte')
    max_cost = django_filters.NumberFilter(field_name='cost', lookup_expr='lte')

    class Meta:
        model = Restaurant
        fields = ['location', 'promotion', 'features', 'kitchen', 'min_cost', 'max_cost']
        ordering_fields = ['rate']


class ReviewFilter(django_filters.FilterSet):
    """фильтр для отзывов"""
    excursion = django_filters.ModelMultipleChoiceFilter(
        field_name='excursion__id',
        queryset=Excursion.objects.prefetch_related('inclusives', 'conditions', 'owner'),
        to_field_name='id',
        conjoined=True
    )
    restaurant = django_filters.ModelMultipleChoiceFilter(
        field_name='restaurant__id',
        queryset=Restaurant.objects.prefetch_related('chat_room', 'owner', 'features', 'kitchen'),
        to_field_name='id',
        conjoined=True
    )
    hotel = django_filters.ModelMultipleChoiceFilter(
        field_name='hotel__id',
        queryset=Hotel.objects.prefetch_related('owner', 'chat_room', 'type_room', 'facilities', 'services'),
        to_field_name='id',
        conjoined=True
    )

    class Meta:
        model = Review
        fields = ['excursion', 'restaurant', 'hotel']


class RestaurantFilter(filters.BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        """фильтр для ресторанов"""
        location = request.query_params.get('location')
        promotion = request.query_params.get('promotion')
        features = request.query_params.getlist('features')
        kitchen = request.query_params.getlist('kitchen')
        min_cost = request.query_params.get('min_cost')
        max_cost = request.query_params.get('max_cost')
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        min_rate = request.query_params.get('min_rate')

        if min_rate:
            queryset = queryset.filter(rate__gte=min_rate)
        if location:
            queryset = queryset.filter(location__icontains=location)
        if promotion:
            queryset = queryset.filter(promotion=promotion)
        if features:
            for i in features:
                queryset = queryset.filter(features__id__in=i)
        if kitchen:
            for i in kitchen:
                queryset = queryset.filter(kitchen__id__in=i)
        if min_cost:
            queryset = queryset.filter(cost__gte=min_cost)
        if max_cost:
            queryset = queryset.filter(cost__lte=max_cost)
        # вычисление расстояния  и сортировка по дистанции до объекта
        if lat and lng:
            queryset = Hotel.objects.annotate(distance=Func(
                ACos(
                    (
                        Sin(Func('latitude', function='RADIANS')) *
                        Sin(Func(lat, function='RADIANS'))
                    ) + 
                    (
                        Cos(Func('latitude', function='RADIANS')) *
                        Cos(Func(lat, function='RADIANS')) *
                        Cos(Func('longitude', function='RADIANS') - Func(lng, function='RADIANS'))
                    )
                ) * 6371, function='DEGREES')).order_by('distance')

        return queryset


class ExcursionFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        inclusives = request.query_params.getlist('inclusives')
        conditions = request.query_params.getlist('conditions')
        location = request.query_params.get('location')
        promotion = request.query_params.get('promotion')
        min_cost = request.query_params.get('min_cost')
        max_cost = request.query_params.get('max_cost')
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        min_rate = request.query_params.get('min_rate')

        if min_rate:
            queryset = queryset.filter(rate__gte=min_rate)
        if inclusives:
            for i in inclusives:
                queryset = queryset.filter(inclusives__id__in=i)
        if conditions:
            for i in conditions:
                queryset = queryset.filter(conditions__id__in=i)
        if location:
            queryset = queryset.filter(location__icontains=location)
        if promotion:
            queryset = queryset.filter(promotion=promotion)
        if min_cost:
            queryset = queryset.filter(cost__gte=min_cost)
        if max_cost:
            queryset = queryset.filter(cost__lte=max_cost)
        if lat and lng:
            queryset = Hotel.objects.annotate(distance=Func(
                ACos(
                    (
                        Sin(Func('latitude', function='RADIANS')) *
                        Sin(Func(lat, function='RADIANS'))
                    ) + 
                    (
                        Cos(Func('latitude', function='RADIANS')) *
                        Cos(Func(lat, function='RADIANS')) *
                        Cos(Func('longitude', function='RADIANS') - Func(lng, function='RADIANS'))
                    )
                ) * 6371, function='DEGREES')).order_by('distance')

        return queryset


class HotelFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        promotion = request.query_params.get('promotion')
        min_rate = request.query_params.get('min_rate')
        min_cost = request.query_params.get('min_cost')
        max_cost = request.query_params.get('max_cost')
        location = request.query_params.get('location')
        type_rooms = request.query_params.getlist('type_rooms')
        facilities = request.query_params.getlist('facilities')
        services = request.query_params.getlist('services')
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')

        if min_rate:
            queryset = queryset.filter(rate__gte=min_rate)
        if promotion:
            queryset = queryset.filter(promotion=promotion)
        if min_cost:
            queryset = queryset.filter(cost__gte=min_cost)
        if max_cost:
            queryset = queryset.filter(cost__lte=max_cost)
        if location:
            queryset = queryset.filter(location__icontains=location)
        if type_rooms:
            for i in type_rooms:
                queryset = queryset.filter(type_room__id__in=i)
        if facilities:
            for i in facilities:
                queryset = queryset.filter(facilities__id__in=i)
        if services:
            for i in services:
                queryset = queryset.filter(services__id__in=i)
        if lat and lng:
            queryset = Hotel.objects.annotate(distance=Func(
                ACos(
                    (
                        Sin(Func('latitude', function='RADIANS')) *
                        Sin(Func(lat, function='RADIANS'))
                    ) + 
                    (
                        Cos(Func('latitude', function='RADIANS')) *
                        Cos(Func(lat, function='RADIANS')) *
                        Cos(Func('longitude', function='RADIANS') - Func(lng, function='RADIANS'))
                    )
                ) * 6371, function='DEGREES')).order_by('distance')
 
        return queryset

