# Generated by Django 4.1.6 on 2023-03-19 13:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='class_list',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
    ]
