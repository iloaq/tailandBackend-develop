from django.shortcuts import render, get_object_or_404
from rest_framework.decorators import api_view
from rest_framework import generics, permissions
from rest_framework.views import APIView

from .serializers import UserRoomsSerializer

from .models import Room, Message, UserRooms
from users.models import User


## это чисто для тестирования работы чата

def room(request, pk):
    room: Room = get_object_or_404(Room, pk=pk)
    tokenn = request.GET.get('token', '')
    return render(request, 'room.html', {
        "room": room,
        "tokenn": tokenn,
    })


@api_view(['POST'])
def send_message(request):
    """тоже забей"""
    sender = request.user
    recipient = User.objects.get(id=request.data['recipient_id'])
    message = request.data['message']
    
    chat_message = ChatMessage(sender=sender, recipient=recipient, message=message)
    chat_message.save()
    
    return Response({'success': True})



class UserRoomsListAPIView(generics.ListAPIView):
    """тоже забей"""
    serializer_class = UserRoomsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return UserRooms.objects.filter(user=user)
