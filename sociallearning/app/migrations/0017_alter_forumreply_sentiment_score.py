# Generated by Django 5.1.6 on 2025-04-18 03:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0016_forumreply_sentiment_score'),
    ]

    operations = [
        migrations.AlterField(
            model_name='forumreply',
            name='sentiment_score',
            field=models.FloatField(default=0),
        ),
    ]
