from django.contrib import admin
from .models import Category, Product, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 2   # 👈 Minimum 2 images


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name',)
    inlines = [ProductImageInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')


admin.site.register(ProductImage)
