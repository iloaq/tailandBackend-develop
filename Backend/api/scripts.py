import random
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut


def generate_code():
    """генерация кода для отправки на почту при восстановлении пароля"""
    return random.randint(1000, 9999)


def get_city(latitude, longitude):
    """функций определения города"""
    geolocator = Nominatim(user_agent="tailand_app")
    try:
        location = geolocator.reverse((latitude, longitude))
        return location.raw['address']['city']
    except GeocoderTimedOut:
        return None