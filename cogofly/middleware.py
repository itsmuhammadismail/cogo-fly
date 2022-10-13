from timezonefinder import TimezoneFinder
from django.utils import timezone

class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.tzfinder = TimezoneFinder()

    def __call__(self, request):
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            place = request.user.profile.place
            tz = self.tzfinder.timezone_at(lng=place.longitude, lat=place.latitude)
            timezone.activate(tz)
        return self.get_response(request)