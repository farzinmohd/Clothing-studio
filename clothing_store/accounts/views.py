from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import ProtectedError

from .forms import UserRegistrationForm, UserProfileForm, AddressForm
from .models import UserProfile, Address


# -------------------------
# USER REGISTRATION
# -------------------------
def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )

            # Ensure profile exists
            UserProfile.objects.get_or_create(user=user)

            auth_login(request, user)
            return redirect('home')
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


# -------------------------
# USER LOGIN
# -------------------------
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user:
            auth_login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password')

    return render(request, 'accounts/login.html')


# -------------------------
# USER LOGOUT
# -------------------------
def user_logout(request):
    auth_logout(request)
    return redirect('login')


# -------------------------
# USER PROFILE (✅ FINAL FIX)
# -------------------------
@login_required
def profile(request):
    # Always ensure profile exists
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    # Handle profile form
    if request.method == 'POST':
        form = UserProfileForm(
            request.POST,
            request.FILES,
            instance=profile
        )
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)

    # -------------------------
    # BODY MEASUREMENTS (SAFE)
    # -------------------------
    measurements = None
    if hasattr(request.user, 'body_measurements'):
        measurements = request.user.body_measurements

    # Gender flags (NO template comparison)
    is_gender_m = False
    is_gender_f = False
    if measurements and measurements.gender:
        is_gender_m = measurements.gender == 'M'
        is_gender_f = measurements.gender == 'F'

    context = {
        'form': form,
        'profile': profile,
        'measurements': measurements,
        'is_gender_m': is_gender_m,
        'is_gender_f': is_gender_f,
    }

    return render(request, 'accounts/profile.html', context)


# -------------------------
# ADDRESS LIST
# -------------------------
@login_required
def address_list(request):
    addresses = Address.objects.filter(user=request.user)
    return render(
        request,
        'accounts/address_list.html',
        {'addresses': addresses}
    )


# -------------------------
# ADD ADDRESS
# -------------------------
@login_required
def add_address(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user

            # Handle default address
            if address.is_default:
                Address.objects.filter(
                    user=request.user,
                    is_default=True
                ).update(is_default=False)

            address.save()
            return redirect('address_list')
    else:
        form = AddressForm()

    return render(
        request,
        'accounts/address_form.html',
        {'form': form}
    )


# -------------------------
# EDIT ADDRESS
# -------------------------
@login_required
def edit_address(request, address_id):
    address = get_object_or_404(
        Address,
        id=address_id,
        user=request.user
    )

    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            updated_address = form.save(commit=False)

            if updated_address.is_default:
                Address.objects.filter(
                    user=request.user,
                    is_default=True
                ).exclude(id=address.id).update(is_default=False)

            updated_address.save()
            return redirect('address_list')
    else:
        form = AddressForm(instance=address)

    return render(
        request,
        'accounts/address_form.html',
        {'form': form}
    )


# -------------------------
# DELETE ADDRESS
# -------------------------
@login_required
def delete_address(request, address_id):
    address = get_object_or_404(
        Address,
        id=address_id,
        user=request.user
    )

    if request.method == 'POST':
        try:
            address.delete()
            messages.success(request, 'Address deleted successfully')
        except ProtectedError:
            messages.error(
                request,
                'This address is used in an order and cannot be deleted.'
            )
        return redirect('address_list')

    return render(
        request,
        'accounts/address_confirm_delete.html',
        {'address': address}
    )
