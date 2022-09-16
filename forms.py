from django import forms

from .models import Photo


class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ['image']
        labels = {
            'image': 'Photo(s)'
        }
        widgets = {
            'image': forms.FileInput(attrs={'multiple': True})
        }
