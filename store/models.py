from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Book(models.Model):
    DISCOUNT_VALIDATE = [MinValueValidator(0), MaxValueValidator(100)]

    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    author_name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='owned_books')
    readers = models.ManyToManyField(User, through='UserBookRelation', related_name='books_read')
    discount = models.PositiveSmallIntegerField(default=0, blank=True, validators=DISCOUNT_VALIDATE)
    rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, default=None)

    def __str__(self):
        return f'ID {self.id}: {self.name}'


class UserBookRelation(models.Model):
    RATE_CHOICES = (
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    like = models.BooleanField(default=False)
    in_bookmarks = models.BooleanField(default=False)
    rate = models.PositiveSmallIntegerField(choices=RATE_CHOICES, null=True)

    def __str__(self):
        return f'{self.user.username}: {self.book.name} - rate {self.rate}'

    def __init__(self, *args, **kwargs):
        super(UserBookRelation, self).__init__(*args, **kwargs)
        self.old_rate = self.rate

    def save(self, *args, **kwargs):
        from store.utils import set_rating

        creating = not self.pk

        super().save(*args, **kwargs)

        if self.old_rate != self.rate or creating:
            set_rating(self.book)
