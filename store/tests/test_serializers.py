from django.contrib.auth.models import User
from django.db.models import Count, Case, When, Avg, F, DecimalField, ExpressionWrapper
from django.test import TestCase

from store.models import Book, UserBookRelation
from store.serializers import BookSerializer


class BookSerializerTestCase(TestCase):
    def test_ok(self):
        user1 = User.objects.create(username='user1', first_name='Sultan', last_name='Sulaimanov')
        user2 = User.objects.create(username='user2', first_name='Ulan', last_name='Kurmanbekov')
        user3 = User.objects.create(username='user3', first_name='Marlen', last_name='Melsov')

        book1 = Book.objects.create(name='Test book 1', price=10, author_name='Author 1', owner=user1)
        book2 = Book.objects.create(name='Test book 2', price=20, author_name='Author 2', discount=10)

        UserBookRelation.objects.create(user=user1, book=book1, like=True, rate=5)
        UserBookRelation.objects.create(user=user2, book=book1, like=True, rate=5)
        UserBookRelation.objects.create(user=user3, book=book1, like=True, rate=4)

        UserBookRelation.objects.create(user=user1, book=book2, like=True)
        UserBookRelation.objects.create(user=user2, book=book2, like=True, rate=4)
        UserBookRelation.objects.create(user=user3, book=book2, like=False, rate=2)

        books = Book.objects.all().annotate(
            likes_count=Count(Case(When(userbookrelation__like=True, then=1))),
            rating=Avg('userbookrelation__rate'),
            discounted_price=ExpressionWrapper(
                F('price') * (1 - F('discount') / 100.0),
                output_field=DecimalField()
            )
        ).order_by('id')
        data = BookSerializer(books, many=True).data
        expected_data = [
            {
                'id': book1.id,
                'name': 'Test book 1',
                'price': '10.00',
                'author_name': 'Author 1',
                'likes_count': 3,
                'rating': '4.67',
                'discounted_price': '10.00',
                'owner_name': user1.username,
                'readers': [
                    {
                        'first_name': 'Sultan',
                        'last_name': 'Sulaimanov'
                    },
                    {
                        'first_name': 'Ulan',
                        'last_name': 'Kurmanbekov'
                    },
                    {
                        'first_name': 'Marlen',
                        'last_name': 'Melsov'
                    },
                ]
            },
            {
                'id': book2.id,
                'name': 'Test book 2',
                'price': '20.00',
                'author_name': 'Author 2',
                'likes_count': 2,
                'rating': '3.00',
                'discounted_price': '18.00',
                'owner_name': '',
                'readers': [
                    {
                        'first_name': 'Sultan',
                        'last_name': 'Sulaimanov'
                    },
                    {
                        'first_name': 'Ulan',
                        'last_name': 'Kurmanbekov'
                    },
                    {
                        'first_name': 'Marlen',
                        'last_name': 'Melsov'
                    },
                ]
            }
        ]

        self.assertEqual(expected_data, data)
