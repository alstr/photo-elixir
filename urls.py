from django.urls import path

from . import views

app_name = 'photo_elixir'
urlpatterns = [
    path('', views.photo_view, name='photo_view'),
    path('get-photo/', views.get_photo, name='get_photo'),
    path('upload/', views.upload, name='upload')
]