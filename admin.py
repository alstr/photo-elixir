from django.contrib import admin

from .models import *


class PhotoAdmin(admin.ModelAdmin):
    list_display = ['render_thumbnail_tag', 'date_taken', 'last_shown', 'date_added']
    fields = ['render_preview_tag', 'date_taken', 'last_shown', 'date_added', 'location', 'description']
    ordering = ['-date_added']
    readonly_fields = ['render_preview_tag', 'date_added']
    list_per_page = 5


admin.site.register(Location)
admin.site.register(Photo, PhotoAdmin)
