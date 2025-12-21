from django.db import models
from django.contrib.auth.models import User
from products.models import Product


class UserProductInteraction(models.Model):
    VIEW = 'view'
    WISHLIST = 'wishlist'
    PURCHASE = 'purchase'

    INTERACTION_CHOICES = [
        (VIEW, 'Viewed'),
        (WISHLIST, 'Wishlisted'),
        (PURCHASE, 'Purchased'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    interaction_type = models.CharField(
        max_length=20,
        choices=INTERACTION_CHOICES
    )
    score = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product', 'interaction_type')

    def __str__(self):
        return f"{self.user} - {self.product} ({self.interaction_type})"
