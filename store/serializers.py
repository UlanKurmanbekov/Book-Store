from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from store.models import Book, UserBookRelation


class BookSerializer(ModelSerializer):
    likes_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Book
        fields = ('id', 'name', 'price', 'author_name', 'likes_count')


class UserBookRelationSerializer(ModelSerializer):
    class Meta:
        model = UserBookRelation
        fields = ('book', 'like', 'in_bookmarks', 'rate')
