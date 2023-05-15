# Generated by Django 4.1.6 on 2023-04-07 18:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0011_schedule_editable'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='term',
            field=models.CharField(default=1238, max_length=4),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='schedule',
            name='term',
            field=models.CharField(default=1238, max_length=4),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='cart',
            name='student',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='schedule.student'),
        ),
    ]
