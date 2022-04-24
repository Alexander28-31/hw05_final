from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Follow, Group, Post, User

SECOND_PAGE_PAGINATOR = 3


class CaheTests(TestCase):

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


class PagesTests(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(username='leo')
        super().setUpClass()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.group = Group.objects.create(title='test_group',
                                         slug='test_slug',
                                         description='test_description')
        cls.group_test = Group.objects.create(title='test_group_test1',
                                              slug='test_slug1',
                                              description='test_description1')
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(text='test_text',
                                       author=cls.user,
                                       group=cls.group,
                                       image=cls.uploaded)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def chek_post(self, post):
        self.assertEqual(post.id, self.post.id)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.image, self.post.image)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_name = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user.username}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
                'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
                'posts/post_create.html',
            reverse('posts:post_create'): 'posts/post_create.html',
        }

        for addres, template, in templates_pages_name.items():
            with self.subTest(addres=addres):
                response = self.authorized_client.get(addres)
                self.assertTemplateUsed(response, template)

    def test_home_page_correct_context(self):
        """Проверка списка постов."""
        response = self.authorized_client.get(reverse('posts:index'))
        test_obj = response.context['page_obj'][0]
        self.assertEqual(test_obj, self.post)

    def test_group_list_page_correct_context(self):
        """Проверка списка постов отфильтрованных по группе."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.user.slug}))
        post = response.context['page_obj'][0]
        self.chek_post(post)
        self.assertEqual(self.group, response.context["group"])

    def test_group_list_page_correct_context(self):
        """Проверка списка постов отфильтрованных по пользователю."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username}))
        post = response.context['page_obj'][0]
        self.chek_post(post)
        self.assertEqual(self.user, response.context["author"])

    def test_group_list_page_id_correct_context(self):
        """Проверка одного поста отфильтрованного по id."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': 1}))
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(
            response.context.get('post').author.posts.count(),
            len(self.user.posts.all()))
        self.assertEqual(response.context.get('post').author, self.user)

    def test_creat_page_correct_context(self):
        """Шаблон создания поста с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'group': forms.models.ModelChoiceField,
            'text': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_page_correct_context(self):
        """Шаблон редактирования поста с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        self.assertIsInstance(response.context.get('form'), PostForm)
        form_fields = {
            'group': forms.models.ModelChoiceField,
            'text': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        is_edit = response.context['is_edit']
        self.assertTrue('is_edit')
        self.assertIsInstance(is_edit, bool)

    def test_post_in_the_right_group(self):
        """ Проверяем что пост не попал в другую группу """
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test_slug1'}))
        self.assertEqual(len(response.context['page_obj']), 0)


class PiginatorViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='meo')
        cls.user_2 = User.objects.create_user(username='lmeo')
        cls.group = Group.objects.create(title='test_group',
                                         slug='test_slug',
                                         description='test_description')
        for i in range(13):
            cls.posts = Post.objects.create(author=cls.user,
                                            text=f'{i} Text',
                                            group=cls.group)
        cls.templates = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': cls.group.slug}),
            reverse('posts:profile', kwargs={'username': cls.user.username}),
            reverse('posts:follow_index')
        ]
        cls.templates2 = [
            reverse('posts:index') + '?page=2',
            reverse('posts:group_list', kwargs={'slug': cls.group.slug})
            + '?page=2',
            reverse('posts:profile', kwargs={'username': cls.user.username})
            + '?page=2'
        ]

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client_not_autor = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_not_autor.force_login(self.user_2)

    def test_paginator_correct(self):
        """Проверяет что на странице присутсвует 10 постов."""
        Follow.objects.create(user=self.user_2, author=self.user)
        for number_of_posts_for_paginator in range(len(self.templates)):
            with self.subTest(
                    templates=self.templates[number_of_posts_for_paginator]):
                response = self.authorized_client_not_autor.get(
                    self.templates[number_of_posts_for_paginator])
                self.assertEqual(len(response.context['page_obj']),
                                 settings.POSTS_PER_PAGE)

    def test_paginator_correct_2(self):
        """Проверяет количество постов на 2ой странице -3."""
        for number_of_posts_on_next_page in range(len(self.templates2)):
            with self.subTest(
                    templates2=self.templates2[number_of_posts_on_next_page]):
                response = self.authorized_client.get(
                    self.templates2[number_of_posts_on_next_page])
                self.assertEqual(len(response.context['page_obj']),
                                 SECOND_PAGE_PAGINATOR)


class FollowerFormTest(TestCase):
    """Класс тестирования подисок."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.user = User.objects.create_user(username='user_bob')
        cls.post = Post.objects.create(text='test_text',
                                       author=cls.user
                                       )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client_not_author = Client()
        self.authorized_client.force_login(self.author)
        self.authorized_client_not_author.force_login(self.user)

    def test_authorized_client_create_follow(self):
        """
        Авторизованный пользователь может подписываться
        на других пользователей.
        """
        follow_count = Follow.objects.count()
        form = {
            "username": self.author.username,
        }
        response = self.authorized_client_not_author.post(
            reverse('posts:profile_follow',
                    kwargs={'username': self.author.username}),
            data=form,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.author.username})
        )
        last_follow = Follow.objects.first()
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertEqual(last_follow.user, self.user)

    def test_authorized_client_create_unfollow(self):
        """
        Авторизованный пользователь может  отписаться
        подписываться от других пользователей.
        """
        follow = Follow.objects.create(user=self.user, author=self.author)
        follow_count = Follow.objects.count()
        follow.delete()
        form = {
            "username": self.author.username,
        }
        response = self.authorized_client_not_author.post(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author.username}),
            data=form,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.author.username})
        )
        self.assertEqual(Follow.objects.count(), follow_count - 1)
        self.assertFalse(
            Follow.objects.filter(author=self.author,
                                  user=self.user).exists()
        )


class FollowFormTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.user = User.objects.create_user(username='user_new')
        cls.user2 = User.objects.create_user(username='user_new2')
        cls.group = Group.objects.create(title='test_group',
                                         slug='test_slug',
                                         description='test_descripton')
        cls.post = Post.objects.create(text='test_text',
                                       author=cls.author,
                                       group=cls.group)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client_not_author_1 = Client()
        self.authorized_client_not_author = Client()
        self.authorized_client.force_login(self.author)
        self.authorized_client_not_author_1.force_login(self.user)
        self.authorized_client_not_author.force_login(self.user2)

    def test_follow_test(self):
        """
        Новый пост появляется на странице подписок если
        ты подписан на юзера.
        """
        Follow.objects.create(user=self.user, author=self.author)
        new_post = Post.objects.create(text='test_text',
                                       author=self.author,
                                       group=self.group)
        response = self.authorized_client_not_author_1.get(
            reverse('posts:follow_index'))
        self.assertEqual(response.context['page_obj'][0], new_post)

    def test_unfollow_test(self):
        """
        Пост не появляется на странице если ты не подписан на юзера.
        """
        Follow.objects.create(user=self.user2, author=self.user)
        Post.objects.create(text='test_text',
                            author=self.user,
                            group=self.group)
        new_post = Post.objects.create(text='test_text',
                                       author=self.author,
                                       group=self.group)
        response = self.authorized_client_not_author.get(
            reverse('posts:follow_index'))
        self.assertNotEqual(response.context['page_obj'][0], new_post)
