from django.core.management.base import BaseCommand
from products.models import Product
from ai_features.dynamic_pricing_ml import predict_demand_score, calculate_new_price

class Command(BaseCommand):
    help = 'Runs AI Dynamic Pricing engine to update product prices'

    def handle(self, *args, **kwargs):
        products = Product.objects.filter(is_dynamic_pricing=True)
        
        if not products.exists():
            self.stdout.write(self.style.WARNING("No products have dynamic pricing enabled."))
            return

        self.stdout.write(f"Analyzing {products.count()} products...")

        for p in products:
            # 1. Get Score
            score = predict_demand_score(p)
            p.current_demand_score = score
            
            # 2. Calculate Price
            old_price = p.price
            new_price = calculate_new_price(p, score)
            
            # 3. Update
            p.price = new_price
            p.save()
            
            # Log
            change_pct = ((float(new_price) - float(old_price)) / float(old_price)) * 100
            
            msg = f"[{p.name}] Score: {score}/100 | Price: {old_price} -> {new_price} ({change_pct:+.1f}%)"
            
            if change_pct > 0:
                self.stdout.write(self.style.SUCCESS(msg))
            elif change_pct < 0:
                self.stdout.write(self.style.NOTICE(msg))
            else:
                self.stdout.write(msg)
