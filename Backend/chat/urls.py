from django.urls import path
from . import views

## это чисто для тестирования работы чата
urlpatterns = [
    path('room/<int:pk>/', views.room, name='room'),
    path('chats/', views.UserRoomsListAPIView.as_view(), name='chats')
]