from django.db import models
from django.core.files.uploadedfile import SimpleUploadedFile

from PIL import Image, ExifTags, ImageOps
from pillow_heif import register_heif_opener

from datetime import datetime
import os
from io import BytesIO
from zoneinfo import ZoneInfo
import mimetypes
import pytz


class Location(models.Model):
    lat = models.FloatField(blank=True, null=True, verbose_name='latitude')
    lng = models.FloatField(blank=True, null=True, verbose_name='longitude')

    def __str__(self):
        return f'{self.lat}, {self.lng}'


class Photo(models.Model):
    image = models.ImageField()
    date_taken = models.DateTimeField(blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)
    last_shown = models.DateField(blank=True, null=True)
    location = models.ForeignKey(Location, blank=True, null=True, on_delete=models.CASCADE)
    description = models.CharField(blank=True, null=True, max_length=100)

    def __str__(self):
        return os.path.split(self.image.file.name)[1]

    def save(self, *args, **kwargs):
        if not self.pk:
            register_heif_opener()

            file_stream = BytesIO()
            split_name = self.image.file.name.split('.')
            extension = split_name[len(split_name) - 1]

            if 'png' in extension.lower():
                img = Image.open(self.image).convert('RGBA')
            else:
                img = Image.open(self.image).convert('RGB')
            longest_side = max(img.size[0], img.size[1])
            side_limit = 1024
            if longest_side > side_limit:
                if img.size[0] > img.size[1]:
                    new_width = side_limit
                    new_height = int(round((side_limit / float(img.size[0])) * img.size[1]))
                else:
                    new_height = side_limit
                    new_width = int(round((side_limit / float(img.size[1])) * img.size[0]))

                img = img.resize((new_width, new_height), Image.ANTIALIAS)

            img = ImageOps.exif_transpose(img)
            img.save(file_stream, 'JPEG')
            file_stream.seek(0)
            split_name.pop()
            file_name = '_'.join(split_name) + '.' + extension
            content_type = mimetypes.guess_type(file_name)[0]
            self.image = SimpleUploadedFile(file_name, file_stream.read(), content_type=content_type)
            file_stream.close()

            img_exif = img.getexif()
            if img_exif is not None:
                data = {}

                for key, value in img_exif.items():
                    if key in ExifTags.TAGS:
                        data[ExifTags.TAGS[key]] = value

                gps_info = None
                for key, value in ExifTags.TAGS.items():
                    if value == "GPSInfo":
                        gps_info = img_exif.get_ifd(key)
                if gps_info is not None:
                    for key, value in gps_info.items():
                        data[ExifTags.GPSTAGS[key]] = value

                if 'GPSLatitude' in data and 'GPSLongitude' in data:
                    lat_info = data['GPSLatitude']
                    lat = lat_info[0] + (lat_info[1] / 60) + (lat_info[2] / 3600)
                    lng_info = data['GPSLongitude']
                    lng = lng_info[0] + (lng_info[1] / 60) + (lng_info[2] / 3600)
                    if data['GPSLatitudeRef'] == 'S':
                        lat = -lat
                    if data['GPSLongitudeRef'] == 'W':
                        lng = -lng
                    location = Location(lat=lat, lng=lng)
                    location.save()
                    self.location = location

                if 'DateTime' in data:
                    try:
                        date_taken = datetime.strptime(data['DateTime'], '%Y:%m:%d %H:%M:%S')
                        date_taken = date_taken.replace(tzinfo=ZoneInfo('Europe/London'))
                        self.date_taken = date_taken
                    except ValueError:
                        self.date_taken = None

        super(Photo, self).save(*args, **kwargs)

    def format_date_taken(self):
        if self.date_taken is not None:
            local_tz = pytz.timezone('Europe/London')
            date_taken_normalised = local_tz.normalize(self.date_taken.astimezone(local_tz))
            return date_taken_normalised.strftime('%a %d %b %Y, %H:%M')
        return 'No date'
