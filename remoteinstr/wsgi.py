"""
WSGI config for remoteinstr project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "remoteinstr.settings")

application = get_wsgi_application()

#from threading_django import tasks_threads
#t = tasks_threads.MiThread('Tareilla')
#t.start()
#~t.join()
