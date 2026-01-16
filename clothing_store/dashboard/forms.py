from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from products.models import Product, Category, ProductImage, ProductVariant, Review
from orders.models import Order, Coupon


# ================= AUTHENTICATION =================
class AdminLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )


# ================= PRODUCT FORMS =================
class ProductForm(forms.ModelForm):
    # Override stock field to make it optional
    stock = forms.IntegerField(
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text='Enter total stock. Will be auto-calculated from variants if you add size variants.'
    )
    
    class Meta:
        model = Product
        fields = [
            'category', 'name', 'description', 'price', 'stock', 'color', 'tags',
            'is_dynamic_pricing', 'base_price', 'max_price', 'view_count', 'cart_add_count', 
            'units_sold', 'current_demand_score', 'is_active'
        ]
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Product Description'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'color': forms.Select(attrs={'class': 'form-select'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Shirt, Casual, Red'}),
            'is_dynamic_pricing': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'base_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'view_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'cart_add_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'units_sold': forms.NumberInput(attrs={'class': 'form-control'}),
            'current_demand_score': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'base_price': 'Original price before AI adjustment',
            'max_price': 'Maximum price ceiling (optional). Price will never exceed this amount.',
            'current_demand_score': '0-100 score. 50 is neutral.',
            'tags': 'Manually enter tags (e.g., Shirt, Casual, Red) or use AI generation when editing.',
        }
    
    def clean_stock(self):
        """Ensure stock defaults to 0 if not provided"""
        stock = self.cleaned_data.get('stock')
        return stock if stock is not None else 0


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
        }


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['size', 'stock']
        widgets = {
            'size': forms.Select(attrs={'class': 'form-select'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
        }


# ================= CATEGORY FORM =================
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Category Name'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# ================= ORDER FORMS =================
class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


# ================= COUPON FORM =================
class CouponForm(forms.ModelForm):
    expiry_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    class Meta:
        model = Coupon
        fields = ['code', 'discount_type', 'discount_value', 'min_order_amount', 'expiry_date', 'active']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'COUPON CODE'}),
            'discount_type': forms.Select(attrs={'class': 'form-select'}),
            'discount_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'min_order_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# ================= USER MANAGEMENT FORM =================
class UserStatusForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['is_active']
        widgets = {
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
