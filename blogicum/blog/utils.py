from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q, Count


def annotate_comment_count(queryset):
    return queryset.annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date')


def get_paginator_page(queryset, page_number, posts_per_page=10):
    paginator = Paginator(queryset, posts_per_page)
    return paginator.get_page(page_number)


def filter_published_posts(queryset, user=None):
    published_condition = Q(
        is_published=True,
        category__is_published=True,
        pub_date__lte=timezone.now()
    )

    if user and user.is_authenticated:
        return queryset.filter(
            Q(author=user) | published_condition
        ).distinct()

    return queryset.filter(published_condition)
