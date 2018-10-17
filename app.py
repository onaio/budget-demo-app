"""
Simple budget mkononi demo app
"""
# -------------------
# Configuration
# -------------------

import os

from django.http import JsonResponse
from django.test import TestCase

from django_micro import configure, route, run

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_URL = '/static/'
DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    },
}

configure(locals(), django_admin=True)

# --------------------
# Views
# --------------------


@route('', name='index')
def show_index(request):
    """
    Main index view
    """
    return JsonResponse({'posts': "hello world"})

# --------------------
# Tests
# --------------------


class TestIndexView(TestCase):
    """
    Main Test class
    """

    def test_success(self):
        """
        Test that the main view works
        """
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)


# -------------------
# Expose application
# -------------------

application = run()
