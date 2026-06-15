from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("portal", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="scrapejob",
            name="progress",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="scrapejob",
            name="do_export",
            field=models.BooleanField(default=False),
        ),
    ]
