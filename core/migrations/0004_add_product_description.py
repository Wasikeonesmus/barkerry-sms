from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_add_created_at_to_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='description',
            field=models.TextField(blank=True),
        ),
    ] 