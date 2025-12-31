from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User


from products.models import Wishlist, ProductImage
from orders.models import OrderItem
from .models import UserProductInteraction
from .recommendations.similarity import FeatureExtractor, load_catalog_features, save_catalog_features, tensorflow
import os
from django.conf import settings
from django.db import transaction

# Ensure TF is loaded if possible, or lazy load inside signal



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

@receiver(post_save, sender=ProductImage)
def update_product_embedding(sender, instance, created, **kwargs):
    """
    Automatically generate/update embedding when a new product image is added.
    Uses transaction.on_commit to ensure the file is actually on disk.
    """
    if created:
        def _update():
            # Lazy load logic inside to prevent import blocking
            try:
                img_path = os.path.join(settings.MEDIA_ROOT, str(instance.image))
                if os.path.exists(img_path):
                    extractor = FeatureExtractor()
                    # This might be slow (1-2s), so ideally this should be a Celery task
                    # But for now, we run it inline for immediate results.
                    new_features = extractor.extract(img_path)
                    
                    # Update Pickle
                    features_dict = load_catalog_features()
                    features_dict[instance.product.id] = new_features
                    save_catalog_features(features_dict)
                    print(f"✅ Auto-updated embedding for {instance.product.name}")
            except Exception as e:
                print(f"⚠️ Failed to auto-update embedding: {e}")

        transaction.on_commit(_update)
