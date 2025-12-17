from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages

from .forms import UserRegistrationForm
from .models import UserProfile
from .forms import UserRegistrationForm, UserProfileForm
from django.contrib.auth.decorators import login_required



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