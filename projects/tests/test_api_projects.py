from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from ..models import Project, Question, Answer, Milestone, Task, TaskStatus
from ..constants import STAGE, QUESTION_GROUPS, QUESTION_TYPES
from accounts.models import User


class ProjectViewSetTests(APITestCase):
    """
    Tests for ProjectViewSet
    """
    def setUp(self):
        self.user1 = User.objects.create_user(
            email='qq44@qq.qq', password='adminadmin'
        )
        self.client.login(email=self.user1.email, password='adminadmin')

        self.user2 = User.objects.create_user(
            email='qq43@qq.qq', password='adminadmin'
        )

        self.project = Project.objects.create(
            owner=self.user1,
            title='title',
            stage=STAGE[0][0],
            is_visible=True,
            status='published'
        )
        self.milestone = Milestone.objects.create(
            project=self.project,
            title='milestone',
            description='milestone',
            date_start='2000-01-01T00:00:00Z',
            date_end='2000-12-12T00:00:00Z'
        )
        self.project_hidden = Project.objects.create(
            owner=self.user1,
            title='title hidden',
            stage=STAGE[0][0],
            is_visible=False
        )

        self.question1 = Question.objects.create(
            title='title 1',
            subtitle='subtitle 1',
            stage=STAGE[0][0],
            group=QUESTION_GROUPS[0][0],
            question_type=QUESTION_TYPES[0][0]
        )
        self.question2 = Question.objects.create(
            group=QUESTION_GROUPS[1][0],
            title='What is your surname?',
            question_type=QUESTION_TYPES[1][0]
        )
        Answer.objects.create(
            question=self.question1, project=self.project, response_text='text'
        )
        self.task_status = TaskStatus.objects.create(title='todo')
        self.task = Task.objects.create(
            milestone=self.milestone,
            owner=self.user1,
            title='task 1',
            status=self.task_status
        )
        Task.objects.create(
            milestone=self.milestone,
            owner=self.user1,
            parent_task=self.task,
            title='subtask 1',
            status=self.task_status
        )

        self.image = 'data:image/gif;base64,R0lGODlhPQBEAPeoAJosM//AwO/AwHVYZ/z595kzAP/s7P+goOXMv8+fhw/v739/f+8PD98fH/8mJl+fn/9ZWb8/PzWlwv///6wWGbImAPgTEMImIN9gUFCEm/gDALULDN8PAD6atYdCTX9gUNKlj8wZAKUsAOzZz+UMAOsJAP/Z2ccMDA8PD/95eX5NWvsJCOVNQPtfX/8zM8+QePLl38MGBr8JCP+zs9myn/8GBqwpAP/GxgwJCPny78lzYLgjAJ8vAP9fX/+MjMUcAN8zM/9wcM8ZGcATEL+QePdZWf/29uc/P9cmJu9MTDImIN+/r7+/vz8/P8VNQGNugV8AAF9fX8swMNgTAFlDOICAgPNSUnNWSMQ5MBAQEJE3QPIGAM9AQMqGcG9vb6MhJsEdGM8vLx8fH98AANIWAMuQeL8fABkTEPPQ0OM5OSYdGFl5jo+Pj/+pqcsTE78wMFNGQLYmID4dGPvd3UBAQJmTkP+8vH9QUK+vr8ZWSHpzcJMmILdwcLOGcHRQUHxwcK9PT9DQ0O/v70w5MLypoG8wKOuwsP/g4P/Q0IcwKEswKMl8aJ9fX2xjdOtGRs/Pz+Dg4GImIP8gIH0sKEAwKKmTiKZ8aB/f39Wsl+LFt8dgUE9PT5x5aHBwcP+AgP+WltdgYMyZfyywz78AAAAAAAD///8AAP9mZv///wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAEAAKgALAAAAAA9AEQAAAj/AFEJHEiwoMGDCBMqXMiwocAbBww4nEhxoYkUpzJGrMixogkfGUNqlNixJEIDB0SqHGmyJSojM1bKZOmyop0gM3Oe2liTISKMOoPy7GnwY9CjIYcSRYm0aVKSLmE6nfq05QycVLPuhDrxBlCtYJUqNAq2bNWEBj6ZXRuyxZyDRtqwnXvkhACDV+euTeJm1Ki7A73qNWtFiF+/gA95Gly2CJLDhwEHMOUAAuOpLYDEgBxZ4GRTlC1fDnpkM+fOqD6DDj1aZpITp0dtGCDhr+fVuCu3zlg49ijaokTZTo27uG7Gjn2P+hI8+PDPERoUB318bWbfAJ5sUNFcuGRTYUqV/3ogfXp1rWlMc6awJjiAAd2fm4ogXjz56aypOoIde4OE5u/F9x199dlXnnGiHZWEYbGpsAEA3QXYnHwEFliKAgswgJ8LPeiUXGwedCAKABACCN+EA1pYIIYaFlcDhytd51sGAJbo3onOpajiihlO92KHGaUXGwWjUBChjSPiWJuOO/LYIm4v1tXfE6J4gCSJEZ7YgRYUNrkji9P55sF/ogxw5ZkSqIDaZBV6aSGYq/lGZplndkckZ98xoICbTcIJGQAZcNmdmUc210hs35nCyJ58fgmIKX5RQGOZowxaZwYA+JaoKQwswGijBV4C6SiTUmpphMspJx9unX4KaimjDv9aaXOEBteBqmuuxgEHoLX6Kqx+yXqqBANsgCtit4FWQAEkrNbpq7HSOmtwag5w57GrmlJBASEU18ADjUYb3ADTinIttsgSB1oJFfA63bduimuqKB1keqwUhoCSK374wbujvOSu4QG6UvxBRydcpKsav++Ca6G8A6Pr1x2kVMyHwsVxUALDq/krnrhPSOzXG1lUTIoffqGR7Goi2MAxbv6O2kEG56I7CSlRsEFKFVyovDJoIRTg7sugNRDGqCJzJgcKE0ywc0ELm6KBCCJo8DIPFeCWNGcyqNFE06ToAfV0HBRgxsvLThHn1oddQMrXj5DyAQgjEHSAJMWZwS3HPxT/QMbabI/iBCliMLEJKX2EEkomBAUCxRi42VDADxyTYDVogV+wSChqmKxEKCDAYFDFj4OmwbY7bDGdBhtrnTQYOigeChUmc1K3QTnAUfEgGFgAWt88hKA6aCRIXhxnQ1yg3BCayK44EWdkUQcBByEQChFXfCB776aQsG0BIlQgQgE8qO26X1h8cEUep8ngRBnOy74E9QgRgEAC8SvOfQkh7FDBDmS43PmGoIiKUUEGkMEC/PJHgxw0xH74yx/3XnaYRJgMB8obxQW6kL9QYEJ0FIFgByfIL7/IQAlvQwEpnAC7DtLNJCKUoO/w45c44GwCXiAFB/OXAATQryUxdN4LfFiwgjCNYg+kYMIEFkCKDs6PKAIJouyGWMS1FSKJOMRB/BoIxYJIUXFUxNwoIkEKPAgCBZSQHQ1A2EWDfDEUVLyADj5AChSIQW6gu10bE/JG2VnCZGfo4R4d0sdQoBAHhPjhIB94v/wRoRKQWGRHgrhGSQJxCS+0pCZbEhAAOw=='
        self.spreadsheet = 'data:application/octet-stream;base64,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'
        self.diagram = '<mxGraphModel><root><mxCell id=“0”/><mxCell id=“1" parent=“0”/><mxCell id=“2" value=“sfddsfsdf” style=“fillColor=#7ED321 ;strokeColor=#FF0827 ;strokeWidth=1;fontSize=12;fontColor=#F8E71C ;;” vertex=“1” parent=“1"><mxGeometry x=“10” y=“10" width=“80” height=“80" as=“geometry”/></mxCell></root></mxGraphModel>'

    def test_post(self):
        """
        test for post request to project-list
        :return: 201
        """
        data = {
            'title': 'title',
            'stage': STAGE[0][0]
        }
        response = self.client.post(reverse('project-list'), data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Project.objects.get(pk=response.data['id']).owner, self.user1
        )
        self.assertEqual(response.data['title'], 'title')
        self.assertEqual(response.data['stage'], STAGE[0][0])

    def test_get(self):
        """
        test for get request to project-list and project-detail
        :return: 200
        """
        response = self.client.get(reverse('project-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data, [])

        self.client.login(email=self.user2.email, password='adminadmin')

        response = self.client.get(
            reverse('project-detail', args=[self.project.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.user1.userprofile.employees.add(self.user2)
        self.project.participants.add(self.user2)
        response = self.client.get(
            reverse('project-detail', args=[self.project.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_put(self):
        """
        test for put request to project-detail
        :return: 200
        """
        data = {
            'date_start': '2000-12-12'
        }
        response = self.client.put(
            reverse('project-detail', args=[self.project.pk]), data=data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['date_start'], '2000-12-12')

    def test_delete(self):
        """
        test for delete request to project-detail
        :return: 204
        """
        response = self.client.delete(
            reverse('project-detail', args=[self.project.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_get_published_list(self):
        """
        test for get request to project-published (list)
        :return: 200
        """
        response = self.client.get(reverse('project-published-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # On setUp we created 2 projects (visible and invisible)
        self.assertEqual(len(response.data), 1)

    def test_get_published_detail(self):
        """
        test for get request to project-published (detail)
        :return: 200
        """
        response = self.client.get(
            reverse('project-published-detail', args=[self.project.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'title')
        self.assertEqual(response.data['participants'], [])
        self.assertEqual(response.data['date_start'], None)
        self.assertEqual(response.data['date_end'], None)
        self.assertEqual(response.data['stage'], 'idea')
        self.assertEqual(response.data['progress'], 100)
        self.assertNotEqual(response.data['milestones'], [])
        self.assertTrue(isinstance(response.data['milestones'], list))
        self.assertNotEqual(response.data['owner'], {})
        self.assertTrue(isinstance(response.data['owner'], dict))

    def test_get_activity(self):
        """
        test for get request to project-activity
        :return: 200
        """
        response = self.client.get(
            reverse('project-activity', args=[self.project.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'title')
        self.assertNotEqual(response.data['feed'], [])
        self.assertTrue(isinstance(response.data['feed'], list))
        # FIXME: need recheck it because we change logic
        # self.assertNotEqual(response.data['processes'], [])
        # self.assertTrue(isinstance(response.data['processes'], list))

    def test_get_milestones(self):
        """
        test for get request to project-milestones
        :return: 200
        """
        response = self.client.get(
            reverse('project-milestones', args=[self.project.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data, [])
        self.assertTrue(isinstance(response.data, list))

    def test_post_answers(self):
        """
        test for post request to project-answers
        :return: 200
        """
        # create
        data = [
            {
                'response_text': 'foo1',
                'is_private': False,
                'question': self.question1.pk,
                'image': None,
                'diagram': None
            },
            {
                'response_text': 'foo2',
                'is_private': False,
                'question': self.question2.pk,
                'image': None,
                'diagram': None
            },
        ]
        response = self.client.post(
            reverse('project-answers', args=[self.project.pk]), data=data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data, [])
        self.assertTrue(isinstance(response.data, list))

        # update
        data = [
            {
                'response_text': 'bar1',
                'is_private': False,
                'question': self.question1.pk,
                'image': None,
                'diagram': None,
                'spreadsheet': None
            },
            {
                'response_text': 'bar2',
                'is_private': False,
                'question': self.question2.pk,
                'image': None,
                'diagram': None,
                'spreadsheet': None
            },
        ]
        response = self.client.post(
            reverse('project-answers', args=[self.project.pk]), data=data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data, [])
        self.assertTrue(isinstance(response.data, list))

        # with image
        data = [
            {
                'question': self.question2.pk,
                'image': self.image,
                'response_text': ''
            }
        ]
        response = self.client.post(
            reverse('project-answers', args=[self.project.pk]), data=data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            next(
                iter(
                    filter(lambda x: x['image'] is not None, response.data)
                )
            )['image'],
            self.image
        )

        # with spreadsheet
        data = [
            {
                'question': self.question2.pk,
                'image': '',
                'spreadsheet': self.spreadsheet,
                'response_text': ''
            }
        ]
        response = self.client.post(
            reverse('project-answers', args=[self.project.pk]), data=data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            next(
                iter(
                    filter(
                        lambda x: x['spreadsheet'] is not None, response.data
                    )
                )
            )['spreadsheet'],
            self.spreadsheet
        )

        # with diagram
        data = [
            {
                'question': self.question2.pk,
                'image': '',
                'spreadsheet': '',
                'response_text': '',
                'diagram': self.diagram
            }
        ]
        response = self.client.post(
            reverse('project-answers', args=[self.project.pk]), data=data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            next(
                iter(
                    filter(
                        lambda x: x['diagram'] is not None, response.data
                    )
                )
            )['diagram'],
            self.diagram
        )

    def test_get_answers(self):
        """
        test for get request to project-answers
        :return: 200
        """
        response = self.client.get(
            reverse('project-answers', args=[self.project.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data, [])
        self.assertTrue(isinstance(response.data, list))

    def test_get_answers_published(self):
        """
        test for get request to project-answers-published
        :return: 200
        """
        response = self.client.get(
            reverse('project-answers-published', args=[self.project.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data, [])
        self.assertTrue(isinstance(response.data, list))


class MilestoneViewSetTest(APITestCase):
    """
    Tests for MilestoneViewSet
    """
    def setUp(self):
        self.user = User.objects.create_user(
            email='qq27@qq.qq', password='adminadmin'
        )
        self.client.login(email=self.user.email, password='adminadmin')

        self.project = Project.objects.create(
            owner=self.user, title='title', stage=STAGE[0][0], is_visible=True
        )
        self.milestone = Milestone.objects.create(
            project=self.project,
            title='milestone',
            description='milestone',
            date_start='2000-01-01T00:00:00Z',
            date_end='2000-12-12T00:00:00Z'
        )

    def test_post(self):
        """
        test for post request to milestone-list
        :return: 201
        """
        data = {
            'project': self.project.pk,
            'title': 'title',
            'description': 'description',
            'date_start': '2000-12-12T00:00:00Z',
            'date_end': '2001-12-12T00:00:00Z'
        }
        response = self.client.post(reverse('milestone-list'), data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['project'], self.project.pk)
        self.assertEqual(response.data['title'], 'title')
        self.assertEqual(response.data['description'], 'description')
        self.assertEqual(response.data['date_start'], '2000-12-12T00:00:00Z')
        self.assertEqual(response.data['date_end'], '2001-12-12T00:00:00Z')

    def test_get(self):
        """
        test for get request to milestone-list and milestone-detail
        :return: 200
        """
        response = self.client.get(reverse('milestone-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data, [])
        self.assertTrue(isinstance(response.data, list))

        response = self.client.get(
            reverse('milestone-detail', args=[self.milestone.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_put(self):
        """
        test for put request to milestone-detail
        :return: 200
        """
        data = {
            'date_start': '2000-12-12T00:00:00Z'
        }
        response = self.client.put(
            reverse('milestone-detail', args=[self.milestone.pk]), data=data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['date_start'], '2000-12-12T00:00:00Z')

    def test_delete(self):
        """
        test for delete request to milestone-detail
        :return: 204
        """
        response = self.client.delete(
            reverse('milestone-detail', args=[self.milestone.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
