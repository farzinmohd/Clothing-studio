from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


# -------------------------
# CATEGORY
# -------------------------
class Category(models.Model):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


# -------------------------
# PRODUCT (FINAL ✅)
# -------------------------
class Product(models.Model):
    COLOR_CHOICES = (
        ('Black', 'Black'),
        ('Blue', 'Blue'),
        ('Red', 'Red'),
        ('White', 'White'),
        ('Green', 'Green'),
        ('Brown', 'Brown'),
        ('Beige', 'Beige'),
        ('Yellow', 'Yellow'),
        ('Pink', 'Pink'),
    )

    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()

    # ✅ MAIN COLOR (AI + FILTERING)
    color = models.CharField(
        max_length=20,
        choices=COLOR_CHOICES,
        null=True,
        blank=True,
        help_text="Primary product color used for AI recommendations"
    )

    # ✅ DYNAMIC PRICING & DEMAND TRACKING
    is_dynamic_pricing = models.BooleanField(default=True, help_text="Enable AI-driven price adjustments")
    base_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Original price before AI adjustment")
    view_count = models.PositiveIntegerField(default=0)
    cart_add_count = models.PositiveIntegerField(default=0)
    units_sold = models.PositiveIntegerField(default=0)
    current_demand_score = models.IntegerField(default=50, help_text="0-100 score. 50 is neutral.")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# -------------------------
# PRODUCT IMAGE
# -------------------------
class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        related_name='images',
        on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to='product_images/')

    def __str__(self):
        return f"Image for {self.product.name}"


# -------------------------
# PRODUCT VARIANT
# -------------------------
class ProductVariant(models.Model):
    SIZE_CHOICES = (
        ('S', 'S / 38'),
        ('M', 'M / 40'),
        ('L', 'L / 42'),
        ('XL', 'XL / 44'),
    )

    product = models.ForeignKey(
        Product,
        related_name='variants',
        on_delete=models.CASCADE
    )
    size = models.CharField(max_length=5, choices=SIZE_CHOICES)
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('product', 'size')

    def __str__(self):
        return f"{self.product.name} - {self.size}"




# -------------------------
# REVIEW
# -------------------------
class Review(models.Model):
    product = models.ForeignKey(
        Product,
        related_name='reviews',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'user')

    def __str__(self):
        return f"{self.product.name} - {self.rating}⭐"


# -------------------------
# WISHLIST
# -------------------------
class Wishlist(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='wishlists'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='wishlisted_products'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} ❤️ {self.product.name}"


# -------------------------
# SIGNALS (STOCK SYNC)
# -------------------------
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum

@receiver(post_save, sender=ProductVariant)
@receiver(post_delete, sender=ProductVariant)
def update_product_stock(sender, instance, **kwargs):
    """
    Auto-update Product stock whenever a Variant is saved or deleted.
    Main Product Stock = Sum of all Variant Stocks
    """
    product = instance.product
    total_stock = product.variants.aggregate(total=Sum('stock'))['total'] or 0
    
    # Only update if changed to avoid recursion loops (though save logic is clean)
    if product.stock != total_stock:
        product.stock = total_stock
        product.save()
