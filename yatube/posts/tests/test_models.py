from django.test import TestCase

from posts.models import Group, Post, User

LIMIT_SIMBOLS = 15


class PostModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        """Класс для тестирования моедели Post."""
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа' * 2,
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост' * 2,
            group=cls.group,
        )

    def test_post_model_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает str."""
        post = PostModelTest.post
        self.assertEqual(str(post), post.text[:LIMIT_SIMBOLS])

    def test_group_model_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает str."""
        group = PostModelTest.group
        self.assertEqual(str(group), group.title)

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'group': 'Группа',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help_text = {
            'text': 'Введите текст поста',
            'group': 'Группа к которой будет относится пост',
        }
        for value, expected in field_help_text.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected)
