from django.shortcuts import render
from django.http.response import JsonResponse
from django.db.models import Q
from django.utils import timezone
from django.contrib import messages

from .models import Photo
from .forms import PhotoForm

from random import *


def photo_view(request):
    return render(request, 'photo_elixir/photo.html')


def get_photo(request):
    now = timezone.now()

    photos = Photo.objects.filter(Q(last_shown=None))
    if not photos.exists():
        oldest_last_shown = Photo.objects.all().order_by('last_shown')[0].last_shown
        photos = Photo.objects.filter(last_shown=oldest_last_shown)

    random_index = randint(0, photos.count() - 1)
    photo = photos[random_index]
    data = {
        'photo': photo.image.url
    }
    if photo.date_taken is not None:
        data['date_taken'] = photo.format_date_taken()
    if photo.location is not None:
        data['location'] = {
            'lat': photo.location.lat,
            'lng': photo.location.lng
        }
    photo.last_shown = now
    photo.save()
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
