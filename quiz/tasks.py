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
        "id": game.id,
        "player_amount": 0,
        "remainders": 0,
        "reward": game.reward,
        "quiz": quiz,
        "is_active": game.is_active,
    }
    print(game_info)
    return json.dumps(game_info)


@celery_app.task()
def update_game_status(game_id):
    game = Game.objects.get(pk=game_id)
    if game.is_active:
        if game.status == Game.CREATED:
            logger.info('更新游戏[{}]为正在进行中'.format(game.title))
            game.status = Game.PROCESSING
            game.save(update_fields=['status'])
        elif game.status == Game.PROCESSING:
            logger.info('游戏[{}]正在进行中'.format(game.title))
        elif game.status == Game.OVER:
            logger.info('游戏[{}]已结束'.format(game.title))
        else:
            logger.info('游戏[{}]状态错误'.format(game.title))
    else:
        logger.error('游戏[{}]未激活'.format(game.title))


@celery_app.task()
def start_game(game_id):
    game = Game.objects.get(pk=game_id)
    if game.is_active:
        if game.status == Game.CREATED:
            # 将数据存储到redis
            game_info = format_game(game)
            r.set("game", game_info)
            r.set("gameFlag:{}".format(game_id), 0)
        elif game.status == Game.PROCESSING:
            logger.info('游戏[{}]正在进行中'.format(game.title))
        elif game.status == Game.OVER:
            logger.info('游戏[{}]已结束'.format(game.title))
        else:
            logger.info('游戏[{}]状态错误'.format(game.title))
    else:
        logger.error('游戏[{}]未激活'.format(game.title))


@celery_app.task()
def save_game_result(game_id):
    user_key = "game:{}".format(game_id)
    result_key = "gameResult:{}".format(game_id)
    game_flag = "gameFlag:{}".format(game_id)
    user_info = r.hvals(user_key)
    insert_data = []

    if r.get(game_flag) == 1:
        return

    try:
        with transaction.atomic():
            result = r.get(result_key)
            if result:
                result = json.loads(result)
                winners = result.get('winners')
                all_user = [user['openid'] for user in winners]
                game = Game.objects.get(pk=game_id)
                all_reward = game.reward
                game.status = Game.OVER
                game.player_num = result.get('player_amount', 0)
                game.win_num = result.get('winner_amount', 0)
                game.save(update_fields=['status', 'player_num', 'win_num'])
            else:
                all_user = []
                all_reward = 0
                winners = []

            for u in user_info:
                user = json.loads(u.decode('utf-8'))
                if winners:
                    reward = round(all_reward / len(winners), 2) if user['openid'] in all_user else 0
                else:
                    reward = 0
                item = GameResult(openid=user['openid'], nickname=user['name'], sex=user['sex'],
                                  nums=len([i for i in user['answers'] if i['result'] == 1]), reward=reward,
                                  join_time=datetime.fromtimestamp(user.get('enter_timestamp', 0)), game_id=game_id)
                insert_data.append(item)
            logger.info("winners:{}".format(len(winners)))
            logger.info(insert_data)
            GameResult.objects.bulk_create(insert_data)
            r.set(game_flag, 1)
    except Exception as e:
        logger.error(e)
