from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from ..models import (
    Question, Answer, Project
)
from ..constants import QUESTION_GROUPS, QUESTION_TYPES, STAGE
from accounts.models import User


class StartupQuestionsAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='test1@test.com', password='123', is_staff=False)
        self.project = Project.objects.create(owner=self.user, stage='startup')
        self.question = Question.objects.create(group=QUESTION_GROUPS[0][0],
                                           title='What is your name?',
                                           question_type=QUESTION_TYPES[0][0],
                                           stage='startup')
        self.answer = Answer.objects.create(response_text='Andy', question=self.question, project=self.project)

    def tearDown(self):
        self.client.logout()

    def test_create(self):
        """
        test for create request to api:question-list
        :return: 201
        """
        self.client.login(email=self.user.email, password='123')
        questions_count = Question.objects.count()
        data = {
            'group': QUESTION_GROUPS[0][0],
            'title': 'test Q 1',
            'question_type': QUESTION_TYPES[0][0],
            'stage': STAGE[0][0]
        }
        response = self.client.post(
            reverse('startup-question-list'), data=data
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Question.objects.count() > questions_count)

    def test_get(self):
        """
        test for get request to api:question-list and question-detail
        :return: 200
        """
        self.user = User.objects.get(email='test1@test.com')
        response = self.client.get(reverse('startup-question-list'))
        self.assertTrue(response.status_code == status.HTTP_403_FORBIDDEN, 'response.status_code is %d!' % response.status_code)

        response = self.client.get(reverse('startup-question-detail', kwargs={'pk': self.question.pk}))
        self.assertTrue(response.status_code == status.HTTP_403_FORBIDDEN, 'response.status_code is %d!' % response.status_code)

        self.client.login(email=self.user.email, password='123')
        response = self.client.get(reverse('startup-question-list'))
        self.assertTrue(response.status_code == status.HTTP_200_OK, 'response.status_code is %d!' % response.status_code)

        response = self.client.get(reverse('startup-question-detail', kwargs={'pk': self.question.pk}))
        self.assertTrue(response.status_code == status.HTTP_200_OK, 'response.status_code is %d!' % response.status_code)

        response = self.client.get(reverse('startup-question-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data, {})
