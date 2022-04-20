from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Comment, Post


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Текст поста',
            'group': 'Группа поста',
        }
        help_texts = {
            'text': _('Заполните поле - для вашего поста'),
            'group': _('Группа не обязательна, но я настаиваю 😡')
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].widget.attrs['placeholder'] = (
            'Введите какой нибудь текст, ну пожалуйста 🥺')
        self.fields['group'].empty_label = ('Выберите группу 👀')


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'Текст комментария',
        }
        help_texts = {
            'text': _('Заполните поле - для вашего комментария')
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].widget.attrs['placeholder'] = (
            'Введите какой нибудь текст, ну пожалуйста 🥺')
