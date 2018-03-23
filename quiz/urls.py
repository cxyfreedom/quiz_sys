# -*- coding: utf-8 -*-
from django.conf.urls import url

from quiz.views import ResultView, UserInfoView

urlpatterns = [
    url(r'^push$', ResultView.as_view(), name='result_push'),
    url(r'^user-info$', UserInfoView.as_view(), name='user_info'),
]