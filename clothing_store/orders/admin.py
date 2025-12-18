from django.contrib import admin
from .models import Order, OrderItem, Coupon


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'size', 'color', 'quantity', 'price')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'total_amount',
        'discount_amount',
        'final_amount',
        'status',
        'created_at'
    )
    list_filter = ('status', 'created_at')
    list_editable = ('status',)
    search_fields = ('user__username',)
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'size', 'color', 'quantity', 'price')


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'discount_type',
        'discount_value',
        'min_order_amount',
        'expiry_date',
        'active'
    )
    list_filter = ('active', 'discount_type')
    search_fields = ('code',)
