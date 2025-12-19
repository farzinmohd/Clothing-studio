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


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'category',
        'price', 'color',  # ✅ SHOW COLOR
        'stock', 'is_active'
    )
    list_filter = ('category', 'color', 'is_active')
    search_fields = ('name',)
    inlines = [ProductImageInline, ProductVariantInline]


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
