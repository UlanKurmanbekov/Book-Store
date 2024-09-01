from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from store.models import Book
from store.serializers import BookSerializer


class BooksAPITestCase(APITestCase):
    def test_get(self):
        book1 = Book.objects.create(name='Test book 1', price=10)
        book2 = Book.objects.create(name='Test book 2', price=20)

        url = reverse('book-list')

        response = self.client.get(url)
        serializer_data = BookSerializer([book1, book2], many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

