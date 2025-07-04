from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import *
from .forms import *

def role_check(user, allowed_roles):
    return user.userrole_set.filter(role__in=allowed_roles).exists()

def admin_required(view_func):
    return user_passes_test(lambda u: role_check(u, ['admin']))(view_func)

def manager_required(view_func):
    return user_passes_test(lambda u: role_check(u, ['admin', 'manager']))(view_func)

def salesman_required(view_func):
    return user_passes_test(lambda u: role_check(u, ['admin', 'manager', 'salesman']))(view_func)

@login_required
def dashboard(request):
    context = {}
    user_roles = request.user.userrole_set.all()
    
    if role_check(request.user, ['admin']):
        # Admin dashboard
        context['products'] = Product.objects.all()[:10]
        context['orders'] = Order.objects.all()[:10]
    elif role_check(request.user, ['manager']):
        # Manager dashboard
        context['products'] = Product.objects.all()[:10]
        context['low_stock'] = Inventory.objects.filter(current_stock__lte=F('reorder_level'))
    elif role_check(request.user, ['salesman']):
        # Salesman dashboard
        context['retailers'] = Retailer.objects.filter(assigned_salesman=request.user)
        context['orders'] = Order.objects.filter(salesman=request.user)[:10]
    
    return render(request, 'inventory/dashboard.html', context)

@login_required
def product_list(request):
    products = Product.objects.all()
    return render(request, 'inventory/product_list.html', {'products': products})

# Add similar views for other models (Order, Retailer, etc.)