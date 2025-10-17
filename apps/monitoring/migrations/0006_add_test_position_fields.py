# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0005_add_stop_detection_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='vehiclepositionhistory',
            name='is_test_position',
            field=models.BooleanField(
                default=False,
                help_text='Indica se esta é uma posição injetada para teste/simulação',
                verbose_name='Posição de Teste'
            ),
        ),
        migrations.AddField(
            model_name='vehiclepositionhistory',
            name='test_metadata',
            field=models.JSONField(
                blank=True,
                help_text='Informações sobre o teste (modo de simulação, origem, etc.)',
                null=True,
                verbose_name='Metadados de Teste'
            ),
        ),
    ]

