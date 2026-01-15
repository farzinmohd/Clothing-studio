from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncMonth
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.core.management import call_command
from django.contrib import messages
from django.core.paginator import Paginator

import csv
from reportlab.pdfgen import canvas

from orders.models import Order, OrderItem, Coupon
from products.models import Product, Category, ProductImage, ProductVariant, Review
from .forms import (
    AdminLoginForm, ProductForm, CategoryForm, CouponForm, 
    OrderStatusForm, ProductImageForm, ProductVariantForm
)


# ================= AUTHENTICATION =================
def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        form = AdminLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None and user.is_staff:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect('admin_dashboard')
            else:
                messages.error(request, 'Invalid credentials or insufficient permissions.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AdminLoginForm()
    
    return render(request, 'dashboard/login.html', {'form': form})


@login_required
def admin_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('admin_login')


# ================= ADMIN DASHBOARD =================
@staff_member_required
def admin_dashboard(request):
    total_users = User.objects.count()
    total_orders = Order.objects.count()

    total_revenue = (
        Order.objects
        .filter(status__in=['paid', 'shipped', 'delivered'])
        .aggregate(total=Sum('total_amount'))['total'] or 0
    )

    # Orders by status
    status_data = list(
        Order.objects
        .values('status')
        .annotate(count=Count('id'))
    )

    # Monthly sales
    monthly_sales = (
        Order.objects
        .filter(status__in=['paid', 'shipped', 'delivered'])
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('total_amount'))
        .order_by('month')
    )

    months = [m['month'].strftime('%b %Y') for m in monthly_sales]
    totals = [float(m['total']) for m in monthly_sales]

    # Top selling products
    top_products = (
        OrderItem.objects
        .values('product__name')
        .annotate(total_qty=Sum('quantity'))
        .order_by('-total_qty')[:5]
    )

    context = {
        'total_users': total_users,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'status_data': status_data,
        'months': months,
        'totals': totals,
        'top_products': top_products,
    }

    return render(request, 'dashboard/admin_dashboard.html', context)


# ================= PRODUCT MANAGEMENT =================
@staff_member_required
def product_list(request):
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    
    products = Product.objects.all().select_related('category')
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    if category_filter:
        products = products.filter(category_id=category_filter)
    
    products = products.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.all()
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'search_query': search_query,
        'category_filter': category_filter,
    }
    
    return render(request, 'dashboard/products/list.html', context)


@staff_member_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            
            # Handle image uploads
            images = request.FILES.getlist('images')
            for image in images:
                ProductImage.objects.create(product=product, image=image)
            
            # Handle variants (use new_variant_* fields for new products)
            sizes = request.POST.getlist('new_variant_size')
            stocks = request.POST.getlist('new_variant_stock')
            for size, stock in zip(sizes, stocks):
                if size and stock:
                    ProductVariant.objects.create(
                        product=product,
                        size=size,
                        stock=int(stock)
                    )
            
            # Recalculate total stock from variants
            from django.db.models import Sum
            total_stock = product.variants.aggregate(total=Sum('stock'))['total'] or 0
            if total_stock > 0:
                product.stock = total_stock
                product.save()
            
            messages.success(request, f'Product "{product.name}" created successfully!')
            return redirect('admin_product_list')
    else:
        form = ProductForm()
    
    context = {
        'form': form,
        'action': 'Create',
        'size_choices': ProductVariant.SIZE_CHOICES,
    }
    return render(request, 'dashboard/products/form.html', context)


