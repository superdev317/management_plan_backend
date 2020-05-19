from django.test import tag

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from .models import Place
from accounts.models import User


class PlaceAddressAutocompliteListViewTests(APITestCase):
    """
    Tests for PlaceAddressAutocompliteListView
    """
    def setUp(self):
        self.user = User.objects.create_user(
            email='qq26@qq.qq', password='adminadmin'
        )
        self.client.login(email=self.user.email, password='adminadmin')

    @tag('address')
    def test_get(self):
        """
        test for get request to places_autocomplite
        :return: 200
        """
        response = self.client.get(reverse('places_autocomplite'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        places_count = Place.objects.count()

        response = self.client.get(
            '{}?q=New+York'.format(reverse('places_autocomplite'))
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data, [])
        self.assertTrue(isinstance(response.data, list))
        self.assertTrue(Place.objects.count() > places_count)
