import json

from django.contrib.auth.models import User
from django.db.models import Count, Case, When, Avg
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APITestCase

from store.models import Book, UserBookRelation
from store.serializers import BookSerializer


class BooksAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username='test user')
        self.user2 = User.objects.create(username='not owner')
        self.book1 = Book.objects.create(name='Test book 1', price=10, author_name='Author 1', owner=self.user)
        self.book2 = Book.objects.create(name='Test book 2', price=20, author_name='Author 2', owner=self.user)
        self.book3 = Book.objects.create(name='Test book Author 1', price=20, author_name='Author 3', owner=self.user)

        UserBookRelation.objects.create(user=self.user, book=self.book1, like=True, rate=5)

    def test_get(self):
        url = reverse('book-list')

        response = self.client.get(url)

        books = Book.objects.all().annotate(
            likes_count=Count(Case(When(userbookrelation__like=True, then=1))),
            rating=Avg('userbookrelation__rate')
        )

        serializer_data = BookSerializer(books, many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)
        self.assertEqual(serializer_data[1]['rating'], '5.00')
        self.assertEqual(serializer_data[1]['likes_count'], 1)

    def test_get_filter(self):
        url = reverse('book-list')

        response = self.client.get(url, data={'price': 20})

        books = Book.objects.filter(id__in=[self.book2.id, self.book3.id]).annotate(
            likes_count=Count(Case(When(userbookrelation__like=True, then=1))),
            rating=Avg('userbookrelation__rate')
        )

        serializer_data = BookSerializer(books, many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_get_search(self):
        url = reverse('book-list')

        response = self.client.get(url, data={'search': 'Author 1'})

        books = Book.objects.filter(id__in=[self.book1.id, self.book3.id]).annotate(
            likes_count=Count(Case(When(userbookrelation__like=True, then=1))),
            rating=Avg('userbookrelation__rate')
        )

        serializer_data = BookSerializer(books, many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_get_ordering(self):
        url = reverse('book-list')

        response = self.client.get(url, data={'ordering': '-price'})
        books = Book.objects.all().annotate(
            likes_count=Count(Case(When(userbookrelation__like=True, then=1))),
            rating=Avg('userbookrelation__rate')
        ).order_by('-price')

        serializer_data = BookSerializer(books, many=True).data
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

        book = Book.objects.filter(id=self.book1.id).annotate(
            likes_count=Count(Case(When(userbookrelation__like=True, then=1))),
            rating=Avg('userbookrelation__rate')
        ).first()
        serializer_data = BookSerializer(book).data

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

    def test_update_not_owner_but_staff(self):
        self.user_staff = User.objects.create(username='staff', is_staff=True)
        url = reverse('book-detail', args=(self.book1.id,))
        data = {
            'name': self.book1.name,
            'price': 60,
            'author_name': self.book1.author_name
        }
        json_data = json.dumps(data)

        self.client.force_login(self.user_staff)

        response = self.client.put(url, data=json_data, content_type='application/json')

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.book1.refresh_from_db()
        self.assertEqual(60, self.book1.price)


class UserBookRelationTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username='user')
        self.user2 = User.objects.create(username='user2')
        self.book1 = Book.objects.create(name='Test book 1', price=10, author_name='Author 1', owner=self.user)
        self.book2 = Book.objects.create(name='Test book 2', price=20, author_name='Author 2')

    def test_like_and_bookmark(self):
        url = reverse('userbookrelation-detail', args=(self.book1.id,))

        data = {
            'like': True
        }
        json_data = json.dumps(data)

        self.client.force_login(self.user)
        response = self.client.patch(url, data=json_data, content_type='application/json')

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        relation = UserBookRelation.objects.get(user=self.user, book=self.book1)
        self.assertTrue(relation.like)

        data = {
            'in_bookmarks': True
        }
        json_data = json.dumps(data)

        response = self.client.patch(url, data=json_data, content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        relation = UserBookRelation.objects.get(user=self.user, book=self.book1)

        self.assertTrue(relation.in_bookmarks)

    def test_rate(self):
        url = reverse('userbookrelation-detail', args=(self.book1.id,))

        data = {
            'rate': 3
        }
        json_data = json.dumps(data)

        self.client.force_login(self.user)
        response = self.client.patch(url, data=json_data, content_type='application/json')

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        relation = UserBookRelation.objects.get(user=self.user, book=self.book1)
        self.assertEqual(3, relation.rate)

    def test_rate_wrong(self):
        url = reverse('userbookrelation-detail', args=(self.book1.id,))

        data = {
            'rate': 6
        }
        json_data = json.dumps(data)

        self.client.force_login(self.user2)
        response = self.client.patch(url, data=json_data, content_type='application/json')

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        relation = UserBookRelation.objects.get(user=self.user2, book=self.book1)
        self.assertEqual(None, relation.rate)
