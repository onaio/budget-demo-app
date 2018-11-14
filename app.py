"""
Simple budget mkononi demo app
"""
# -------------------
# Configuration
# -------------------

import json
import os
from decimal import Decimal

from django.core.cache import cache
from django.http import JsonResponse
from django.test import TestCase

from django_micro import configure, route, run
from flatdict import FlatterDict
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_URL = '/static/'
DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    },
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/var/tmp/django_cache',
    }
}

BUDGET_ALLOWED_TYPES = [
    1,  # tomatoes
    2,  # broilers
]

BUDGET_API_URL = "https://budgetmkononi.com/en/budgeting/api/create/"
BUDGET_DELIMITER = "/"
BUDGET_CACHE_DURATION = 60 * 60 * 12

configure(locals(), django_admin=False)

# --------------------
# Functions
# --------------------


def get_budget_fixture(thing_being_farmed: int):
    """
    Gets the budget fixture for the thing being farmed
    """
    if thing_being_farmed == 1:
        path = os.path.join(BASE_DIR, 'fixtures', 'tomato-budget.json')
    elif thing_being_farmed == 2:
        path = os.path.join(BASE_DIR, 'fixtures', 'broiler-budget.json')
    else:
        return None

    with open(path, 'r') as budget_fixture:
        budget = json.load(budget_fixture)

    return budget


def get_quantity(item: dict):
    """
    Get the value of the quantity
    """
    qty = item.get('quantity')
    if isinstance(qty, dict):
        return Decimal(qty["value"])
    return Decimal(qty)


def update_quantity(item: dict, new_qty):
    """
    Get the value of the quantity
    """
    qty = item.get('quantity')
    if isinstance(qty, dict):
        item['quantity']['value'] = new_qty
    else:
        item['quantity'] = new_qty


def get_tomatoes_budget(acres: int = 1):
    """
    Calculates and returns tomatoes budget
    """
    budget = get_budget_fixture(thing_being_farmed=1)

    if acres > 1:
        # ratios of custom inputs
        ratios = {
            3: 7.2
        }

        for i, segment in enumerate(budget['segments']):
            for i2, activity in enumerate(segment['activities']):
                for i3, item in enumerate(activity['inputs']):
                    qty = get_quantity(item)
                    new_qty = qty * acres
                    update_quantity(item, new_qty)

                    new_price = acres * item['price']

                    if item['id'] in ratios.keys():
                        new_price = ratios[item['id']] * acres

                    item['estimated_price'] = new_price
                    item['price'] = new_price

    return budget


def get_broilers_budget(chickens: int = 1):
    """
    Calculates and returns broilers budget
    """
    budget = get_budget_fixture(thing_being_farmed=2)

    for i, segment in enumerate(budget['segments']):
        for i2, activity in enumerate(segment['activities']):
            for i3, item in enumerate(activity['inputs']):
                new_price = chickens * item['price']
                item['estimated_price'] = new_price
                item['price'] = new_price

    return budget


def get_budget_from_api(type_of_thing: int, qty: int):
    """
    Gets the budget from the API
    """
    payload = {"multiplier": qty}
    if type_of_thing == 1:
        payload["commodity"] = "tomatoes"
    elif type_of_thing == 2:
        payload["commodity"] = "broiler-chickens"
    else:
        return None

    cache_key = f"{type_of_thing}-{qty}"

    val_from_cache = cache.get(cache_key)
    if val_from_cache:
        return val_from_cache

    json_payload = json.dumps(payload)

    r = requests.post(BUDGET_API_URL, json_payload)

    if r.status_code == 200:
        result = r.json()['data']
        cache.set(
            cache_key,
            result,
            BUDGET_CACHE_DURATION
        )
        return result

    return None

# --------------------
# Views
# --------------------


@route('', name='index')
def show_index(request):
    """
    Main index view
    """
    segment = None
    type_of_thing = request.GET.get('type')

    amt = request.GET.get('amount')
    if amt is not None and amt.isdigit():
        amt = int(amt)
    else:
        amt = 1

    if type_of_thing and type_of_thing.isdigit() and\
            int(type_of_thing) in BUDGET_ALLOWED_TYPES:
        budget = None

        if request.GET.get('api'):
            budget = get_budget_from_api(
                type_of_thing=int(type_of_thing), qty=amt)
        else:
            if int(type_of_thing) == 1:
                budget = get_tomatoes_budget(acres=amt)
            elif int(type_of_thing) == 2:
                budget = get_broilers_budget(chickens=amt)

        segment = request.GET.get('segment')
        if segment and segment.isdigit():
            segment = int(segment)

            if budget is not None:
                try:
                    budget = budget['segments'][segment]
                except IndexError:
                    budget = None

        if budget is not None:
            if request.GET.get('flat'):
                flat_budget = FlatterDict(budget, delimiter=BUDGET_DELIMITER)

                return JsonResponse(dict(flat_budget))

            return JsonResponse(budget)

    return JsonResponse({"error": "Nothing here."})

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
