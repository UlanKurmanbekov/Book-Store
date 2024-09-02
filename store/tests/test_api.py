import json

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APITestCase

from store.models import Book
from store.serializers import BookSerializer


class BooksAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username='test user')
        self.user2 = User.objects.create(username='not owner')
        self.book1 = Book.objects.create(name='Test book 1', price=10, author_name='Author 1', owner=self.user)
        self.book2 = Book.objects.create(name='Test book 2', price=20, author_name='Author 2', owner=self.user)
        self.book3 = Book.objects.create(name='Test book Author 1', price=20, author_name='Author 3', owner=self.user)

    def test_get(self):
        url = reverse('book-list')

        response = self.client.get(url)
        serializer_data = BookSerializer([self.book1, self.book2, self.book3], many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_get_filter(self):
        url = reverse('book-list')

        response = self.client.get(url, data={'price': 20})
        serializer_data = BookSerializer([self.book2, self.book3], many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_get_search(self):
        url = reverse('book-list')

        response = self.client.get(url, data={'search': 'Author 1'})
        serializer_data = BookSerializer([self.book1, self.book3], many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_get_ordering(self):
        url = reverse('book-list')

        response = self.client.get(url, data={'ordering': '-price'})
        serializer_data = BookSerializer([self.book2, self.book3, self.book1], many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_create(self):
        self.assertEqual(3, Book.objects.all().count())
        url = reverse('book-list')
        data = {
            'name': 'Programming in Python 3',
            'price': 600,
            'author_name': 'Mark Summerfield'
        }
        json_data = json.dumps(data)

        self.client.force_login(self.user)

        response = self.client.post(url, data=json_data, content_type='application/json')

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(4, Book.objects.all().count())
        self.assertEqual(self.user, Book.objects.last().owner)

    def test_update(self):
        url = reverse('book-detail', args=(self.book1.id,))
        data = {
            'name': self.book1.name,
            'price': 60,
            'author_name': self.book1.author_name
        }
        json_data = json.dumps(data)

        self.client.force_login(self.user)

        response = self.client.put(url, data=json_data, content_type='application/json')

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.book1.refresh_from_db()
        self.assertEqual(60, self.book1.price)

    def test_get_detail(self):
        url = reverse('book-detail', args=(self.book1.id,))

        serializer_data = BookSerializer(self.book1).data

        self.client.force_login(self.user)
        response = self.client.get(url)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_delete(self):
        self.assertEqual(3, Book.objects.all().count())
        url = reverse('book-detail', args=(self.book1.id,))

        self.client.force_login(self.user)
        response = self.client.delete(url)

        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertEqual(2, Book.objects.all().count())

    def test_update_not_owner(self):
        url = reverse('book-detail', args=(self.book1.id,))
        data = {
            'name': self.book1.name,
            'price': 60,
            'author_name': self.book1.author_name
        }
        json_data = json.dumps(data)

        self.client.force_login(self.user2)

        response = self.client.put(url, data=json_data, content_type='application/json')

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        expected_data = {
            'detail': ErrorDetail(
                string='You do not have permission to perform this action.',
                code='permission_denied'
            )
        }

        self.assertEqual(expected_data, response.data)
        self.book1.refresh_from_db()
        self.assertEqual(10, self.book1.price)

    def test_delete_not_owner(self):
        self.assertEqual(3, Book.objects.all().count())
        url = reverse('book-detail', args=(self.book1.id,))

        self.client.force_login(self.user2)
        response = self.client.delete(url)

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual(3, Book.objects.all().count())
        expected_data = {
            'detail': ErrorDetail(
                string='You do not have permission to perform this action.',
                code='permission_denied'
            )
        }

        self.assertEqual(expected_data, response.data)
