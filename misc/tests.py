from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from .models import Page, Message


class PageListViewTests(APITestCase):
    """
    Tests for PageListView
    """
    def setUp(self):
        Page.objects.create(
            various=Page.VARIOUS[0][0], title='title', description='some text'
        )

    def test_get(self):
        """
        test for get request to misc_page_list
        :return: 200
        """
        response = self.client.get(reverse('misc_page_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data, [])
        self.assertTrue(isinstance(response.data, list))


class MessageListViewTests(APITestCase):
    """
    Tests for MessageListView
    """
    def setUp(self):
        Message.objects.create(
            various=Page.VARIOUS[0][0], message='some message'
        )

    def test_get(self):
        """
        test for get request to misc_message_list
        :return: 200
        """
        response = self.client.get(reverse('misc_message_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data, [])
        self.assertTrue(isinstance(response.data, list))
