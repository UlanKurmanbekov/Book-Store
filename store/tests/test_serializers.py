from django.contrib.auth.models import User
from django.db.models import Count, Case, When
from django.test import TestCase

from store.models import Book, UserBookRelation
from store.serializers import BookSerializer


class BookSerializerTestCase(TestCase):
    def test_ok(self):
        user1 = User.objects.create(username='user1')
        user2 = User.objects.create(username='user2')
        user3 = User.objects.create(username='user3')

        book1 = Book.objects.create(name='Test book 1', price=10, author_name='Author 1')
        book2 = Book.objects.create(name='Test book 2', price=20, author_name='Author 2')

        UserBookRelation.objects.create(user=user1, book=book1, like=True)
        UserBookRelation.objects.create(user=user2, book=book1, like=True)
        UserBookRelation.objects.create(user=user3, book=book1, like=True)

        UserBookRelation.objects.create(user=user1, book=book2, like=True)
        UserBookRelation.objects.create(user=user1, book=book2, like=True)
        UserBookRelation.objects.create(user=user1, book=book2, like=False)

        books = Book.objects.all().annotate(likes_count=Count(Case(When(userbookrelation__like=True, then=1)))).order_by('id')
        data = BookSerializer(books, many=True).data
        expected_data = [
            {
                'id': book1.id,
                'name': 'Test book 1',
                'price': '10.00',
                'author_name': 'Author 1',
                'likes_count': 3
            },
            {
                'id': book2.id,
                'name': 'Test book 2',
                'price': '20.00',
                'author_name': 'Author 2',
                'likes_count': 2,
            }
        ]

        self.assertEqual(expected_data, data)
