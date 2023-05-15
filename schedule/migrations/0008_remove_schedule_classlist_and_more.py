# Generated by Django 4.1.6 on 2023-03-27 18:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0007_alter_course_units'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='schedule',
            name='classList',
        ),
        migrations.RemoveField(
            model_name='schedule',
            name='scheduleList',
        ),
        migrations.AddField(
            model_name='schedule',
            name='courses',
            field=models.ManyToManyField(to='schedule.course'),
        ),
    ]