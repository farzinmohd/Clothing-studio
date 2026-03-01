import sys
import os

sys.path.append(r"d:\django_ecommerce\clothing_store")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "clothing_store.settings")
import django
django.setup()

from ai_features.size_recommendation.model import predict_size

print(predict_size(185, 80, 30, 'M'))
