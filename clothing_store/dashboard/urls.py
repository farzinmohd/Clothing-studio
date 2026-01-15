from django.urls import path
from .views import (
    # Authentication
    admin_login, admin_logout,
    # Dashboard
    admin_dashboard,
    # Products
    product_list, product_create, product_update, product_delete, generate_product_tags,
    # Categories
    category_list, category_create, category_update, category_delete,
    # Orders
    order_list, order_detail, order_update_status,
    # Users
    user_list, user_detail, user_toggle_active, user_delete,
    # Reviews
    review_list, review_delete,
    # Coupons
    coupon_list, coupon_create, coupon_update, coupon_delete,
    # Reports
    sales_report_pdf, sales_report_excel, trigger_pricing_update
)

urlpatterns = [
    # Authentication
    path('login/', admin_login, name='admin_login'),
    path('logout/', admin_logout, name='admin_logout'),
    
    # Dashboard Home
    path('', admin_dashboard, name='admin_dashboard'),
    
    # Products
    path('products/', product_list, name='admin_product_list'),
    path('products/add/', product_create, name='admin_product_create'),
    path('products/<int:pk>/edit/', product_update, name='admin_product_update'),
    path('products/<int:pk>/delete/', product_delete, name='admin_product_delete'),
    path('products/<int:pk>/generate-tags/', generate_product_tags, name='admin_product_generate_tags'),
    
    # Categories
    path('categories/', category_list, name='admin_category_list'),
    path('categories/add/', category_create, name='admin_category_create'),
    path('categories/<int:pk>/edit/', category_update, name='admin_category_update'),
    path('categories/<int:pk>/delete/', category_delete, name='admin_category_delete'),
    
    # Orders
    path('orders/', order_list, name='admin_order_list'),
    path('orders/<int:pk>/', order_detail, name='admin_order_detail'),
    path('orders/<int:pk>/status/', order_update_status, name='admin_order_status'),
    
    # Users
    path('users/', user_list, name='admin_user_list'),
    path('users/<int:pk>/', user_detail, name='admin_user_detail'),
    path('users/<int:pk>/toggle/', user_toggle_active, name='admin_user_toggle'),
    path('users/<int:pk>/delete/', user_delete, name='admin_user_delete'),
    
    # Reviews
    path('reviews/', review_list, name='admin_review_list'),
    path('reviews/<int:pk>/delete/', review_delete, name='admin_review_delete'),
    
    # Coupons
    path('coupons/', coupon_list, name='admin_coupon_list'),
    path('coupons/add/', coupon_create, name='admin_coupon_create'),
    path('coupons/<int:pk>/edit/', coupon_update, name='admin_coupon_update'),
    path('coupons/<int:pk>/delete/', coupon_delete, name='admin_coupon_delete'),
    
    # Reports
    path('report/pdf/', sales_report_pdf, name='sales_report_pdf'),
    path('report/excel/', sales_report_excel, name='sales_report_excel'),
    path('trigger-pricing/', trigger_pricing_update, name='trigger_pricing_update'),
]
