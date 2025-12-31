from django.core.management.base import BaseCommand
from django.db.models import Sum
from products.models import Product
from orders.models import OrderItem

class Command(BaseCommand):
    help = 'Syncs historical sales data (OrderItem) to Product.units_sold'

    def handle(self, *args, **kwargs):
        self.stdout.write("Syncing sales data...")
        
        products = Product.objects.all()
        count = 0
        
        for product in products:
            # Calculate total quantity sold from OrderItems
            total_sold = OrderItem.objects.filter(product=product).aggregate(
                total=Sum('quantity')
            )['total'] or 0
            
            if total_sold != product.units_sold:
                self.stdout.write(f"Updating {product.name}: {product.units_sold} -> {total_sold}")
                product.units_sold = total_sold
                product.save()
                count += 1
                
        self.stdout.write(self.style.SUCCESS(f"Synced {count} products."))
