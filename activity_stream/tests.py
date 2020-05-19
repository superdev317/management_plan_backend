from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from rest_framework import status


class ActionStreamAnyListViewTests(APITestCase):
    """
    Tests for ActionStreamAnyListView
    """
    def test_get(self):
        """
        test for get request to reverse('actstream_list')
        :return: 200
        """
        response = self.client.get(reverse('actstream_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
