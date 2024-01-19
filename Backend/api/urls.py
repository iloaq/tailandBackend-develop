from django.urls import path, include
from rest_framework import permissions, routers
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from .views import (
    CustomObtainAuthToken, ObjectsWithFalseStatusListView, PartnerProfileView, PartnerRegisterView, RegistrationView, SendEmailView,
    VerifyCodeView, UpdatePasswordView, HotelCreateView,
    HotelDeleteView, HotelListView, HotelRetrieveView,
    HotelUpdateView, RestaurantCreateView, RestaurantDeleteView,
    RestaurantListView, RestaurantRetrieveView, RestaurantUpdateView,
    NewsCreateView, NewsDeleteView, NewsListView, NewsRetrieveView,
    NewsUpdateView, TransportCreateView, TransportDeleteView,
    TransportListView, TransportRetrieveView, TransportUpdateView,
    FaqCreateView, FaqDeleteView, FaqListView, FaqRetrieveView, FaqUpdateView,
    RefreshTokenn, TripFolderListCreateAPIView,
    TripFolderRetrieveUpdateDestroyAPIView, FavoriteListAPIView, FavoriteCreateAPIView,
    FavoriteRetrieveUpdateDestroyAPIView, UserInfo, change_status, delete_user,
    FeaturesRetriveApiView, FeaturesListApiView, KitchenListApiView,
    KitchenRetriveApiView, ServiceListApiView, ServiceRetriveApiView,
    TypeRoomListApiView, TypeRoomRetriveApiView, FacilitiesListApiView,
    FacilitiesRetriveApiView, ExcursionListView, ExcursionCreateView,
    ExcursionDeleteView, ExcursionRetrieveView, ExcursionUpdateView,
    UserApplicationsView, UserCreateApplicationView, ApplicationUpdateStatus,
    PartnerApplicationListView, PartnerApplicationRetrieveView, DeleteFavoriteAPIView,
    RewiewCreateView, ReviewListView, StatisticsView, BlockedUser, ApplicationUnblockListView,
    ApplicationUnblockCreateView, ApplicationUnblockUpdateView, RentalServicesRetriveApiView, 
    RentalServicesListApiView, InclusiveListApiView, InclusiveRetriveApiView, 
    ConditionsListApiView, ConditionsRetriveApiView, InfoViewSet, UserUserInfoView, PartnerUserInfoView, AdminUserInfoView)


schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

router = routers.DefaultRouter()

router.register(r"info", InfoViewSet, basename="information")

