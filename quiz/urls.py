# -*- coding: utf-8 -*-
from django.conf.urls import url

from quiz.views import ResultView

urlpatterns = [
    url(r'^push$', ResultView.as_view(), name='result_push'),
]