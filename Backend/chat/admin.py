from django.contrib import admin

from .models import Message, Room,UserRooms

admin.site.register(Message)
admin.site.register(Room)
admin.site.register(UserRooms)
