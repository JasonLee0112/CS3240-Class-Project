# Generated by Django 4.1.6 on 2023-04-07 18:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0012_cart_term_schedule_term_alter_cart_student'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cart',
            name='term',
        ),
    ]
