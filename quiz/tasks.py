# -*- coding: utf-8 -*-
import json
from datetime import timedelta, datetime

from celery.utils.log import get_task_logger
from django.db import transaction

from quiz.models import Game, Choice, GameResult
from quiz_sys import celery_app
from quiz_sys.redis import r

logger = get_task_logger(__name__)


def format_game(game):
    questions = game.gamequestion_set.values('question_id', 'index')
    choices = Choice.objects.filter(question__in=[q['question_id'] for q in questions]).values('question__title',
                                                                                               'question_id',
                                                                                               'description', 'index',
                                                                                               'is_correct').order_by(
        'question_id', 'index')

    options_dict = {}
    for item in choices:
        question_id = item['question_id']
        if question_id not in options_dict.keys():
            options_dict[question_id] = {"options": [], "answer": 0, "title": item["question__title"]}
        if item["is_correct"] == 1:
            options_dict[question_id]["answer"] = item['index']
        options_dict[question_id]["options"].append(dict(key=item['index'], value=item['description']))

    quiz = []
    for q in questions:
        qid = q['question_id']
        info = dict(id=qid, title=options_dict[qid]['title'], answer=options_dict[qid]['answer'], order=q['index'],
                    options=options_dict[qid]['options'])
        quiz.append(info)

    game_info = {
        "start_time": int(game.start_time.timestamp()),
        "interval": game.each_time,
        "game_id": game.id,
        "player_amount": 0,
        "remainders": 0,
        "quiz": quiz,
    }
    print(game_info)
    return json.dumps(game_info)


@celery_app.task()
def start_game(game_id):
    game = Game.objects.get(pk=game_id)
    if game.is_active:
        if game.status == Game.CREATED:
            logger.info("游戏[{}]开始".format(game.title))
            game.status = Game.PROCESSING
            game.save(update_fields=['status'])
            # 将数据存储到redis
            game_info = format_game(game)
            r.set("game", game_info)
        elif game.status == Game.PROCESSING:
            logger.info('游戏[{}]正在进行中'.format(game.title))
        elif game.status == Game.OVER:
            logger.info('游戏[{}]已结束'.format(game.title))
        else:
            logger.info('游戏[{}]状态错误'.format(game.title))
    else:
        logger.error('游戏[{}]未激活'.format(game.title))


@celery_app.task(bind=True)
def save_game_result(self, game_id):
    user_key = "game:{}".format(game_id)
    result_key = "gameResult:{}".format(game_id)
    user_info = self.r.hvals(user_key)
    insert_data = []

    try:
        with transaction.atomic():
            result = self.r.get(result_key)
            if result:
                result = json.loads(result)
                game = Game.objects.get(pk=game_id)
                game.status = Game.OVER
                game.player_num = result.get('player_amount', 0)
                game.win_num = result.get('winner_amount', 0)
                game.save(update_fields=['status', 'player_num', 'win_num'])

            for u in user_info:
                user = json.loads(u.decode('utf-8'))
                item = GameResult(openid=user['openid'], nickname=user['nickname'], sex=user['sex'],
                                  nums=len([i for i in user['answers'] if i['result'] == 1]),
                                  join_time=datetime.fromtimestamp(user.get('enter_timestamp', 0)), game_id=game_id)
                insert_data.append(item)
                GameResult.objects.bulk_create(insert_data)
    except Exception as e:
        self.retry(exc=e, countdown=5, max_retries=3)
