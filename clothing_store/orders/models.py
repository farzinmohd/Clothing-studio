from django.db import models
from django.contrib.auth.models import User
from products.models import Product
from accounts.models import Address
from django.utils import timezone


class Coupon(models.Model):
    DISCOUNT_TYPE = (
        ('percent', 'Percentage'),
        ('flat', 'Flat Amount'),
    )

    code = models.CharField(max_length=20, unique=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)

    min_order_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )

    expiry_date = models.DateField()
    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self, order_total):
        if not self.active:
            return False
        if timezone.now().date() > self.expiry_date:
            return False
        if order_total < self.min_order_amount:
            return False
        return True

    def __str__(self):
        return self.code


class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('return_requested', 'Return Requested'),
        ('returned', 'Returned'),
        ('cancelled', 'Cancelled'),
    )

    PAYMENT_METHODS = (
        ('COD', 'Cash on Delivery'),
        ('ONLINE', 'Online Payment'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    address = models.ForeignKey(
        Address,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    # 🔥 COUPON FIELDS (NEW)
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )

    shipping_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )

    final_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_METHODS,
        default='COD'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def can_cancel(self):
        return self.status in ['pending', 'paid']

    def can_return(self):
        # Allow returns if status is delivered and within 7 days
        if self.status == 'delivered':
            delta = timezone.now() - self.updated_at
            if delta.days <= 7:
                return True
        return False

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='items',
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    size = models.CharField(max_length=10)
    color = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} ({self.size}, {self.color}) x {self.quantity}"
