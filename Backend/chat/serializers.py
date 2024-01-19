from rest_framework import serializers

from .models import Room, Message, UserRooms
from api.serializers import UserSerializer


class MessageSerializer(serializers.ModelSerializer):
    created_at_formatted = serializers.SerializerMethodField()
    file = serializers.FileField(allow_empty_file=True, required=False)
    user = UserSerializer()

    class Meta:
        model = Message
        exclude = []
        depth = 1

    def get_created_at_formatted(self, obj: Message):
        return obj.created_at.strftime("%d-%m-%Y %H:%M:%S")


class RoomSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Room
        fields = ["pk", "name", "host", "messages", "current_users", "last_message"]
        depth = 1
        read_only_fields = ["messages", "last_message"]

    def get_last_message(self, obj: Room):
        return MessageSerializer(obj.messages.order_by('created_at').last()).data
    

class RoomChatsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Room
        fields = ["pk", "name", "host"]


class UserRoomsSerializer(serializers.ModelSerializer):
    room = RoomChatsSerializer()

    class Meta:
        model = UserRooms
        fields = ['room', ]


class ChatListSerializer(serializers.Serializer):
    room_id = serializers.IntegerField()
    room_name = serializers.CharField()
    last_message = serializers.CharField()
