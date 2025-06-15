from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0008_add_product_inventory_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ] 