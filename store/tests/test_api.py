from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from store.models import Book
from store.serializers import BookSerializer


class BooksAPITestCase(APITestCase):
    def setUp(self):
        self.book1 = Book.objects.create(name='Test book 1', price=10, author_name='Author 1')
        self.book2 = Book.objects.create(name='Test book 2', price=20, author_name='Author 2')
        self.book3 = Book.objects.create(name='Test book Author 1', price=20, author_name='Author 3')

    def test_get(self):
        url = reverse('book-list')

        response = self.client.get(url)
        serializer_data = BookSerializer([self.book1, self.book2, self.book3], many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