@staff_member_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            
            # Handle new image uploads
            images = request.FILES.getlist('images')
            for image in images:
                ProductImage.objects.create(product=product, image=image)
            
            # Handle image deletions
            delete_images = request.POST.getlist('delete_images')
            # Filter out empty values
            delete_images = [img_id for img_id in delete_images if img_id]
            if delete_images:
                ProductImage.objects.filter(id__in=delete_images).delete()
            
            # Handle variant updates
            variant_ids = request.POST.getlist('variant_id')
            variant_sizes = request.POST.getlist('variant_size')
            variant_stocks = request.POST.getlist('variant_stock')
            
            # Update existing variants
            for vid, size, stock in zip(variant_ids, variant_sizes, variant_stocks):
                if vid:
                    variant = ProductVariant.objects.filter(id=vid, product=product).first()
                    if variant:
                        variant.size = size
                        variant.stock = int(stock) if stock else 0
                        variant.save()
            
            # Add new variants
            new_sizes = request.POST.getlist('new_variant_size')
            new_stocks = request.POST.getlist('new_variant_stock')
            for size, stock in zip(new_sizes, new_stocks):
                if size and stock:
                    ProductVariant.objects.create(
                        product=product,
                        size=size,
                        stock=int(stock)
                    )
            
            # Handle variant deletions
            delete_variants = request.POST.getlist('delete_variants')
            # Filter out empty values
            delete_variants = [var_id for var_id in delete_variants if var_id]
            if delete_variants:
                ProductVariant.objects.filter(id__in=delete_variants).delete()
            
            # Recalculate total stock from variants
            from django.db.models import Sum
            total_stock = product.variants.aggregate(total=Sum('stock'))['total'] or 0
            if total_stock > 0:
                product.stock = total_stock
                product.save()
            
            messages.success(request, f'Product "{product.name}" updated successfully!')
            return redirect('admin_product_list')
    else:
        form = ProductForm(instance=product)
    
    context = {
        'form': form,
        'action': 'Update',
        'product': product,
        'images': product.images.all(),
        'variants': product.variants.all(),
        'size_choices': ProductVariant.SIZE_CHOICES,
    }
    return render(request, 'dashboard/products/form.html', context)


@staff_member_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Product "{product_name}" deleted successfully!')
        return redirect('admin_product_list')
    
    return render(request, 'dashboard/products/delete_confirm.html', {'product': product})


@staff_member_required
def generate_product_tags(request, pk):
    """Generate AI tags for a product using its images"""
    from ai_features.tagging import predict_image_tags
    
    product = get_object_or_404(Product, pk=pk)
    
    # Get the first image
    first_image = product.images.first()
    
    if not first_image:
        return JsonResponse({
            'success': False,
            'error': 'No images found. Please upload at least one product image first.'
        })
    
    try:
        # Generate tags using AI
        img_path = first_image.image.path
        tags = predict_image_tags(img_path)
        
        # Update product tags
        product.tags = tags
        product.save()
        
        return JsonResponse({
            'success': True,
            'tags': tags,
            'message': 'AI tags generated successfully!'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error generating tags: {str(e)}'
        })


# ================= CATEGORY MANAGEMENT =================
@staff_member_required
def category_list(request):
    categories = Category.objects.annotate(product_count=Count('product')).order_by('name')
    
    context = {'categories': categories}
    return render(request, 'dashboard/categories/list.html', context)


@staff_member_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" created successfully!')
            return redirect('admin_category_list')
    else:
        form = CategoryForm()
    
    return render(request, 'dashboard/categories/form.html', {'form': form, 'action': 'Create'})


@staff_member_required
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f'Category "{category.name}" updated successfully!')
            return redirect('admin_category_list')
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'dashboard/categories/form.html', {
        'form': form, 
        'action': 'Update', 
        'category': category
    })


@staff_member_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        category_name = category.name
        category.delete()
        messages.success(request, f'Category "{category_name}" deleted successfully!')
        return redirect('admin_category_list')
    
    return render(request, 'dashboard/categories/delete_confirm.html', {'category': category})


# ================= ORDER MANAGEMENT =================
@staff_member_required
def order_list(request):
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    
    orders = Order.objects.all().select_related('user').order_by('-created_at')
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    if search_query:
        orders = orders.filter(
            Q(id__icontains=search_query) | 
            Q(user__username__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_choices': Order.STATUS_CHOICES,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'dashboard/orders/list.html', context)


@staff_member_required
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.select_related('user', 'address'), pk=pk)
    order_items = order.items.select_related('product')
    
    context = {
        'order': order,
        'order_items': order_items,
    }
    
    return render(request, 'dashboard/orders/detail.html', context)


@staff_member_required
def order_update_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == 'POST':
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, f'Order #{order.id} status updated to {order.get_status_display()}!')
            return redirect('admin_order_detail', pk=pk)
    
    return redirect('admin_order_detail', pk=pk)


