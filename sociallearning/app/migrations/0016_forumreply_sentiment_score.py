# Generated by Django 5.1.6 on 2025-04-18 03:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0015_notification'),
    ]

    operations = [
        migrations.AddField(
            model_name='forumreply',
            name='sentiment_score',
            field=models.IntegerField(default=0),
        ),
    ]
