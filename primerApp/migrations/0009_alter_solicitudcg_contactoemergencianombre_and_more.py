# Generated by Django 5.1.1 on 2024-12-12 04:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('primerApp', '0008_alter_solicitudcg_contactoemergencianombre_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='solicitudcg',
            name='contactoEmergenciaNombre',
            field=models.CharField(max_length=512),
        ),
        migrations.AlterField(
            model_name='solicitudcg',
            name='contactoEmergenciaTelefono',
            field=models.CharField(max_length=512),
        ),
        migrations.AlterField(
            model_name='solicitudcg',
            name='correoElectronico',
            field=models.CharField(max_length=512),
        ),
        migrations.AlterField(
            model_name='solicitudcg',
            name='nombreCompleto',
            field=models.CharField(max_length=512),
        ),
        migrations.AlterField(
            model_name='solicitudcg',
            name='rut',
            field=models.CharField(max_length=512),
        ),
        migrations.AlterField(
            model_name='solicitudcg',
            name='telefono',
            field=models.CharField(max_length=512),
        ),
    ]