# ================= USER MANAGEMENT =================
@staff_member_required
def user_list(request):
    search_query = request.GET.get('search', '')
    
    users = User.objects.all().order_by('-date_joined')
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) | 
            Q(email__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    
    return render(request, 'dashboard/users/list.html', context)


@staff_member_required
def user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    orders = Order.objects.filter(user=user).order_by('-created_at')[:10]
    total_spent = Order.objects.filter(user=user, status__in=['paid', 'shipped', 'delivered']).aggregate(total=Sum('total_amount'))['total'] or 0
    
    context = {
        'user_obj': user,
        'orders': orders,
        'total_spent': total_spent,
    }
    
    return render(request, 'dashboard/users/detail.html', context)


@staff_member_required
def user_toggle_active(request, pk):
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        user.is_active = not user.is_active
        user.save()
        status = 'activated' if user.is_active else 'blocked'
        
        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({
                'success': True,
                'is_active': user.is_active,
                'message': f'User "{user.username}" has been {status}!'
            })
        
        messages.success(request, f'User "{user.username}" has been {status}!')
    
    return redirect('admin_user_detail', pk=pk)


@staff_member_required
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    
    # Prevent deleting yourself
    if user == request.user:
        messages.error(request, 'You cannot delete your own account!')
        return redirect('admin_user_list')
    
    # Prevent deleting superusers
    if user.is_superuser:
        messages.error(request, 'Cannot delete superuser accounts!')
        return redirect('admin_user_list')
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User "{username}" has been deleted successfully!')
        return redirect('admin_user_list')
    
    return render(request, 'dashboard/users/delete_confirm.html', {'user_to_delete': user})



# ================= REVIEW MANAGEMENT =================
@staff_member_required
def review_list(request):
    rating_filter = request.GET.get('rating', '')
    
    reviews = Review.objects.all().select_related('product', 'user').order_by('-created_at')
    
    if rating_filter:
        reviews = reviews.filter(rating=rating_filter)
    
    # Pagination
    paginator = Paginator(reviews, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'rating_filter': rating_filter,
    }
    
    return render(request, 'dashboard/reviews/list.html', context)


@staff_member_required
def review_delete(request, pk):
    review = get_object_or_404(Review, pk=pk)
    
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Review deleted successfully!')
        return redirect('admin_review_list')
    
    return render(request, 'dashboard/reviews/delete_confirm.html', {'review': review})


# ================= COUPON MANAGEMENT =================
@staff_member_required
def coupon_list(request):
    coupons = Coupon.objects.all().order_by('-created_at')
    
    context = {'coupons': coupons}
    return render(request, 'dashboard/coupons/list.html', context)


@staff_member_required
def coupon_create(request):
    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            coupon = form.save()
            messages.success(request, f'Coupon "{coupon.code}" created successfully!')
            return redirect('admin_coupon_list')
    else:
        form = CouponForm()
    
    return render(request, 'dashboard/coupons/form.html', {'form': form, 'action': 'Create'})


@staff_member_required
def coupon_update(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk)
    
    if request.method == 'POST':
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            form.save()
            messages.success(request, f'Coupon "{coupon.code}" updated successfully!')
            return redirect('admin_coupon_list')
    else:
        form = CouponForm(instance=coupon)
    
    return render(request, 'dashboard/coupons/form.html', {
        'form': form, 
        'action': 'Update', 
        'coupon': coupon
    })


@staff_member_required
def coupon_delete(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk)
    
    if request.method == 'POST':
        coupon_code = coupon.code
        coupon.delete()
        messages.success(request, f'Coupon "{coupon_code}" deleted successfully!')
        return redirect('admin_coupon_list')
    
    return render(request, 'dashboard/coupons/delete_confirm.html', {'coupon': coupon})


# ================= PDF REPORT =================
@staff_member_required
def sales_report_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="sales_report.pdf"'

    p = canvas.Canvas(response)
    p.setFont("Helvetica", 12)

    y = 800
    p.drawString(200, y, "Sales Report")
    y -= 40

    orders = Order.objects.all()

    for order in orders:
        line = f"Order #{order.id} | {order.user} | {order.total_amount} | {order.status}"
        p.drawString(50, y, line)
        y -= 20

        if y < 50:
            p.showPage()
            y = 800

    p.showPage()
    p.save()
    return response


# ================= EXCEL (CSV) REPORT =================
@staff_member_required
def sales_report_excel(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sales_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Order ID', 'User', 'Total Amount', 'Status', 'Date'])

    orders = Order.objects.all()
    for order in orders:
        writer.writerow([
            order.id,
            order.user.username,
            order.total_amount,
            order.status,
            order.created_at.strftime('%Y-%m-%d')
        ])

    return response

# ================= UPDATE PRICES TRIGGER =================
@staff_member_required
def trigger_pricing_update(request):
    try:
        call_command('update_dynamic_prices')
        messages.success(request, 'Dynamic Pricing Update Triggered Successfully! 🚀')
    except Exception as e:
        messages.error(request, f'Error updating prices: {str(e)}')
    
    return redirect('admin_dashboard')
