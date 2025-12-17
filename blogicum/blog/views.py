from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404, HttpResponseForbidden
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from .models import Post, Category, Comment
from .forms import PostForm, CommentForm, UserCreationForm, UserUpdateForm
from .utils import (
    annotate_comment_count,
    get_paginator_page,
    filter_published_posts,
)


User = get_user_model()


def index(request):
    template = 'blog/index.html'

    post_list = Post.objects.select_related(
        'category', 'location', 'author'
    )
    post_list = annotate_comment_count(post_list)
    post_list = filter_published_posts(post_list)
    post_list = post_list.order_by('-pub_date')

    page_obj = get_paginator_page(post_list, request.GET.get('page'))

    context = {'page_obj': page_obj}
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'blog/detail.html'
    post = get_object_or_404(
        Post.objects.select_related('category', 'location', 'author')
        .prefetch_related('comments__author'),
        pk=post_id
    )

    can_see_post = (
        post.is_published and 
        post.category.is_published and 
        post.pub_date <= timezone.now()
    )
    if not can_see_post and post.author != request.user:
        raise Http404("Post not found")

    comments = post.comments.all()
    form = CommentForm()

    context = {
        'post': post,
        'comments': comments,
        'form': form
    }
    return render(request, template, context)


def category_posts(request, category_slug):
    template = 'blog/category.html'
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )

    post_list = category.posts.select_related(
        'location', 'author'
    )
    post_list = annotate_comment_count(post_list)
    post_list = filter_published_posts(post_list)
    post_list = post_list.order_by('-pub_date')

    page_obj = get_paginator_page(post_list, request.GET.get('page'))

    context = {
        'category': category,
        'page_obj': page_obj
    }
    return render(request, template, context)


def profile(request, username):
    template = 'blog/profile.html'
    author = get_object_or_404(User, username=username)

    post_list = author.posts.select_related(
        'category', 'location'
    )
    post_list = annotate_comment_count(post_list)
    post_list = filter_published_posts(post_list, request.user)
    post_list = post_list.order_by('-pub_date')

    page_obj = get_paginator_page(post_list, request.GET.get('page'))

    context = {
        'profile': author,
        'page_obj': page_obj
    }
    return render(request, template, context)


def profile_edit(request):
    template = 'blog/user.html'
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('blog:profile', username=request.user.username)
    else:
        form = UserUpdateForm(instance=request.user)

    context = {'form': form}
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'blog/create.html'
    form = PostForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('blog:profile', username=request.user.username)

    context = {'form': form}
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    template = 'blog/create.html'
    post = get_object_or_404(Post, pk=post_id)

    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None,
        request.FILES or None,
        instance=post
    )

    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post_id)

    context = {
        'form': form,
        'post': post
    }
    return render(request, template, context)


@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    if post.author != request.user:
        return HttpResponseForbidden()

    post.delete()

    return redirect('blog:profile', username=request.user.username)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()

    return redirect('blog:post_detail', post_id=post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    template = 'blog/comment.html'
    comment = get_object_or_404(Comment, pk=comment_id, post_id=post_id)

    if comment.author != request.user:
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = CommentForm(instance=comment)

    context = {
        'form': form,
        'comment': comment,
        'post': comment.post
    }
    return render(request, template, context)


@login_required
def delete_comment(request, post_id, comment_id):
    template = 'blog/comment.html'
    comment = get_object_or_404(Comment, pk=comment_id, post_id=post_id)

    if comment.author != request.user:
        return HttpResponseForbidden()

    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)

    context = {
        'comment': comment,
        'post': comment.post
    }
    return render(request, template, context)


def registration(request):
    template = 'registration/registration_form.html'
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()

    context = {'form': form}
    return render(request, template, context)
