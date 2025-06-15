from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0007_add_product_sku'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='reorder_point',
            field=models.PositiveIntegerField(default=10),
        ),
        migrations.AddField(
            model_name='product',
            name='current_stock',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='product',
            name='cost_price',
            field=models.DecimalField(max_digits=10, decimal_places=2, default=0),
        ),
    ] 