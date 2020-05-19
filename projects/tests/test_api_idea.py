from django.test import TestCase
from django.urls import reverse
from django.core.files.base import ContentFile

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from ..models import (
    Question, Answer, Project, TaskStatus, TaskTag, Task, TaskRule, Milestone,
    TaskDocument
)
from ..constants import QUESTION_GROUPS, QUESTION_TYPES, STAGE, DOCUMENT_TYPE
from accounts.models import User

from io import BytesIO


class IdeaQuestionsAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='test1@test.com', password='123', is_staff=False)
        self.project = Project.objects.create(owner=self.user, stage='idea')
        self.question = Question.objects.create(group=QUESTION_GROUPS[0][0],
                                           title='What is your name?',
                                           question_type=QUESTION_TYPES[0][0],
                                           stage='idea')
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
        response = self.client.post(reverse('idea-question-list'), data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Question.objects.count() > questions_count)

    def test_get(self):
        """
        test for get request to api:question-list and question-detail
        :return: 200
        """
        self.user = User.objects.get(email='test1@test.com')
        response = self.client.get(reverse('idea-question-list'))
        self.assertTrue(response.status_code == status.HTTP_403_FORBIDDEN, 'response.status_code is %d!' % response.status_code)

        response = self.client.get(reverse('idea-question-detail', kwargs={'pk': self.question.pk}))
        self.assertTrue(response.status_code == status.HTTP_403_FORBIDDEN, 'response.status_code is %d!' % response.status_code)

        self.client.login(email=self.user.email, password='123')
        response = self.client.get(reverse('idea-question-list'))
        self.assertTrue(response.status_code == status.HTTP_200_OK, 'response.status_code is %d!' % response.status_code)

        response = self.client.get(reverse('idea-question-detail', kwargs={'pk': self.question.pk}))
        self.assertTrue(response.status_code == status.HTTP_200_OK, 'response.status_code is %d!' % response.status_code)

        response = self.client.get(reverse('idea-question-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data, {})


class GanttProjectsListViewTests(APITestCase):
    """
    Tests for GanttProjectsListView
    """
    def setUp(self):
        self.user = User.objects.create_user(
            email='qq37@qq.qq', password='adminadmin'
        )
        self.client.login(email=self.user.email, password='adminadmin')
        Project.objects.create(
            owner=self.user, stage='idea',
            date_start='2000-01-01', date_end='2000-12-12'
        )

    def test_get(self):
        """
        test for get request to reverse('gantt_projects')
        :return: 200
        """
        response = self.client.get(reverse('idea_gantt_projects'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data, [])


class TaskViewSetTests(APITestCase):
    """
    Tests for TaskViewSet
    """
    def setUp(self):
        self.status = TaskStatus.objects.create(title='backlog')
        self.user1 = User.objects.create_user(
            email='qq39@qq.qq', password='adminadmin'
        )
        self.user2 = User.objects.create_user(
            email='qq38@qq.qq', password='adminadmin'
        )
        self.project = Project.objects.create(owner=self.user1, stage='idea')
        self.milestone = Milestone.objects.create(
            project=self.project,
            title='title',
            description='description',
            date_start='2000-01-01T00:00:00Z',
            date_end='2000-12-12T00:00:00Z'
        )
        self.task = Task.objects.create(
            milestone=self.milestone, owner=self.user1, title='title',
            description='description', status=self.status
        )
        self.tag = TaskTag.objects.create(title='tag')
        self.task.tags.add(self.tag)

    def test_get(self):
        """
        test for get request to idea-task-list and idea-task-detail
        :return: 200
        """
        self.client.login(email=self.user2.email, password='adminadmin')
        response = self.client.get(reverse('idea-task-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data, [])
        self.assertTrue(isinstance(response.data, list))

        self.client.login(email=self.user1.email, password='adminadmin')
        response = self.client.get(reverse('idea-task-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('idea-task-detail', args=[self.task.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post(self):
        """
        test for post request to idea-task-list
        :return: 201
        """
        self.client.login(email=self.user1.email, password='adminadmin')
        tags_count = TaskTag.objects.count()
        tasks_count = Task.objects.count()
        rules_count = TaskRule.objects.count()

        data = {
            'assignee': self.user1.pk,
            'complete_percent': 20,
            'due_date': '2000-12-12',
            'title': 'test title',
            'status': self.status.pk
        }
        response = self.client.post(reverse('idea-task-list'), data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = {
            'parent_task': None,
            'title': 'test title',
            'description': 'test description',
            'status': self.status.pk,
            'due_date': '2000-12-12',
            'complete_percent': 20,
            'milestone': self.milestone.pk,
            'assignee': self.user1.pk,
            'participants': [self.user1.pk],
            'tags': [
                {'title': 'tag1'},
                {'title': 'tag2'}
            ],
            'rules': [
                {'title': 'rule1'},
                {'title': 'rule2'}
            ]
        }
        response = self.client.post(reverse('idea-task-list'), data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(TaskTag.objects.count() > tags_count)
        self.assertTrue(Task.objects.count(), tasks_count)
        self.assertTrue(TaskRule.objects.count() > rules_count)

        # create sub-task
        task_id = response.data['id']
        data = {
            'parent_task': task_id,
            'milestone': self.milestone.pk,
            'title': 'sub title',
            'status': self.status.pk,
            'complete_percent': 20
        }
        response = self.client.post(reverse('idea-task-list'), data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_put(self):
        """
        test for put request to idea-task-detail
        :return: 200
        """
        self.client.login(email=self.user1.email, password='adminadmin')
        tags_count = TaskTag.objects.count()
        rules_count = TaskRule.objects.count()

        data = {
            'title': 'foo',
            'description': 'bar',
            'status': self.status.pk,
            'milestone': self.milestone.pk,
            'tags': [
                {'title': 'tag1'},
                {'title': 'tag2'}
            ],
            'rules': [
                {'title': 'rule3'},
                {'title': 'rule4'}
            ]
        }
        response = self.client.put(
            reverse('idea-task-detail', args=[self.task.pk]), data=data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(TaskTag.objects.count() > tags_count)
        self.assertTrue(self.task.tags.count(), 3)
        self.assertTrue(TaskRule.objects.count() > rules_count)
        self.assertEqual(
            response.data['rules'], [{'title': 'rule3'}, {'title': 'rule4'}]
        )

    def test_delete(self):
        """
        test for delete request to idea-task-detail
        :return: 204
        """
        self.client.login(email=self.user1.email, password='adminadmin')
        response = self.client.delete(
            reverse('idea-task-detail', args=[self.task.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_get_statuses(self):
        """
        test for get request to idea-task-statuses
        :return: 200
        """
        self.client.login(email=self.user1.email, password='adminadmin')
        response = self.client.get(reverse('idea-task-statuses'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data, [])
        self.assertTrue(isinstance(response.data, list))


class TaskDocumentViewSetTest(APITestCase):
    """
    Tests for TaskDocumentViewSet
    """
    def setUp(self):
        self.status = TaskStatus.objects.create(title='backlog')
        self.user1 = User.objects.create_user(
            email='qq52@qq.qq', password='adminadmin'
        )
        self.project = Project.objects.create(owner=self.user1, stage='idea')
        self.milestone = Milestone.objects.create(
            project=self.project,
            title='title',
            description='description',
            date_start='2000-01-01T00:00:00Z',
            date_end='2000-12-12T00:00:00Z'
        )
        self.task = Task.objects.create(
            milestone=self.milestone, owner=self.user1, title='title',
            description='description', status=self.status
        )
        self.subtask = Task.objects.create(
            milestone=self.milestone, owner=self.user1, title='sub title',
            description='sub description', status=self.status,
            parent_task=self.task
        )
        self.document = TaskDocument(
            task=self.subtask,
            doc_type=DOCUMENT_TYPE[0][0],
            name='some name',
            ext='img'
        )
        self.document.document.save(
            'myimage.jpg', ContentFile(b'mybinarydata')
        )
        self.document.save()
        self.client.force_login(self.user1)

    def test_post(self):
        """
        test for post request to idea-task-document-list
        :return: 201
        """
        img = BytesIO(b'mybinarydata')
        img.name = 'myimage.jpg'

        data = {
            'task': self.subtask.pk,
            'doc_type': DOCUMENT_TYPE[0][0],
            'name': 'myimage',
            'ext': 'jpg',
            'document': img
        }
        response = self.client.post(
            reverse('idea-task-document-list'),
            data=data,
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(response.data, {})
        self.assertTrue(isinstance(response.data, dict))

    def test_get(self):
        """
        test for get request to idea-task-document-list
        :return: 200
        """
        response = self.client.get(reverse('idea-task-document-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data, [])
        self.assertTrue(isinstance(response.data, list))

    def test_put(self):
        """
        test for put request to idea-task-document-detail
        :return: 200
        """
        data = {
            'name': 'new name'
        }
        response = self.client.patch(
            reverse('idea-task-document-detail', args=[self.document.pk]),
            data=data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'new name')

    def test_delete(self):
        """
        test for delete request to idea-task-document-detail
        :return: 204
        """
        response = self.client.delete(
            reverse('idea-task-document-detail', args=[self.document.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
