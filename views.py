from datetime import timedelta

from django.shortcuts import render
from django.http.response import JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.contrib import messages
from django.db.models import Q

from .models import Photo
from .forms import PhotoForm

import feedparser
from geopy.distance import geodesic
import random
import re


HOME_LOCATION = (54.189053057612234, -3.204282818084613)

THEME_SCHEDULE = [
    (0, 'classic'),         # 00:00 - 02:00
    (2, 'travels'),         # 02:00 - 04:00
    (4, 'bermuda_triangle'),# 04:00 - 06:00
    (6, 'throwback'),       # 06:00 - 08:00
    (8, 'new_photos'),      # 08:00 - 10:00
    (10, 'random'),         # 10:00 - 12:00
    (12, 'classic'),        # 12:00 - 14:00
    (14, 'travels'),        # 14:00 - 16:00
    (16, 'bermuda_triangle'),#16:00 - 18:00
    (18, 'throwback'),      # 18:00 - 20:00
    (20, 'new_photos'),     # 20:00 - 22:00
    (22, 'random'),         # 22:00 - 24:00
]


def photo_view(request):
    if 'session_photos' in request.session:
        request.session.pop('session_photos')
    if 'last_weather_update' in request.session:
        request.session.pop('last_weather_update')

    return render(request, 'photo_elixir/photo.html')


def get_weather():
    curr_weather_feed = feedparser.parse('https://weather-broker-cdn.api.bbci.co.uk/en/observation/rss/2656908')
    temperature = 'Unavailable'
    if len(curr_weather_feed['entries']) > 0:
        curr_weather = curr_weather_feed['entries'][0]['summary']
        temperature_search = re.search(r'(?<=Temperature:\s)\S*', curr_weather)
        if temperature_search:
            temperature = temperature_search.group(0)

    forecast_weather_feed = feedparser.parse('https://weather-broker-cdn.api.bbci.co.uk/en/forecast/rss/3day/2656908')
    forecast = []
    if len(forecast_weather_feed['entries']) > 0:
        for entry in forecast_weather_feed['entries']:
            day_search = re.search(r'^[a-zA-z]+?(?=:)', entry['title'])
            summary_search = re.search(r'(?<=:\s).+?(?=,)', entry['title'])
            min_temp_search = re.search(r'(?<=Minimum Temperature:\s)\S*', entry['title'])
            max_temp_search = re.search(r'(?<=Maximum Temperature:\s)\S*', entry['title'])
            if day_search and summary_search and min_temp_search and max_temp_search:
                day = day_search.group(0)
                if day != 'Today':
                    day = day[:3]
                forecast.append({
                    'day': day,
                    'summary': summary_search.group(0),
                    'min_temp': min_temp_search.group(0),
                    'max_temp': max_temp_search.group(0)
                })
    return temperature, forecast

def get_current_and_next_theme():
    now = timezone.localtime()
    hour = now.hour

    current_index = 0
    for i, (start_hour, _) in enumerate(THEME_SCHEDULE):
        if hour >= start_hour:
            current_index = i
    current_theme = THEME_SCHEDULE[current_index]
    next_index = (current_index + 1) % len(THEME_SCHEDULE)
    next_theme = THEME_SCHEDULE[next_index]

    return current_theme, next_theme


def is_far(photo_location):
    if photo_location and photo_location.lat is not None and photo_location.lng is not None:
        dist = geodesic(HOME_LOCATION, (photo_location.lat, photo_location.lng)).km
        return dist > 500  # consider "travel" if > 500 km away
    return False


def filter_photos_by_theme(queryset, theme):
    now = timezone.now()
    today = now.date()
    if theme == 'new_photos':
        one_month_ago = now - timedelta(days=30)
        return queryset.filter(date_taken__gte=one_month_ago)
    elif theme == 'throwback':
        # Same day/month but previous years (exclude photos taken this year)
        return queryset.filter(
            date_taken__month=today.month,
            date_taken__day=today.day
        ).exclude(date_taken__year=today.year)
    elif theme == 'random':
        return queryset
    elif theme == 'classic':
        five_years_ago = now - timedelta(days=5*365)
        return queryset.filter(date_taken__lte=five_years_ago)
    elif theme == 'travels':
        # Filter photos with location, then filter in Python for distance
        photos_with_location = queryset.filter(
            location__lat__isnull=False,
            location__lng__isnull=False,
        )
        # Filter far photos in Python (geopy calculation)
        filtered = [p for p in photos_with_location if is_far(p.location)]
        return filtered
    elif theme == 'bermuda_triangle':
        return queryset.filter(
            Q(location__lat__isnull=True) | Q(location__lng__isnull=True) | Q(date_taken__isnull=True)
        )
    else:
        return queryset  # fallback no filtering


def get_photo(request):
    now = timezone.now()

    session_photos = request.session.get('session_photos', [])
    all_photos = Photo.objects.exclude(pk__in=session_photos)

    # Reset if exhausted
    if not all_photos.exists():
        session_photos = []
        all_photos = Photo.objects.all()

    current_theme, next_theme = get_current_and_next_theme()
    themed_photos = filter_photos_by_theme(all_photos, current_theme)

    # Handle if filtered result is list (e.g. travels theme) or QuerySet
    if isinstance(themed_photos, list):
        if not themed_photos:
            # fallback if no photos match theme
            themed_photos = list(all_photos)
        photo = random.choice(themed_photos)
    else:
        if not themed_photos.exists():
            themed_photos = all_photos.order_by('last_shown')[:20]
        photo = random.choice(list(themed_photos))

    photo.last_shown = now
    photo.save()

    session_photos.append(photo.pk)
    request.session['session_photos'] = session_photos[-100:]  # keep recent 100

    last_weather_update_str = request.session.get('last_weather_update')
    last_weather_update = parse_datetime(last_weather_update_str) if last_weather_update_str else None
    temperature, forecast = None, None
    if not last_weather_update or now - last_weather_update > timedelta(hours=1):
        temperature, forecast_raw = get_weather()
        forecast = render_to_string('photo_elixir/forecast-container-inner.html', {'forecast': forecast_raw})
        request.session['last_weather_update'] = now.isoformat()

    def format_theme_name(name):
        return name.replace('_', ' ').title()

    def format_theme_time(start_hour):
        end_hour = (start_hour + 2) % 24
        return f'{start_hour:02}:00 - {end_hour:02}:00'

    data = {
        'photo': photo.image.url,
        'current_theme_name': format_theme_name(current_theme[1]),
        'current_theme_time': format_theme_time(current_theme[0]),
        'next_theme_name': format_theme_name(next_theme[1]),
        'next_theme_time': format_theme_time(next_theme[0]),
        'temperature': temperature,
        'forecast': forecast
    }

    if photo.date_taken:
        data['date_taken'] = photo.format_date_taken()
    if photo.location and photo.location.lat is not None and photo.location.lng is not None:
        data['location'] = {'lat': photo.location.lat, 'lng': photo.location.lng}

    return JsonResponse(data)


def upload(request):
    if request.method == 'POST':
        form = PhotoForm(request.POST, request.FILES)
        if form.is_valid():
            files = request.FILES.getlist('image')
            for index, file in enumerate(files):
                photo = Photo(image=file)
                photo.save()
                print(f'Photo {index + 1} of {len(files)} created')
            messages.success(request, f'{len(files)} photo(s) added')
        else:
            messages.error(request, 'Form is not valid')
    else:
        form = PhotoForm()
    return render(request, 'photo_elixir/upload.html', {'form': form})
