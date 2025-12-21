from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

from products.models import Wishlist
from orders.models import OrderItem
from .models import UserProductInteraction


@receiver(post_save, sender=Wishlist)
def track_wishlist(sender, instance, created, **kwargs):
    if created:
        UserProductInteraction.objects.update_or_create(
            user=instance.user,
            product=instance.product,
            interaction_type='wishlist',
            defaults={'score': 3}
        )


@receiver(post_save, sender=OrderItem)
def track_purchase(sender, instance, created, **kwargs):
    if created:
        UserProductInteraction.objects.update_or_create(
            user=instance.order.user,
            product=instance.product,
            interaction_type='purchase',
            defaults={'score': 5}
        )
