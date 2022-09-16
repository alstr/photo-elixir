from django.core.management.base import BaseCommand
from django.core.files.uploadedfile import SimpleUploadedFile

import os
import mimetypes

from photo_elixir.models import Photo


class Command(BaseCommand):
    help = 'Imports photos from the specified folder.'

    def add_arguments(self, parser):
        parser.add_argument('folder_path', type=str)

    def handle(self, *args, **options):
        folder_path = options['folder_path']
        folder_contents = os.listdir(folder_path)
        for file_name in folder_contents:
            if file_name == '.DS_Store':
                continue
            self.stdout.write(file_name)
            file_path = os.path.join(folder_path, file_name)
            file = open(file_path, 'rb')
            content_type = mimetypes.guess_type(file_path)[0]
            upload = SimpleUploadedFile(file_name, file.read(), content_type=content_type)
            photo = Photo(image=upload)
            photo.save()
