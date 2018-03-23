# -*- coding: utf-8 -*-
import json
from django.http.response import JsonResponse
from django.views.generic.base import View
from django.db import transaction

from quiz.models import GameResult
from quiz.tasks import save_game_result


# Create your views here.
class ResultView(View):
    """存储游戏结果"""

    def post(self, request):
        game_id = json.loads(request.body).get('game_id')
        save_game_result.apply_async((game_id,))
        return JsonResponse({'code': 0, 'msg': 'success'})


class UserInfoView(View):
    """
    添加用户信息
    open_id:
    game_id:
    name:
    phone:
    work_number:
    """

    def post(self, request):
        user_info = json.loads(request.body)
        try:
            with transaction.atomic():
                info = GameResult.objects.select_for_update().get(openid=user_info.get('openid'),
                                                                  game_id=user_info.get('game_id'))
                info.name = user_info.get('name', '')
                info.phone = user_info.get('phone', '')
                info.work_num = user_info.get('work_number', '')
                info.save(update_fields=['name', 'phone', 'work_num'])

                return JsonResponse({'code': 0, 'msg': 'success'})
        except Exception as e:
            print(e)
            return JsonResponse({'code': -1, 'msg': 'failed'})
