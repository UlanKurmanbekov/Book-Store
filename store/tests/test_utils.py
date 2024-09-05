from django.contrib.auth.models import User
from django.test import TestCase

from store.models import Book, UserBookRelation
from store.utils import set_rating


class SetRatingTestCase(TestCase):
    def setUp(self):
        user1 = User.objects.create(username='user1', first_name='Sultan', last_name='Sulaimanov')
        user2 = User.objects.create(username='user2', first_name='Ulan', last_name='Kurmanbekov')
        user3 = User.objects.create(username='user3', first_name='Marlen', last_name='Melsov')

        self.book = Book.objects.create(name='Test book 1', price=10, author_name='Author 1', owner=user1)

        UserBookRelation.objects.create(user=user1, book=self.book, like=True, rate=5)
        UserBookRelation.objects.create(user=user2, book=self.book, like=True, rate=5)
        UserBookRelation.objects.create(user=user3, book=self.book, like=True, rate=4)

    def test_ok(self):
        set_rating(self.book)
        self.book.refresh_from_db()
        self.assertEqual('4.67', str(self.book.rating))
