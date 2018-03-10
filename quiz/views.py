# -*- coding: utf-8 -*-
import json
from django.http.response import JsonResponse
from django.views.generic.base import View

from quiz.tasks import save_game_result


# Create your views here.
class ResultView(View):
    """存储游戏结果"""

    def post(self, request):
        game_id = json.loads(request.body).get('game_id')
        save_game_result.apply_async((game_id,))
        return JsonResponse({'code': 0, 'msg': 'success'})
