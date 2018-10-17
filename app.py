"""
Simple budget mkononi demo app
"""
# -------------------
# Configuration
# -------------------

import json
import os
from decimal import Decimal

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

BUDGET_ALLOWED_TYPES = [
    1,  # tomatoes
    2,  # broilers
]

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

# --------------------
# Views
# --------------------


@route('', name='index')
def show_index(request):
    """
    Main index view
    """
    type_of_thing = request.GET.get('type')

    amt = request.GET.get('amount')
    if amt is not None and amt.isdigit():
        amt = int(amt)
    else:
        amt = 1

    if type_of_thing and type_of_thing.isdigit() and\
            int(type_of_thing) in BUDGET_ALLOWED_TYPES:
        if int(type_of_thing) == 1:
            budget = get_tomatoes_budget(acres=amt)
        elif int(type_of_thing) == 2:
            budget = get_broilers_budget(chickens=amt)

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
