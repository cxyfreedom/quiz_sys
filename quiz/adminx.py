# -*- coding: utf-8 -*-
from datetime import timedelta, datetime

import pytz
import xadmin
from xadmin import views
from django import forms
from django.db.models import F, Q, IntegerField, ExpressionWrapper

from quiz.models import Question, Choice, Game, GameQuestion, GameResult
from quiz.tasks import start_game


class BaseSetting:
    enable_themes = True  # 开启主题选择
    use_bootswatch = True


class GlobalSettings:
    site_title = '冲顶大会管理系统'  # 设置左上角名字
    site_footer = 'quiz'  # 设置底部版权信息
    menu_style = 'accordion'  # 菜单样式


class ChoiceInline:
    model = Choice
    extra = 0
    style = 'accordion'


class QuestionInline:
    model = GameQuestion
    extra = 0
    style = 'accordion'
    style_fields = {'question': "fk-ajax"}


class QuestionAdminForm(forms.ModelForm):
    def clean(self):
        # 校验选项数量2 ～ 4
        num_is_valid = True if 2 <= int(self.data.get('choices-TOTAL_FORMS')) <= 4 else False
        if not num_is_valid:
            raise forms.ValidationError('选项个数必须在2～4之间')
        # 校验选项内容正确答案唯一
        is_unique = True if len([v for k, v in self.data.items() if 'is_correct' in k]) == 1 else False
        if not is_unique:
            raise forms.ValidationError('正确答案必须唯一')


class GameAdminForm(forms.ModelForm):
    def clean(self):
        # 校验游戏时间是否符合逻辑
        cur_id = self.initial.get('id', 0)
        play_time = self.cleaned_data.get('each_time') * self.cleaned_data.get('rounds')
        cur_start = self.cleaned_data.get('start_time')
        cur_end = self.cleaned_data.get('start_time') + timedelta(seconds=play_time)

        # 校验游戏是否已经结束
        if Game.objects.filter(Q(id=cur_id) & Q(status=Game.OVER)):
            raise forms.ValidationError('当前游戏已结束，无法修改相关数据！')

        # 校验当前时间和游戏开始时间是否大于 5 分钟
        now = datetime.now()
        tz = pytz.timezone('Asia/Shanghai')
        now = tz.localize(now)
        if cur_start < now or cur_end < now:
            raise forms.ValidationError('游戏开始和结束时间必须大于当前时间')
        if (now - cur_start).seconds < (60 * 5):
            raise forms.ValidationError('游戏开始时间必须与当前时间间隔至少 5 分钟')

        # 获取数据库中存在的活动时间
        games = Game.objects.filter(~Q(id=cur_id), ~Q(status=Game.OVER)).annotate(
            end_time=ExpressionWrapper(F('each_time') * F('rounds'),
                                       output_field=IntegerField())).values_list('start_time',
                                                                                 'end_time')
        for start_time, end_time in games:
            if max(start_time, cur_start) < min(start_time + timedelta(seconds=end_time), cur_end):
                raise forms.ValidationError('当前游戏时间与其他游戏时间有冲突！')

        question_num = int(self.data['gamequestion_set-TOTAL_FORMS'])
        if question_num <= 0 or int(self.data["rounds"]) != question_num:
            raise forms.ValidationError('回合数和问题数量需相等并且至少一个回合！')

        for q in range(question_num):
            title = "gamequestion_set-{}-question".format(q)
            if not self.data[title]:
                raise forms.ValidationError("题目为必填项！")


class QuestionAdmin:
    form = QuestionAdminForm
    list_display = ['title', 'create_time', 'modified_time']
    search_fields = ['title']
    list_filter = ['title']
    ordering = ['-create_time']
    inlines = [ChoiceInline, ]


class GameAdmin:
    form = GameAdminForm
    list_display = ['title', 'each_time', 'start_time', 'rounds', 'is_active', 'status', 'create_time',
                    'modified_time']
    search_fields = ['title']
    list_filter = ['each_time', 'start_time', 'rounds', 'is_active', 'status', 'create_time']
    inlines = [QuestionInline, ]

    def save_models(self):
        obj = self.new_obj
        obj.save()
        start_game.apply_async((obj.id,), eta=obj.start_time)


class GameResultAdmin:
    list_display = ['nickname', 'sex', 'nums', 'join_time', 'game']  # 设置要显示在列表中的字段
    search_fields = ['game__title']  # 搜索字段
    list_filter = ['game']  # 过滤器
    ordering = []  # 设置默认排序字段，负号表示降序排序
    readonly_fields = ['openid', 'nickname', 'sex', 'nums', 'join_time', 'game']


xadmin.site.register(Question, QuestionAdmin)
xadmin.site.register(Game, GameAdmin)
xadmin.site.register(GameResult, GameResultAdmin)
xadmin.site.register(views.BaseAdminView, BaseSetting)
xadmin.site.register(views.CommAdminView, GlobalSettings)
