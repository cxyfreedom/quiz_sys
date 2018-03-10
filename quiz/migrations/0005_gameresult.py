# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-03-06 09:41
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0004_auto_20180306_1712'),
    ]

    operations = [
        migrations.CreateModel(
            name='GameResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('openid', models.CharField(max_length=200, verbose_name='用户的唯一标识')),
                ('nickname', models.CharField(max_length=128, verbose_name='用户昵称')),
                ('sex', models.IntegerField(choices=[(1, '男'), (2, '女'), (0, '未知')], verbose_name='性别')),
                ('rank', models.IntegerField(verbose_name='游戏排名')),
                ('join_time', models.DateTimeField(editable=False, verbose_name='加入时间')),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='games', to='quiz.Game')),
            ],
        ),
    ]
