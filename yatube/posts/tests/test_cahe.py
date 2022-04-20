
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post, User


class TaskURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='User_test')
        cls.post_cash = Post.objects.create(
            author=cls.user,
            text='Тестируем cashe',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_page(self):
        """Тестируем  кэш главной страницы."""
        response = self.authorized_client.get(
            reverse('posts:index')).content
        self.post_cash.delete()
        response_cache = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertEqual(response, response_cache)
        cache.clear()
        response_clear = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertNotEqual(response, response_clear)
