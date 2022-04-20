from http import HTTPStatus

from django.test import Client, TestCase

from posts.models import Group, Post, User


class PostModelTest(TestCase):
    """Класс тестирвоания страниц."""

    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(username='neo')
        cls.user_post = User.objects.create_user(username='neo_post')
        super().setUpClass()
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_slug',
            description='test_description',
        )
        cls.post = Post.objects.create(
            text='test_text',
            author=cls.user,
            group=cls.group,
        )
        cls.templates_url_all = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.user.username}/': 'posts/profile.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',
            f'/posts/{cls.post.id}/edit/': 'posts/post_create.html',
            '/create/': 'posts/post_create.html',
        }
        cls.templates_url_name = [
            '/',
            f'/group/{cls.group.slug}/',
            f'/profile/{cls.user.username}/',
            f'/posts/{cls.post.id}/',
        ]
        cls.templates_url_name2 = {
            f'/posts/{cls.post.id}/edit/': 'posts/post_create.html',
            '/create/': 'posts/post_create.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_user_post = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_user_post.force_login(self.user_post)

    def test_all_url_exists_at_desired_location(self):
        """
        Страница / доступна любому пользователю.
        Страница '/group/{cls.group.slug}/' доступна любому пользователю.
        Страница '/profile/{cls.user.username}/' доступна любому пользователю.
        Страница '/profile/{cls.post.id}/' доступна любому пользователю.
        """
        for addres in self.templates_url_name:
            with self.subTest(addres=addres):
                response = self.guest_client.get(addres)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_edit_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /posts/{self.post.pk}/edit/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get(
            f'/posts/{self.post.pk}/edit/', follow=True)
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.pk}/edit/')

    def test_create_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /create/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_profile_test_slug_url_exists_at_desired_location(self):
        """Страница  '/unexisting_page/' доступна любому пользователю."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, 404)

    def test_urls_correct_template(self):
        """Проверка используемых шаблоны"""
        for addres, template, in self.templates_url_all.items():
            with self.subTest(addres=addres):
                response = self.authorized_client.get(addres)
                self.assertTemplateUsed(response, template)

    def test_post_edit_url_redirect_authorized_on_post_page(self):
        """Страница post_edit перенаправляет не автора поста."""
        response = self.authorized_user_post.get(
            f'/posts/{self.post.pk}/edit/', follow=True)
        self.assertRedirects(response, f'/posts/{self.post.pk}/')

    def test_edit_create_authorized_on_post_page(self):
        """
        Страница 'post_edit' 'create' доступна авторизованному
        пользователю.
        """
        for addres in self.templates_url_name2:
            with self.subTest(addres=addres):
                response = self.authorized_client.get(addres)
                self.assertEqual(response.status_code, HTTPStatus.OK)
