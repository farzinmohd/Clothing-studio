from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required

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

            # 🔐 Profile will also be created by signals (safe double protection)
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

        if user is not None:
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
# USER PROFILE (🔥 FIXED)
# -------------------------
@login_required
def profile(request):
    # ✅ SAFE: creates profile if missing
    profile, created = UserProfile.objects.get_or_create(user=request.user)

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

    return render(request, 'accounts/profile.html', {
        'form': form,
        'profile': profile
    })


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