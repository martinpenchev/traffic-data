import re
import random
import string
from uuid import uuid4

from faker import Faker
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, ObjectDoesNotExist

from django.shortcuts import reverse
from rest_framework.test import APITestCase, APIRequestFactory

from rest_framework import status

from .models import Repository, TrafficEvent

class UserCreateEndpointTest(APITestCase):

    def setUp(self):
        self.url = reverse('api:user-create')
        self.fake = Faker()

    def test_user_create(self):
        initial_objects_count = get_user_model().objects.count()
        for i in range(0, 5):
            email = self.fake.email()
            response = self.client.post(self.url, {'email': email}, format="json")

            # API response
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue('token' in response.data)
            self.assertTrue(len(response.data) == 1)

            # User creation
            self.assertEqual(get_user_model().objects.count(), initial_objects_count + i + 1)
            try:
                get_user_model().objects.get(email=email)
            except ObjectDoesNotExist:
                raise ValueError
            self.assertEqual(get_user_model().objects.filter(email=email).values('token')[0]['token'], response.data.get('token'))

            # Try creating a user with the same email
            response = self.client.post(self.url, {'email': email}, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertTrue('error' in response.data)
            self.assertTrue(len(response.data) == 1)

            # Try sending some incorrect emails
            incorrect_emails = [
                re.sub(r'(\.[a-z]+\.?[a-z]*)', '', email),
                email.replace('@', '')
            ]
            for incorrect in incorrect_emails:
                response = self.client.post(self.url, {'email': incorrect}, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertTrue('error' in response.data)
                self.assertTrue(len(response.data) == 1)

class RepoEndpointTests(APITestCase):

    def setUp(self):
        self.list_url = reverse('api:repo-list')
        self.create_url = reverse('api:repo-create')
        self.get_url = lambda id: reverse('api:repo-detail', kwargs={"repository_id":id})
        self.delete_url = lambda id: reverse('api:repo-delete', kwargs={"repository_id":id})

        self.fake = Faker()

    def test_repo_list_endpoint(self):
        email = self.fake.email()
        self.client.post(reverse('api:user-create'), {'email': email}, format="json")
        user = get_user_model().objects.get(email=email)

        # Random github URL
        random_string = lambda: ''.join(random.choices(string.ascii_letters + string.digits + '_-', k=random.randint(5,10)))
        url = 'https://github.com/' + random_string() + '/' + random_string()
        repo = Repository.objects.create(url=url, user=user)

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        token = repo.user.token
        headers = {'HTTP_X_API_TOKEN':token}
        response = self.client.get(self.list_url, data={}, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data),1)

    def test_repo_create_endpoint(self):
        email = self.fake.email()
        self.client.post(reverse('api:user-create'), {'email': email}, format="json")
        user = get_user_model().objects.get(email=email)

        # Random github URL
        random_string = lambda: ''.join(random.choices(string.ascii_letters + string.digits + '_-', k=random.randint(5,10)))
        url = 'https://github.com/' + random_string() + '/' + random_string()
        auth_token = uuid4()

        data = {'url':url, 'auth_token':auth_token}
        response = self.client.post(self.create_url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Without token
        response = self.client.post(self.create_url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # With token
        token = user.token
        headers = {'HTTP_X_API_TOKEN':token}
        response = self.client.post(self.create_url, data=data, **headers)

        # Random repository --> github should return an error
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('error' in response.data)
        self.assertEqual(response.data['error'], 'Bad credentials')

    def test_repo_detail_endpoint(self):
        email = self.fake.email()
        self.client.post(reverse('api:user-create'), {'email': email}, format="json")
        user = get_user_model().objects.get(email=email)

        # Random github URL
        random_string = lambda: ''.join(random.choices(string.ascii_letters + string.digits + '_-', k=random.randint(5,10)))
        url = 'https://github.com/' + random_string() + '/' + random_string()
        repo = Repository.objects.create(url=url, user=user)
        id = repo.repository_id

        # Without token
        response = self.client.get(self.get_url(id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # With token
        token = user.token
        headers = {'HTTP_X_API_TOKEN':token}
        response = self.client.get(self.get_url(id), data={}, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Data check
        self.assertEqual(response.data['repository_id'], id)
        self.assertEqual(response.data['url'], url)
        self.assertTrue('traffic' in response.data)

    def test_repo_delete_endpoint(self):
        email = self.fake.email()
        self.client.post(reverse('api:user-create'), {'email': email}, format="json")
        user = get_user_model().objects.get(email=email)

        # Random github URL
        random_string = lambda: ''.join(random.choices(string.ascii_letters + string.digits + '_-', k=random.randint(5,10)))
        url = 'https://github.com/' + random_string() + '/' + random_string()
        repo = Repository.objects.create(url=url, user=user)
        id = repo.repository_id

        # Without token
        response = self.client.get(self.delete_url(id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # With token
        token = user.token
        headers = {'HTTP_X_API_TOKEN':token}
        response = self.client.delete(self.delete_url(id), data={}, **headers)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        # Check for deleted object
        with self.assertRaises(ObjectDoesNotExist):
            Repository.objects.get(repository_id=id)