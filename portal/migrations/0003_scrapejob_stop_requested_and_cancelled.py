from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("portal", "0002_scrapejob_progress"),
    ]

    operations = [
        migrations.AddField(
            model_name="scrapejob",
            name="stop_requested",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="scrapejob",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pendiente"),
                    ("running", "En curso"),
                    ("done", "Completado"),
                    ("cancelled", "Detenido"),
                    ("error", "Error"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
    ]
