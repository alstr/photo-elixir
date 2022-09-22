Photo Elixir is a simple Django-based digital photo frame app for Raspberry Pi.

Features:

* Displays photos randomly with date/time stamp and GPS location
* Management command to import photos from a specified folder
* Upload photos from your local network by navigating to your Pi's IP address

The guide below explains how to install the app and set up your Pi to run the app on boot.

This guide uses the Django development server, which (security disclaimer) is not robust or intended for production usage, but for simple local use/testing only will suffice. For more elaborate usage, you should set up a production server.

# Setup

1. Copy app to Django project folder
2. Install requirements:
   ```
    Django==4.1.1
    Pillow==9.2.0
    pillow_heif==0.7.0
    pytz==2022.2.1
   ```
3. Update project's `urls.py`:
   ```
    urlpatterns = [
        path('', include('photo_elixir.urls')),
        path('admin/', admin.site.urls)
    ]
   ```
   See the Django documentation for updating `urls.py` to serve files in a development environment (`DEBUG = True`).
4. Update `settings.py`:
   ``` 
    ALLOWED_HOSTS = ['*']
   
    INSTALLED_APPS = [
       ...
       'photo_elixir.apps.PhotoElixirConfig'
    ]
   
    MIDDLEWARE = [
       ...
       'photo_elixir.middleware.timezone.TimezoneMiddleware'
    ]
   ```
5. Run `manage.py migrate`.
6. To start the server when the Pi boots, run `crontab -e` and add (adjusting the path as appropriate):
   ```
   @reboot /home/user/PhotoElixir/venv/bin/python3 /home/user/PhotoElixir/manage.py runserver 0.0.0.0:8000 > /home/user/cron_log.txt 2>&1
   ```
   To shut down the Pi at a specified time, run `sudo nano /etc/crontab` and add (adjusted to your desired time):
   ```
   05 22 * * * root shutdown -h now
   ```
7. To automatically display the web browser after login we need to create a script. It is suggested to use Midori browser over Chromium as it is more lightweight. Unclutter is required to hide the mouse cursor.

   ```
   sudo apt-get install midori
   sudo apt-get install unclutter
   ```
   After installing, run `sudo nano /home/user/start-browser.sh` and add:
   ```
   #!/bin/bash

   sleep 5

   unclutter -idle 0 &

   midori -e Fullscreen http://0.0.0.0:8000 &
   ```
   Then run `chmod u+x /home/user/start-browser.sh`.
8. Finally, update your autostart file to execute the script at login (allowing a short delay for the server to start) and disable any screensaver options. Run `sudo nano /etc/xdg/lxsession/LXDE-pi/autostart` and add:
   ```
   #@xscreensaver -no-splash
   @xset s off
   @xset noblank
   @xset -dpms
   @/home/user/start-browser.sh
   ```

### Performance

Although Django's development server is convenient, if using it for prolonged testing you may want to edit Django's `BaseDatabaseWrapper` class to set `force_debug_cursor` to `False` and disable query logging, which can be expensive.

On low memory Pi's (<=1GB), it can be helpful to enable the swap file on your Pi.

### Other considerations

Timezone is currently set to Europe/London but this could be moved into the settings file to allow for easier configuration.

### Hardware

This guide is based on a Raspberry Pi 4 Model B with 1GB memory and Waveshare 10.1" HDMI LCD touch screen display. 