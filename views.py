from django.shortcuts import render
from django.http.response import JsonResponse
from django.db.models import Q
from django.utils import timezone
from django.contrib import messages

from .models import Photo
from .forms import PhotoForm

from random import *


def photo_view(request):
    if 'session_photos' in request.session:
        request.session.pop('session_photos')
    return render(request, 'photo_elixir/photo.html')


def get_photo(request):
    now = timezone.now()

    session_photos = request.session.get('session_photos', [])
    all_photos = Photo.objects.all().exclude(pk__in=session_photos)
    if not all_photos.exists():
        session_photos = []
        all_photos = Photo.objects.all()

    photos = all_photos.filter(Q(last_shown=None))
    if not photos.exists():
        oldest_last_shown = all_photos.order_by('last_shown')[0].last_shown
        photos = all_photos.filter(last_shown=oldest_last_shown)

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
    session_photos.append(photo.pk)
    request.session['session_photos'] = session_photos
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
