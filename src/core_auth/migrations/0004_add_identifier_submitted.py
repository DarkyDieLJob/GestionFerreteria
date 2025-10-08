from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core_auth', '0003_remove_passwordresetrequest_identifier_submitted_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='passwordresetrequest',
            name='identifier_submitted',
            field=models.CharField(max_length=255, blank=True, default=''),
        ),
    ]
