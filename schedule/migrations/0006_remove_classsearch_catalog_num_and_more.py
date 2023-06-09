# Generated by Django 4.1.6 on 2023-03-27 16:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0005_rename_name_course_title_remove_course_course_id_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='classsearch',
            name='catalog_num',
        ),
        migrations.RemoveField(
            model_name='classsearch',
            name='component',
        ),
        migrations.RemoveField(
            model_name='classsearch',
            name='course_id',
        ),
        migrations.RemoveField(
            model_name='classsearch',
            name='end_time',
        ),
        migrations.RemoveField(
            model_name='classsearch',
            name='instructor',
        ),
        migrations.RemoveField(
            model_name='classsearch',
            name='meet_days',
        ),
        migrations.RemoveField(
            model_name='classsearch',
            name='name',
        ),
        migrations.RemoveField(
            model_name='classsearch',
            name='section',
        ),
        migrations.RemoveField(
            model_name='classsearch',
            name='start_time',
        ),
        migrations.RemoveField(
            model_name='classsearch',
            name='strm',
        ),
        migrations.RemoveField(
            model_name='classsearch',
            name='subject',
        ),
        migrations.RemoveField(
            model_name='classsearch',
            name='term',
        ),
        migrations.RemoveField(
            model_name='classsearch',
            name='year',
        ),
        migrations.AddField(
            model_name='classsearch',
            name='search_results',
            field=models.ManyToManyField(to='schedule.course'),
        ),
        migrations.AddField(
            model_name='classsearch',
            name='student',
            field=models.ForeignKey(default=2, on_delete=django.db.models.deletion.CASCADE, to='schedule.student'),
            preserve_default=False,
        ),
    ]
