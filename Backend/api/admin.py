from django.contrib import admin

from .models import (Faq, News, Hotel, Photo, Restaurant,
                     Transport, TripFolder, Favorite,
                     Features, Excursion, ApplicationOnExcursion, Inclusive,
                     Conditions, Review, ApplicationUnblock, Facilities,
                     RentalServices, TypeRoom, Service, Kitchen, WorkingHours, Info)


class FaqAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'answer')


class NewsAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'content')


class HotelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description')


class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description')


class TransportAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description')


class TripFolderAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user')


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user',)


class ApplicationOnExcursionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'excursion', 'status')


admin.site.register(Faq, FaqAdmin)
admin.site.register(News, NewsAdmin)
admin.site.register(Hotel, HotelAdmin)
admin.site.register(Restaurant, RestaurantAdmin)
admin.site.register(Transport, TransportAdmin)
admin.site.register(TripFolder, TripFolderAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(Features)
admin.site.register(Excursion)
admin.site.register(ApplicationOnExcursion, ApplicationOnExcursionAdmin)
admin.site.register(Inclusive)
admin.site.register(Conditions)
admin.site.register(Review)
admin.site.register(ApplicationUnblock)
admin.site.register(Facilities)
admin.site.register(RentalServices)
admin.site.register(TypeRoom)
admin.site.register(Service)
admin.site.register(Kitchen)
admin.site.register(WorkingHours)
admin.site.register(Photo)
admin.site.register(Info)
