from django.db import models
from django.contrib.auth.models import User
from products.models import Product


class Order(models.Model):
    PAYMENT_METHODS = (
        ('COD', 'Cash on Delivery'),
        ('ONLINE', 'Online Payment'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=[
            ('Pending', 'Pending'),
            ('Paid', 'Paid'),
            ('Shipped', 'Shipped'),
            ('Delivered', 'Delivered'),
            ('Cancelled', 'Cancelled'),
        ],
        default='Pending'
    )
    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_METHODS,
        default='COD'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id}"



class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} (x{self.quantity})"
