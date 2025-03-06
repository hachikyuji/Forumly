# Generated by Django 5.1.3 on 2025-03-06 09:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0006_forumthread_dislikes_forumthread_likes'),
    ]

    operations = [
        migrations.AddField(
            model_name='forumreply',
            name='category',
            field=models.CharField(default='No Category', max_length=200),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='category_comment_count',
            field=models.JSONField(default=dict),
        ),
    ]
