from django.urls import path
from . import consumers


websocket_urlpatterns = [
    path("ws/chat/", consumers.RoomConsumer.as_asgi()),
    path("ws/get_user_chat_list/", consumers.RoomConsumer.as_asgi()),
]