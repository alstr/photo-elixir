import pytz

from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin


# noinspection PyUnusedLocal, PyMethodMayBeStatic
class TimezoneMiddleware(MiddlewareMixin):

    def process_request(self, request):
        tzname = 'Europe/London'
        if tzname:
            timezone.activate(pytz.timezone(tzname))
        else:
            timezone.deactivate()
