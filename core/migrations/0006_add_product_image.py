from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_add_product_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='products/'),
        ),
    ] 