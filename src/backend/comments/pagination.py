from django.core.paginator import Paginator
from django.db import connection
from django.utils.functional import cached_property

from rest_framework.pagination import PageNumberPagination


class FastTopLevelPaginator(Paginator):
    @cached_property
    def count(self):
        """
        Instantly get the row count from the partial index metadata.
        """
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT reltuples FROM pg_class WHERE relname = 'idx_comment_top_id'"
            )
            row = cursor.fetchone()

        estimate = int(row[0]) if row else 0

        if estimate <= 0:
            return super().count

        return estimate


class CommentsPagination(PageNumberPagination):
    django_paginator_class = FastTopLevelPaginator
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100
