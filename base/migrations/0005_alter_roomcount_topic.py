# Generated by Django 3.2 on 2022-11-05 17:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0004_auto_20221105_0938'),
    ]

    operations = [
        migrations.AlterField(
            model_name='roomcount',
            name='topic',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='base.topic'),
        ),
    ]
