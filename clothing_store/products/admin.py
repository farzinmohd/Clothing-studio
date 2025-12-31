from django.contrib import admin
from .models import (
    Category, Product, ProductImage,
    ProductVariant, Review
)

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 2


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ('size', 'stock')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'category',
        'price', 'color', 'tags',  # ✅ Show tags
        'stock', 'is_active'
    )
    list_filter = ('category', 'color', 'is_active')
    search_fields = ('name',)
    inlines = [ProductImageInline, ProductVariantInline]
    actions = ['auto_tag_products']

    @admin.action(description='🏷️ Auto-Generate Tags (AI)')
    def auto_tag_products(self, request, queryset):
        from ai_features.tagging import predict_image_tags
        from django.conf import settings
        import os

        count = 0
        for product in queryset:
            first_img = product.images.first()
            if first_img:
                try:
                    img_path = os.path.join(settings.MEDIA_ROOT, str(first_img.image))
                    tags = predict_image_tags(img_path)
                    
                    product.tags = tags
                    product.save()
                    count += 1
                except Exception as e:
                    self.message_user(request, f"Error tagging {product.name}: {e}", level='error')
        
        self.message_user(request, f"Successfully tagged {count} products!")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__name', 'user__username')


admin.site.register(ProductImage)
admin.site.register(ProductVariant)
