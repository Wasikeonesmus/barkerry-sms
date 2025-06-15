from django.db import migrations, models

def generate_sku(apps, schema_editor):
    Product = apps.get_model('core', 'Product')
    for i, product in enumerate(Product.objects.all(), 1):
        product.sku = f'PROD-{i:04d}'
        product.save()

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_add_product_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='sku',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.RunPython(generate_sku),
        migrations.AlterField(
            model_name='product',
            name='sku',
            field=models.CharField(max_length=50, unique=True),
        ),
    ] 