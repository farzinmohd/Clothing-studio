from django.core.management.base import BaseCommand
import pickle
import os
from django.conf import settings
from products.models import Product

class Command(BaseCommand):
    help = 'Diffs DB products vs AI Embeddings'

    def handle(self, *args, **options):
        path = os.path.join(settings.MEDIA_ROOT, 'ai_features', 'product_embeddings.pkl')
        
        if not os.path.exists(path):
            self.stdout.write("Embeddings file missing!")
            return

        with open(path, 'rb') as f:
            data = pickle.load(f)
            
        db_count = Product.objects.count()
        emb_count = len(data)
        
        with open('debug_report.txt', 'w') as out:
            out.write(f"DB_PRODUCTS_COUNT: {db_count}\n")
            out.write(f"EMBEDDINGS_COUNT: {emb_count}\n")
            
            done_ids = data.keys()
            missing_prods = Product.objects.exclude(id__in=done_ids)
            
            if missing_prods.exists():
                out.write(f"MISSING_FROM_AI_COUNT: {missing_prods.count()}\n")
                # Print first 5 missing
                for p in missing_prods[:5]:
                    out.write(f" - {p.name} (has_image: {p.images.exists()})\n")
            else:
                out.write("ALL_SYNCED\n")
