# Generated by Django 4.0 on 2022-01-16 17:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assistant', '0002_alter_course_date_stamp'),
    ]

    operations = [
        migrations.AlterField(
            model_name='course',
            name='date_stamp',
            field=models.CharField(max_length=100, primary_key=True, serialize=False),
        ),
    ]
