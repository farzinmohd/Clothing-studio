from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from products.models import Product, ProductVariant
from orders.models import Order, OrderItem
from ai_features.collaborative_filtering import get_collaborative_recommendations
import random

class Command(BaseCommand):
    help = 'Seeds order data to test Collaborative Filtering'

    def handle(self, *args, **kwargs):
        self.stdout.write("Checking data availability...")
        
        products = list(Product.objects.filter(is_active=True)[:5])
        if len(products) < 2:
            self.stdout.write(self.style.ERROR("Need at least 2 products to test!"))
            return

        # Ensure we have a few users
        users = []
        for i in range(3):
            u, _ = User.objects.get_or_create(username=f'test_user_{i}', defaults={'email': f'test{i}@example.com'})
            users.append(u)

        p1 = products[0]
        p2 = products[1]
        
        self.stdout.write(f"Creating pattern: People who buy {p1.name} also buy {p2.name}...")

        # Create Orders
        # User 0 buys P1 and P2
        self.create_order(users[0], [p1, p2])
        # User 1 buys P1 and P2
        self.create_order(users[1], [p1, p2])
        # User 2 buys P1 only
        self.create_order(users[2], [p1])

        self.stdout.write(self.style.SUCCESS("Data Seeded! Testing Algorithm..."))

        # TEST
        recs = get_collaborative_recommendations(p1.id)
        self.stdout.write(f"\n--- Recommendations for {p1.name} ---")
        if recs:
            for r in recs:
                self.stdout.write(f" -> {r.name}")
            
            if p2 in recs:
                self.stdout.write(self.style.SUCCESS(f"\nSUCCESS: {p2.name} found in recommendations!"))
            else:
                self.stdout.write(self.style.WARNING(f"\nWARNING: {p2.name} NOT found. (Maybe correlation too weak?)"))
        else:
            self.stdout.write(self.style.WARNING("No recommendations returned."))

    def create_order(self, user, product_list):
        order = Order.objects.create(
            user=user,
            total_amount=1000,
            status='delivered'
        )
        for p in product_list:
            # Need a variant logic, taking first available
            variant = p.variants.first()
            size = variant.size if variant else 'M'
            
            OrderItem.objects.create(
                order=order,
                product=p,
                size=size,
                quantity=1,
                price=p.price
            )
