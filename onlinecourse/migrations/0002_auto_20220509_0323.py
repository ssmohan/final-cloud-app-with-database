# Generated by Django 3.1.3 on 2022-05-09 03:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onlinecourse', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='choice',
            name='choice_text',
            field=models.CharField(max_length=300, null=True),
        ),
        migrations.AlterField(
            model_name='question',
            name='question_text',
            field=models.CharField(max_length=300, null=True),
        ),
    ]
