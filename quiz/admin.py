from django.contrib import admin

# Register your models here.
from .models import Game, Question, Choice


class GameAdmin(admin.ModelAdmin):
    filter_horizontal = ('questions',)


class ChoiceSubInline(admin.TabularInline):
    model = Choice
    extra = 2  # 最少两个选项
    max_num = 4  # 最多四个选项


class QuestionAdmin(admin.ModelAdmin):
    inlines = [
        ChoiceSubInline,
    ]


admin.site.register(Game, GameAdmin)
admin.site.register(Question, QuestionAdmin)