urlpatterns = [

    path('token/refresh/', RefreshTokenn.as_view(), name='token_refresh'),

    path('login/', CustomObtainAuthToken.as_view(), name='login'),
    path('register/', RegistrationView.as_view(), name='registration'),
    path('users/delete/', delete_user),
    path('userinfo/', UserInfo.as_view(), name='get_user_info'),

    path('users/info/', UserUserInfoView.as_view(), name='user_info'),
    path('partners/info/', PartnerUserInfoView.as_view(), name='partner_info'),
    path('admins/info/', AdminUserInfoView.as_view(), name='admin_info'),

    path('sendcode/', SendEmailView.as_view(), name='send_code'),
    path('verifycode/', VerifyCodeView.as_view(), name='verifycode'),
    path('updatepassword/', UpdatePasswordView.as_view(), name='update_password'),

    path('hotels/', HotelListView.as_view(), name='hotel-list'),
    path('hotels/create/', HotelCreateView.as_view(), name='hotel-create'),
    path('hotels/<int:pk>/', HotelRetrieveView.as_view(), name='hotel-retrieve'),
    path('hotels/<int:pk>/update/', HotelUpdateView.as_view(), name='hotel-update'),
    path('hotels/<int:pk>/delete/', HotelDeleteView.as_view(), name='hotel-delete'),

    path('restaurants/', RestaurantListView.as_view(), name='restaurant-list'),
    path('restaurants/create/', RestaurantCreateView.as_view(), name='restaurant-create'),
    path('restaurants/<int:pk>/', RestaurantRetrieveView.as_view(), name='restaurant-retrieve'),
    path('restaurants/<int:pk>/update/', RestaurantUpdateView.as_view(), name='restaurant-update'),
    path('restaurants/<int:pk>/delete/', RestaurantDeleteView.as_view(), name='restaurant-delete'),

    path('faq/', FaqListView.as_view(), name='faq-list'),
    path('faq/create/', FaqCreateView.as_view(), name='faq-create'),
    path('faq/<int:pk>/', FaqRetrieveView.as_view(), name='faq-retrieve'),
    path('faq/<int:pk>/update/', FaqUpdateView.as_view(), name='faq-update'),
    path('faq/<int:pk>/delete/', FaqDeleteView.as_view(), name='faq-delete'),

    path('news/', NewsListView.as_view(), name='news-list'),
    path('news/create/', NewsCreateView.as_view(), name='news-create'),
    path('news/<int:pk>/', NewsRetrieveView.as_view(), name='news-retrieve'),
    path('news/<int:pk>/update/', NewsUpdateView.as_view(), name='news-update'),
    path('news/<int:pk>/delete/', NewsDeleteView.as_view(), name='news-delete'),

    path('transport/', TransportListView.as_view(), name='transport-list'),
    path('transport/create/', TransportCreateView.as_view(), name='transport-create'),
    path('transport/<int:pk>/', TransportRetrieveView.as_view(), name='transport-retrieve'),
    path('transport/<int:pk>/update/', TransportUpdateView.as_view(), name='transport-update'),
    path('transport/<int:pk>/delete/', TransportDeleteView.as_view(), name='transport-delete'),

    path('trip-folders/', TripFolderListCreateAPIView.as_view(), name='trip-folder-list-create'),
    path('trip-folders/<int:pk>/', TripFolderRetrieveUpdateDestroyAPIView.as_view(), name='trip-folder-retrieve-update-destroy'),
    path('favorites/', FavoriteListAPIView.as_view(), name='favorite-list'),
    path('favorites/create/', FavoriteCreateAPIView.as_view(), name='favorite-create'),
    path('favorites/<int:pk>/', FavoriteRetrieveUpdateDestroyAPIView.as_view(), name='favorite-retrieve-update-destroy'),
    path('favorites/delete/', DeleteFavoriteAPIView.as_view(), name='delete favorite'),

    path('features/', FeaturesListApiView.as_view(), name='list features'),
    path('features/<int:pk>/', FeaturesRetriveApiView.as_view(), name='retrive features'),

    path('kitchen/', KitchenListApiView.as_view(), name='list kitchen'),
    path('kitchen/<int:pk>/', KitchenRetriveApiView.as_view(), name='retrive kitchen'),

    path('service/', ServiceListApiView.as_view(), name='list service'),
    path('service/<int:pk>/', ServiceRetriveApiView.as_view(), name='retrive service'),

    path('typeroom/', TypeRoomListApiView.as_view(), name='list types of rooms'),
    path('typeroom/<int:pk>/', TypeRoomRetriveApiView.as_view(), name='retrive type room'),

    path('facilities/', FacilitiesListApiView.as_view(), name='list facilities'),
    path('facilities/<int:pk>/', FacilitiesRetriveApiView.as_view(), name='retrive facilities'),

    path('rental-services/', RentalServicesListApiView.as_view(), name='list rental services of transport'),
    path('rental-services/<int:pk>/', RentalServicesRetriveApiView.as_view(), name='retrive rental services of transport'),

    path('inclusives/', InclusiveListApiView.as_view(), name='list inclusives of excursion'),
    path('inclusive/<int:pk>/', InclusiveRetriveApiView.as_view(), name='retrive inclusive of excursion'),

    path('conditions/', ConditionsListApiView.as_view(), name='list conditions of excursion'),
    path('conditions/<int:pk>/', ConditionsRetriveApiView.as_view(), name='retrive condition of excursion'),

    path('excursions/', ExcursionListView.as_view(), name='list of excursions'),
    path('excursions/create/', ExcursionCreateView.as_view(), name='excursions-create'),
    path('excursions/<int:pk>/', ExcursionRetrieveView.as_view(), name='excursions-retrieve'),

    path('excursions/<int:pk>/update/', ExcursionUpdateView.as_view(), name='excursions-update'),
    path('excursions/<int:pk>/delete/', ExcursionDeleteView.as_view(), name='excursions-delete'),

    path('applications/', UserApplicationsView.as_view(), name='list of user applications'),
    path('applications/create/', UserCreateApplicationView.as_view(), name='create user application'),
    path('applications/<int:pk>/status/', ApplicationUpdateStatus.as_view(), name='update status'),
    path('applications/partner/', PartnerApplicationListView.as_view(), name='list of partner applications'),
    path('applications/partner/<int:pk>/', PartnerApplicationRetrieveView.as_view(), name='retrive partner application'),

    path('reviews/', ReviewListView.as_view(), name='list of reviews with filter'),
    path('reviews/create/', RewiewCreateView.as_view(), name='create review'),

    path('admin/statistics/', StatisticsView.as_view(), name='statistics for admin'),
    path('admin/partners/register/', PartnerRegisterView.as_view(), name='partner_register'),
    path('admin/partners/<int:pk>/', PartnerProfileView.as_view(), name='partner_profile'),
    path('admin/blockuser/<int:pk>/', BlockedUser.as_view(), name='block user'),
    path('admin/application-ublock/', ApplicationUnblockListView.as_view(), name='list of application on ublock'),
    path('application-ublock/create/', ApplicationUnblockCreateView.as_view(), name='create application on ublock'),
    path('admin/application-ublock/update/<int:pk>/', ApplicationUnblockUpdateView.as_view(), name='update application on unblock'),
    path('admin/applications-on-create/', ObjectsWithFalseStatusListView.as_view(), name="applications-on-create"),
    path('admin/applications-on-create/change-status/', change_status, name='ChangeStatus'),

    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
] + router.urls
