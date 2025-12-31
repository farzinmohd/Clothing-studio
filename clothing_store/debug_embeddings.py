import pickle
import os
from django.conf import settings
from products.models import Product

def check():
    path = os.path.join(settings.MEDIA_ROOT, 'ai_features', 'product_embeddings.pkl')
    
    if not os.path.exists(path):
        print("Embeddings file missing!")
        return

    with open(path, 'rb') as f:
        data = pickle.load(f)
        
    db_count = Product.objects.count()
    emb_count = len(data)
    
    print(f"DB_PRODUCTS_COUNT: {db_count}")
    print(f"EMBEDDINGS_COUNT: {emb_count}")
    
    # List products in DB but missing from embeddings
    done_ids = data.keys()
    missing_prods = Product.objects.exclude(id__in=done_ids)
    
    if missing_prods.exists():
        print(f"MISSING_FROM_AI: {[p.name for p in missing_prods]}")
    else:
        print("ALL_SYNCED")

check()
