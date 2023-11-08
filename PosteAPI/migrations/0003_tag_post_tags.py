# Generated by Django 4.2.5 on 2023-11-08 07:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('PosteAPI', '0002_alter_folderpermission_unique_together'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='post',
            name='tags',
            field=models.ManyToManyField(blank=True, related_name='posts', to='PosteAPI.tag'),
        ),
    ]