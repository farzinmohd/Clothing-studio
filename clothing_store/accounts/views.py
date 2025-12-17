from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages

from .forms import UserRegistrationForm
from .models import UserProfile
from .forms import UserRegistrationForm, UserProfileForm
from django.contrib.auth.decorators import login_required
from .models import Address
from .forms import AddressForm


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

            # Create user profile automatically
            UserProfile.objects.create(user=user)

            # Auto login after registration
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


@login_required
def profile(request):
    profile = request.user.userprofile

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'accounts/profile.html', {'form': form})




@login_required
def address_list(request):
    addresses = Address.objects.filter(user=request.user)
    return render(
        request,
        'accounts/address_list.html',
        {'addresses': addresses}
    )


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
