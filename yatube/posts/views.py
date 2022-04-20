from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import get_page_pages


def index(request):
    """Выводит шаблоны главной страницы."""
    context = get_page_pages(
        Post.objects.select_related('author', 'group'), request)
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """Выводит шаблон с группами постов."""
    group = get_object_or_404(Group, slug=slug)
    context = {
        'group': group,
    }
    context.update(get_page_pages(
        group.posts.select_related('author', 'group'), request))
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Выводит шаблон профайла пользователя."""
    author = get_object_or_404(User, username=username)
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user,
        author=author).exists()
    context = {
        'author': author,
        'following': following,
    }
    context.update(get_page_pages(
        author.posts.all(), request))
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Выводит информацию о посте."""
    form = CommentForm()
    post = get_object_or_404(Post.objects.select_related("author"), id=post_id)
    comment = post.comments.all().select_related("author")
    context = {
        'post': post,
        'form': form,
        'comment': comment,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Создания новго поста."""
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()
        return redirect('posts:profile', request.user)
    context = {
        'form': form,
    }
    return render(request, 'posts/post_create.html', context)


@login_required
def post_edit(request, post_id):
    """Редактирование поста."""
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post.pk)
    form = PostForm(request.POST or None,
                    files=request.FILES or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'form': form,
        'is_edit': True,
        'post': post,
    }
    return render(request, 'posts/post_create.html', context)


@login_required
def add_comment(request, post_id):
    """Получение поста."""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'form': form,
        'post': post,
    }
    return render(request, 'posts:post_detail', context)


@login_required
def follow_index(request):
    """Информация о текущем пользователе доступа."""
    post = Post.objects.filter(
        author__following__user=request.user)
    context = {
        'title': "Посты в подписке",
    }
    context.update(get_page_pages(post, request))
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Подписаться на автора."""
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(
            user=request.user,
            author=author
        )
    return redirect("posts:profile", author)


@login_required
def profile_unfollow(request, username):
    """Дизлайк,отписка."""
    Follow.objects.filter(
        user=request.user,
        author__username=username).delete()
    return redirect("posts:profile", username)
