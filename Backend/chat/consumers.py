import json

from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from djangochannelsrestframework.generics import GenericAsyncAPIConsumer
from djangochannelsrestframework import mixins
from djangochannelsrestframework.observer.generics import (ObserverModelInstanceMixin, action)
from djangochannelsrestframework.observer import model_observer
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Room, Message, UserRooms
from .serializers import RoomSerializer, MessageSerializer
from ..api.serializers import UserSerializer
from ..users.models import User


class RoomConsumer(ObserverModelInstanceMixin, GenericAsyncAPIConsumer):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    lookup_field = "pk"

    async def connect(self):
        """Подключение к сокетам и аутентификация"""
        token = self.scope['query_string'].decode().split('=')[1]
        authentication = JWTAuthentication()
        validated_token = authentication.get_validated_token(token)
        user = await database_sync_to_async(authentication.get_user)(validated_token)
        self.user = user
        await self.accept()

    async def disconnect(self, code):
        """обработка отключения"""
        if hasattr(self, "room_subscribe"):
            await self.remove_user_from_room(self.room_subscribe)
            await self.notify_users()
        await super().disconnect(code)

    @action()
    async def join_room(self, pk, **kwargs):
        """подключение к комнате"""
        self.room_subscribe = pk
        # user_room, created = UserRooms.objects.get_or_create(user=self.user, room=pk)
        roommm = await database_sync_to_async(Room.objects.get)(
            id=pk
        )
        user_room, created = await database_sync_to_async(UserRooms.objects.get_or_create)(
            user=self.user,
            room=roommm
        )
        await self.add_user_to_room(pk)
        await self.notify_users()

    @action()
    async def leave_room(self, pk, **kwargs):
        await self.remove_user_from_room(pk)

    @action()
    async def create_message(self, message, file=None, **kwargs):
        if file is not None:
            await self.create_message_with_file(message, file)
        else:
            room: Room = await self.get_room(pk=self.room_subscribe)
            await database_sync_to_async(Message.objects.create)(
                room=room,
                user=self.user,
                text=message
            )

    @action()
    async def delete_message(self, pk, **kwargs):
        message = await self.get_message(pk)
        await database_sync_to_async(message.delete)()

    @action()
    async def subscribe_to_messages_in_room(self, pk, **kwargs):
        """подписка на события в чате"""
        await self.message_activity.subscribe(room=pk)

    @action()
    async def create_message_with_file(self, message, file, **kwargs):
        room: Room = await self.get_room(pk=self.room_subscribe)
        await database_sync_to_async(Message.objects.create)(
            room=room,
            user=self.user,
            text=message,
            file=file
        )

    @model_observer(Message)
    async def message_activity(self, message, observer=None, **kwargs):
        await self.send_json(message)

    @message_activity.groups_for_signal
    def message_activity(self, instance: Message, **kwargs):
        yield f'room__{instance.room_id}'
        yield f'pk__{instance.pk}'

    @message_activity.groups_for_consumer
    def message_activity(self, room=None, **kwargs):
        if room is not None:
            yield f'room__{room}'

    @message_activity.serializer
    def message_activity(self, instance: Message, action, **kwargs):
        return dict(data=MessageSerializer(instance).data, action=action.value, pk=instance.pk)

    async def notify_users(self):
        room: Room = await self.get_room(self.room_subscribe)
        for group in self.groups:
            await self.channel_layer.group_send(
                group,
                {
                    'type': 'update_users',
                    'users': await self.current_users(room)
                }
            )

    async def update_users(self, event: dict):
        await self.send(text_data=json.dumps({'users': event["users"]}))

    @database_sync_to_async
    def get_room(self, pk: int) -> Room:
        return Room.objects.get(pk=pk)

    @database_sync_to_async
    def current_users(self, room: Room):
        return [UserSerializer(user).data for user in room.current_users.all()]

    @database_sync_to_async
    def remove_user_from_room(self, room):
        user: User = self.user
        user.current_rooms.remove(room)

    @database_sync_to_async
    def add_user_to_room(self, pk):
        user: User = self.user
        if not user.current_rooms.filter(pk=self.room_subscribe).exists():
            user.current_rooms.add(Room.objects.get(pk=pk))

    @action()
    async def get_user_chat_list(self, **kwargs):
        """получение списка чатов"""
        user_rooms = await self.get_user_chat_rooms()
        chat_list = await self.get_chat_list(user_rooms)
        await self.send_json({"chat_list": chat_list})

    @database_sync_to_async
    def get_user_chat_rooms(self):
        return UserRooms.objects.filter(user=self.user)

    async def get_chat_list(self, user_rooms):
        chat_list = []
        for user_room in user_rooms:
            room = user_room.room
            last_message = await self.get_last_message(room)
            chat_list.append({
                'room_id': room.id,
                'room_name': room.name,
                'last_message': last_message.text if last_message else None
            })
        return chat_list

    async def get_last_message(self, room):
        last_message = await database_sync_to_async(
            Message.objects.filter(room=room).order_by('-created_at').first
        )()
        return last_message
