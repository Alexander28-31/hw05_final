import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Comment, Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTest(TestCase):
    """Класс тестирования постов."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.user = User.objects.create_user(username='user_bob')
        cls.group = Group.objects.create(title='test_group',
                                         slug='test_slug',
                                         description='test_descripton')
        cls.post = Post.objects.create(author=cls.author,
                                       group=cls.group,
                                       text='Text_3'
                                       )
        cls.post_edit = Post.objects.create(author=cls.author,
                                            group=cls.group,
                                            text='Edit Text',
                                            )
        cls.form = PostForm()

        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )

        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(
            TEMP_MEDIA_ROOT,
            ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client_not_author = Client()
        self.authorized_client.force_login(self.author)
        self.authorized_client_not_author.force_login(self.user)

    def test_create_form_post(self):
        """Проверка создания нового поста с добавлением img."""
        post_count = Post.objects.count()
        form = {
            'text': self.post.text,
            'group': self.group.pk,
            'image': self.uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile',
                    kwargs={'username': self.author.username}))

        last_post = Post.objects.first()
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(last_post.text, form['text'])
        self.assertEqual(last_post.group.pk, form['group'])
        self.assertEqual(last_post.author, self.author)
        self.assertEqual(last_post.image.name, 'posts/small.gif')

    def test_eddit_post_success(self):
        """Проверка редактирования поста."""
        post_count = Post.objects.count()
        form = {
            'text': self.post_edit.text,
            'group': self.post_edit.group.pk,
        }
        response = self.authorized_client.post(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}), data=form)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.post.refresh_from_db()
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        last_post = Post.objects.first()
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(last_post.text, form['text'])
        self.assertEqual(last_post.group.pk, form['group'])
        self.assertEqual(last_post.author, self.author)

    def test_form_create_post_unauthorized_user(self):
        """
        Проверяем, что неавторизованный пользователь не может
        отправить запрос на создание поста
        """
        post_count = Post.objects.count()
        form = {
            'text': 'Text_3',
            'group': self.group.id,
        }
        response = self.guest_client.post(reverse('posts:post_create'),
                                          data=form,
                                          follow=True)
        self.assertRedirects(response,
                             reverse('users:login') + '?next=/create/')
        self.assertEqual(Post.objects.count(), post_count)

    def test_add_comment(self):
        """Авторизованный пользователь может комментировать посты."""
        com_count = Comment.objects.count()
        form = {
            'post': self.post_edit,
            'author': self.post_edit.author,
            'text': self.post_edit.text,
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        comment = Comment.objects.first()
        self.assertEqual(Comment.objects.count(), com_count + 1)
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.text, form['text'])
        self.assertEqual(comment.author, self.post.author)

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
