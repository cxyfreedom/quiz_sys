# -*- coding: utf-8 -*-
from django.db import models
from django.conf import settings


# Create your models here.
class Question(models.Model):
    """问题"""
    title = models.CharField(max_length=200, verbose_name="题目")
    create_time = models.DateTimeField(auto_now_add=True, editable=False, verbose_name="添加时间")
    modified_time = models.DateTimeField(auto_now=True, editable=False, verbose_name="修改时间")

    class Meta:
        db_table = "questions"
        verbose_name = verbose_name_plural = "问题"

    def __str__(self):
        return self.title


class Choice(models.Model):
    """问题选项"""
    question = models.ForeignKey(Question, related_name="choices")
    description = models.CharField(max_length=50, verbose_name="选项内容")
    index = models.PositiveIntegerField(default=1, verbose_name="选项顺序")
    is_correct = models.BooleanField(verbose_name="是否是正确答案")
    create_time = models.DateTimeField(auto_now_add=True, editable=False, verbose_name="创建时间")
    modified_time = models.DateTimeField(auto_now=True, editable=False, verbose_name="修改时间")

    class Meta:
        db_table = "choices"
        verbose_name = verbose_name_plural = "选项"

    def __str__(self):
        return "{} - {}".format(self.description, self.index)


class Game(models.Model):
    CREATED = 0
    PROCESSING = 1
    OVER = 2

    GAME_STATUS = [
        (CREATED, '未开始'),
        (PROCESSING, '进行中'),
        (OVER, '已结束'),
    ]
    title = models.CharField(max_length=50, verbose_name="游戏名称")
    each_time = models.IntegerField(verbose_name="单题答题时间（秒）")
    start_time = models.DateTimeField(verbose_name="轮次开始时间")
    rounds = models.PositiveIntegerField(verbose_name="回合数量")
    questions = models.ManyToManyField(Question, through="GameQuestion")
    is_active = models.BooleanField(default=False, verbose_name="是否激活")
    status = models.IntegerField(choices=GAME_STATUS, default=CREATED, editable=False, verbose_name="游戏状态")
    player_num = models.IntegerField(default=0, editable=False, verbose_name="玩家人数")
    win_num = models.IntegerField(default=0, editable=False, verbose_name="获胜人数")
    create_time = models.DateTimeField(auto_now_add=True, editable=False, verbose_name="创建时间")
    modified_time = models.DateTimeField(auto_now=True, editable=False, verbose_name="修改时间")

    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="管理员")

    def __str__(self):
        return '{}'.format(self.title)

    class Meta:
        db_table = 'game'
        verbose_name = verbose_name_plural = "游戏"
        ordering = ["-create_time"]


class GameQuestion(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name="题目")
    game = models.ForeignKey(Game, on_delete=models.CASCADE, verbose_name="游戏")
    index = models.PositiveIntegerField(default=1, verbose_name="问题顺序")

    def __str__(self):
        return '{} - {}'.format(self.question.title, self.index)

    class Meta:
        db_table = "game_question"
        verbose_name = verbose_name_plural = "问题"


class GameResult(models.Model):
    SEX_ITEMS = [
        (1, '男'),
        (2, '女'),
        (0, '未知'),
    ]

    openid = models.CharField(max_length=200, verbose_name="用户的唯一标识")
    nickname = models.CharField(max_length=128, verbose_name="用户昵称")
    sex = models.IntegerField(choices=SEX_ITEMS, verbose_name="性别")
    # rank = models.IntegerField(verbose_name="游戏排名")
    nums = models.IntegerField(default=0, verbose_name="答对题数")
    join_time = models.DateTimeField(verbose_name="加入时间")
    game = models.ForeignKey(Game, related_name="games", verbose_name="游戏")

    def __str__(self):
        return '{} 的结果'.format(self.game.title)

    class Meta:
        db_table = "game_result"
        verbose_name = verbose_name_plural = "游戏结果"
