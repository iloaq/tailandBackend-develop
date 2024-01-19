from django.db import models

from users.models import User


class Room(models.Model):
    """Модель комнаты"""
    name = models.CharField(max_length=255, null=False, blank=False, unique=True)
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name="rooms")
    current_users = models.ManyToManyField(User, related_name="current_rooms", blank=True)

    def __str__(self):
        return f"Room({self.name} {self.host})"


class Message(models.Model):
    """модель сообщения"""
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="messages")
    text = models.TextField(max_length=500)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="messages")
    file = models.FileField(upload_to='uploads/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message({self.user} {self.room})"
    

class UserRooms(models.Model):
    """в целом, тоже можно забить"""
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.room
