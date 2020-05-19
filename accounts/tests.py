from django.test import tag
from django.test.testcases import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from .models import User, Specialization

import time


class UserManagementTest(TestCase):

    def test_users(self):
        """
        check if we can use email or phone as user ID
        """
        user = User.objects.create_user(email='test@test.com', password='1234')
        self.assertTrue(user)
        with self.assertRaises(ValueError):
            User.objects.create_user(email='test@test.com', password='1234')
        with self.assertRaises(ValueError):
            User.objects.create_user(password='123', is_active=True, is_staff=True)
        with self.assertRaises(ValueError):
            User.objects.create_user(username='test', password='test', is_active=True, is_staff=True)

        User.objects.create_user(phone='+14165550161', password='1234')
        with self.assertRaises(ValueError):
            User.objects.create_user(phone='+14165550161', password='1234')


class AuthLazyUserTokenViewTests(APITestCase):
    """
    Tests for AuthLazyUserTokenView
    """
    def test_get(self):
        """
        test for get request to lazy_user_token
        :return: 403
        """
        response = self.client.get(reverse('lazy_user_token'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post(self):
        """
        test for post request to lazy_user_token
        :return: 200 + token
        """
        response = self.client.post(reverse('lazy_user_token'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('token' in response.data)


class AuthLazyUserConvertViewTests(APITestCase):
    """
    Tests for AuthLazyUserConvertView
    """
    def test_get(self):
        """
        test for get request to lazy-user-list
        :return: 405
        """
        response = self.client.get(reverse('lazy_user_convert'))
        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_post(self):
        """
        test for post request to lazy-user-list
        :return: 201
        """
        response = self.client.post(reverse('lazy_user_token'))
        token = response.data['token']

        response = self.client.post(
            reverse('lazy_user_convert'),
            {'email': 'qq45@qq.qq', 'password': 'adminadmin'},
            **{'HTTP_AUTHORIZATION': 'JWT {0}'.format(token)}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.filter(email='qq45@qq.qq').count(), 1)


class AuthTokenGetTests(APITestCase):
    """
    Tests that check if we can get token
    """
    def setUp(self):
        User.objects.create_user(email='qq40@qq.qq', password='adminadmin')

    def test_email_token(self):
        """
        test get jwt token by email and password
        :return: dict
        """
        response = self.client.post(
            reverse('obtain_token'),
            data={'email': 'qq40@qq.qq', 'password': 'adminadmin'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('token' in response.data)

    def test_phone_token(self):
        """
        test get jwt token by phone and password (SMS code)
        :return: dict
        """
        response = self.client.post(
            reverse('otp_login'), data={'phone': '+14165550161'}
        )
        token = response.data['token']

        response = self.client.post(
            reverse('obtain_token'),
            data={'phone': '+14165550161', 'password': token}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('token' in response.data)


class TestRegisterAPI(TestCase):
    """
    test registration - sending post request to register url
    :return: 201
    """
    def setUp(self):
        self.client = APIClient()

    def tearDown(self):
        self.client.logout()
        User.objects.all().delete()

    def test_register_by_email(self):
        data = {'email': 'register@test.com'}
        response = self.client.post(reverse('register'), data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data['non_field_errors'], ['Please set password']
        )

        data = {'email': 'register@test.com', 'password': '123'}
        response = self.client.post(reverse('register'), data=data)
        self.assertTrue(response.status_code == status.HTTP_201_CREATED)
        self.assertTrue(self.client.login(
            email='register@test.com', password='123')
        )

        # check unique email
        response = self.client.post(reverse('register'), data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data['email'], ['This email has already been registered.']
        )

        # check if new user can login
        response = self.client.post(reverse('obtain_token'), data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('token' in response.data)


class OtpLoginViewTests(APITestCase):
    """
    Tests for OtpLoginView
    """
    def test_post(self):
        """
        test for post request to otp_login
        :return: 201
        """
        data = {'phone': '+41797752819'}
        response = self.client.post(reverse('otp_login'), data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['phone'], '+41797752819')
        self.assertTrue(
            self.client.login(
                phone=response.data['phone'], password=response.data['token']
            )
        )

        # try login again
        self.client.logout()
        time.sleep(2)
        response = self.client.post(reverse('otp_login'), data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['phone'], '+41797752819')
        self.assertTrue(
            self.client.login(
                phone=response.data['phone'], password=response.data['token']
            )
        )


class CurrentUserProfileViewTests(APITestCase):
    """
    Tests for CurrentUserProfileView
    """
    def setUp(self):
        self.user = User.objects.create_user(
            email='qq30@qq.qq', password='123'
        )
        self.user2 = User.objects.create_user(
            email='qqq30@qq.qq', password='123'
        )
        self.specialization = Specialization.objects.create(title='IT')
        self.photo = 'data:image/gif;base64,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'

    def test_get(self):
        """
        test for get request to current_user_profile
        :return: 200
        """
        response = self.client.get(reverse('current_user_profile'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_login(self.user)
        response = self.client.get(reverse('current_user_profile'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        keys = ['id', 'first_name', 'last_name', 'phone_number', 'address',
                'photo', 'passport_photo', 'driver_license_photo', 'role',
                'user_id', 'email', 'title', 'summary', 'specializations',
                'skills', 'educations', 'works', 'employees']
        self.assertTrue(all(x in response.data.keys() for x in keys))

    def test_put(self):
        """
        test for put request to current_user_profile
        :return: 201
        """
        self.client.force_login(self.user)

        data = {
            'first_name': 'Gomer',
            'last_name': 'Simpson',
            'role': 'creator',
            'title': 'Title',
            'specializations': [self.specialization.pk],
            'skills': [self.specialization.pk],
            'educations': [
                {
                    'date_start': '2017-07-17',
                    'date_end': '2017-07-17',
                    'degree': 'degree',
                    'school': 'school'
                }
            ],
            'works': [
                {
                    'date_start': '2017-07-17',
                    'date_end': '2017-07-17',
                    'company': 'company',
                    'position': 'position',
                    'description': 'description description'
                }
            ]
        }
        response = self.client.put(reverse('current_user_profile'), data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Gomer')
        self.assertEqual(response.data['last_name'], 'Simpson')
        self.assertEqual(response.data['address'], None)
        self.assertEqual(response.data['photo'], None)
        self.assertEqual(response.data['driver_license_photo'], None)
        self.assertEqual(response.data['passport_photo'], None)
        self.assertEqual(response.data['role'], 'creator')
        self.assertEqual(response.data['title'], 'Title')
        self.assertNotEqual(response.data['specializations'], [])
        self.assertTrue(isinstance(response.data['specializations'], list))
        self.assertNotEqual(response.data['skills'], [])
        self.assertTrue(isinstance(response.data['skills'], list))
        self.assertNotEqual(response.data['educations'], [])
        self.assertTrue(isinstance(response.data['educations'], list))
        self.assertNotEqual(response.data['works'], [])
        self.assertTrue(isinstance(response.data['works'], list))

        self.client.logout()
        data = {'phone': '+14236550152'}
        response = self.client.post(reverse('otp_login'), data=data)
        data = {'phone': '+14236550152', 'password': response.data['token']}
        response = self.client.post(reverse('obtain_token'), data=data)
        data = {'first_name': 'Bart'}
        response = self.client.put(
            reverse('current_user_profile'),
            data=data,
            **{'HTTP_AUTHORIZATION': 'JWT {0}'.format(response.data['token'])}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Bart')

    def test_put_photo(self):
        """
        test for put only photo and photo_bounds request to current_user_profile
        :return: 200
        """
        self.client.force_login(self.user)
        data = {
            'photo': self.photo,
            'photo_bounds': {'width': 10, 'height': 10, 'x': 10, 'y': 10}
        }
        response = self.client.put(reverse('current_user_profile'), data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data['photo'], '')
        self.assertTrue(isinstance(response.data['photo'], str))
        self.assertEqual(
            response.data['photo_bounds'],
            {'width': 10, 'height': 10, 'x': 10, 'y': 10}
        )

    def test_put_passport_photo(self):
        """
        test for put only passport_photo request to current_user_profile
        :return: 200
        """
        self.client.force_login(self.user)
        data = {'passport_photo': self.photo}
        response = self.client.put(reverse('current_user_profile'), data=data)
        self.assertNotEqual(response.data['passport_photo'], '')
        self.assertTrue(isinstance(response.data['passport_photo'], str))

    def test_put_driver_license_photo(self):
        """
        test for put only driver_license_photo request to current_user_profile
        :return: 200
        """
        self.client.force_login(self.user)
        data = {'driver_license_photo': self.photo}
        response = self.client.put(reverse('current_user_profile'), data=data)
        self.assertNotEqual(response.data['driver_license_photo'], '')
        self.assertTrue(isinstance(response.data['driver_license_photo'], str))

    def test_put_specializations(self):
        """
        test for put only specializations request to current_user_profile
        :return: 200
        """
        self.client.force_login(self.user)
        data = {
            'specializations': [self.specialization.pk]
        }
        response = self.client.put(reverse('current_user_profile'), data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data['specializations'], [])
        self.assertTrue(isinstance(response.data['specializations'], list))

    def test_put_skills(self):
        """
        test for put only skills request to current_user_profile
        :return: 200
        """
        self.client.force_login(self.user)
        data = {
            'skills': [self.specialization.pk]
        }
        response = self.client.put(reverse('current_user_profile'), data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data['skills'], [])
        self.assertTrue(isinstance(response.data['skills'], list))

    def test_put_educations(self):
        """
        test for put only educations request to current_user_profile
        :return: 200
        """
        self.client.force_login(self.user)
        data = {
            'educations': [
                {
                    'date_start': '2017-07-17',
                    'date_end': '2017-07-17',
                    'degree': 'degree',
                    'school': 'school'
                }
            ]
        }
        response = self.client.put(reverse('current_user_profile'), data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data['educations'], [])
        self.assertTrue(isinstance(response.data['educations'], list))

    def test_put_works(self):
        """
        test for put only works request to current_user_profile
        :return: 200
        """
        self.client.force_login(self.user)
        data = {
            'works': [
                {
                    'date_start': '2017-07-17',
                    'date_end': '2017-07-17',
                    'company': 'company',
                    'position': 'position',
                    'description': 'description description'
                }
            ]
        }
        response = self.client.put(reverse('current_user_profile'), data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data['works'], [])
        self.assertTrue(isinstance(response.data['works'], list))

    @tag('address')
    def test_put_address(self):
        """
        test for put only address request to current_user_profile
        :return: 200
        """
        self.client.force_login(self.user)

        data = {'address': 'qwerty qaz'}
        response = self.client.put(reverse('current_user_profile'), data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data['address'], ['Please enter correct address']
        )

        data = {
            'address': '1600 Amphitheatre Parkway Mountain View, CA 94043, United States'
        }
        response = self.client.put(reverse('current_user_profile'), data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['address'],
            'Google Bldg 42, 1600 Amphitheatre Pkwy, Mountain View, CA 94043, USA'
        )

    def test_put_email(self):
        """
        test for put only email request to current_user_profile
        :return: 200
        """
        self.client.force_login(self.user)

        data = {'email': 'aaaa'}
        response = self.client.put(reverse('current_user_profile'), data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data['email'], ['Enter a valid email address.']
        )

        data = {'email': 'new_email@domain.ltd'}
        response = self.client.put(reverse('current_user_profile'), data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'new_email@domain.ltd')

    def test_put_employees(self):
        """
        test for put only employees request to current_user_profile
        :return: 200
        """
        self.client.force_login(self.user)

        data = {'employees': [self.user2.pk]}
        response = self.client.put(reverse('current_user_profile'), data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['employees'], [self.user2.pk])


class CurrentUserEmployeesListViewTest(APITestCase):
    """
    Tests for CurrentUserEmployeesListView
    """
    def setUp(self):
        self.user1 = User.objects.create_user(
            email='qq50@qq.qq', password='123'
        )
        self.user2 = User.objects.create_user(
            email='qq51@qq.qq', password='123'
        )
        self.user1.userprofile.employees.add(self.user2)

    def test_get(self):
        """
        test for get request to current_user_employees_list
        :return: 200
        """
        self.client.force_login(self.user1)
        response = self.client.get(reverse('current_user_employees_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data, [])
        self.assertTrue(isinstance(response.data, list))
