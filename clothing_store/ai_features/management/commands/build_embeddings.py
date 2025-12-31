from django.core.management.base import BaseCommand
from products.models import Product
from ai_features.recommendations.similarity import FeatureExtractor, save_catalog_features
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Builds/Updates image embeddings for all products for Visual Search'

    def handle(self, *args, **options):
        self.stdout.write("Initializing Feature Extractor (loading ResNet50)...")
        extractor = FeatureExtractor()
        extractor.initialize()
        
        products = Product.objects.filter(is_active=True).exclude(images__isnull=True)
        features_dict = {}
        
        total = products.count()
        self.stdout.write(f"Processing {total} products...")
        
        count = 0
        for product in products:
            # Get the first image
            first_image = product.images.first()
            if not first_image:
                continue
                
            img_path = os.path.join(settings.MEDIA_ROOT, str(first_image.image))
            
            if not os.path.exists(img_path):
                self.stdout.write(self.style.WARNING(f"Image not found: {img_path}"))
                continue
                
            try:
                features = extractor.extract(img_path)
                features_dict[product.id] = features
                count += 1
                if count % 10 == 0:
                    self.stdout.write(f"Processed {count}/{total}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing {product.name}: {e}"))
        
        save_catalog_features(features_dict)
        self.stdout.write(self.style.SUCCESS(f"Successfully saved embeddings for {len(features_dict)} products."))
