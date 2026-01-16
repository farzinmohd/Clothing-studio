# Generated manually for adding max_price field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0010_product_tags'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='max_price',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Maximum price limit for dynamic pricing', max_digits=10, null=True),
        ),
    ]
