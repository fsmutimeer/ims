# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin
# from django.contrib.auth.forms import UserChangeForm
# from django.contrib.auth import get_user_model
# from django.utils.html import format_html
# from .models import *

# # Get the custom User model
# User = get_user_model()

# class CustomUserChangeForm(UserChangeForm):
#     class Meta(UserChangeForm.Meta):
#         model = User
#         exclude = ('last_login',)  # Explicitly exclude non-editable field

# class UserRoleInline(admin.TabularInline):
#     model = UserRole
#     extra = 1
#     fk_name = 'user'  # Resolves multiple ForeignKey issue
#     fields = ('role', 'additional_info')  # Only editable fields
#     verbose_name = "User Role"
#     verbose_name_plural = "User Roles"

# class CustomUserAdmin(UserAdmin):
#     form = CustomUserChangeForm
#     inlines = [UserRoleInline]
#     list_display = ('username', 'email', 'first_name', 'last_name', 'is_active', 'contact_number')
#     list_filter = ('is_active', 'is_staff', 'is_superuser')
#     search_fields = ('username', 'email', 'first_name', 'last_name')
    
#     # Updated fieldsets without last_login
#     fieldsets = (
#         (None, {'fields': ('username', 'password')}),
#         ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'contact_number')}),
#         ('Permissions', {
#             'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
#         }),
#         ('Important dates', {'fields': ('date_joined',)}),  # Removed last_login
#     )
    
#     # Add fieldsets configuration
#     add_fieldsets = (
#         (None, {
#             'classes': ('wide',),
#             'fields': ('username', 'password1', 'password2', 'email', 'contact_number'),
#         }),
#     )
    
#     def save_formset(self, request, form, formset, change):
#         instances = formset.save(commit=False)
#         for instance in instances:
#             if isinstance(instance, UserRole) and not instance.pk:
#                 instance.created_by = request.user
#             instance.save()
#         formset.save_m2m()

# class BaseAdmin(admin.ModelAdmin):
#     """Base admin class with common functionality"""
#     exclude = ('created_by',)
#     readonly_fields = ('created_at',)
    
#     def save_model(self, request, obj, form, change):
#         """Auto-set created_by to current user for new objects"""
#         if not obj.pk and not obj.created_by and hasattr(obj, 'created_by'):
#             obj.created_by = request.user
#         super().save_model(request, obj, form, change)

# @admin.register(Category)
# class CategoryAdmin(BaseAdmin):
#     list_display = ('name', 'description', 'created_at', 'created_by')
#     search_fields = ('name', 'description')
#     list_filter = ('created_at',)

# @admin.register(Supplier)
# class SupplierAdmin(BaseAdmin):
#     list_display = ('name', 'contact_person', 'email', 'phone', 'created_at', 'created_by')
#     search_fields = ('name', 'contact_person', 'email')
#     list_filter = ('created_at',)

# @admin.register(Product)
# class ProductAdmin(BaseAdmin):
#     list_display = ('name', 'category', 'sku', 'selling_price', 'current_stock_display', 'created_by')
#     list_filter = ('category', 'created_at')
#     search_fields = ('name', 'sku', 'barcode')
    
#     def current_stock_display(self, obj):
#         inventory = obj.inventory_set.first()
#         if inventory:
#             stock = inventory.current_stock
#             color = 'green' if stock > inventory.reorder_level else 'red'
#             return format_html('<span style="color: {};">{}</span>', color, stock)
#         return 0
#     current_stock_display.short_description = 'Current Stock'
    
#     def get_queryset(self, request):
#         return super().get_queryset(request).prefetch_related('inventory_set')

# @admin.register(Inventory)
# class InventoryAdmin(BaseAdmin):
#     list_display = ('product', 'supplier', 'current_stock', 'reorder_level', 'last_stock_update', 'updated_by')
#     list_filter = ('supplier', 'last_stock_update')
#     search_fields = ('product__name', 'product__sku')
    
#     def get_queryset(self, request):
#         return super().get_queryset(request).select_related('product', 'supplier', 'updated_by')

# @admin.register(Retailer)
# class RetailerAdmin(BaseAdmin):
#     list_display = ('name', 'contact_person', 'email', 'phone', 'assigned_salesman', 'created_by')
#     list_filter = ('assigned_salesman', 'created_at')
#     search_fields = ('name', 'contact_person', 'email')
    
#     def get_queryset(self, request):
#         return super().get_queryset(request).select_related('assigned_salesman')

# @admin.register(Order)
# class OrderAdmin(BaseAdmin):
#     list_display = ('id', 'retailer', 'order_date', 'colored_status', 'total_amount', 'salesman', 'processed_by')
#     list_filter = ('status', 'order_date', 'payment_method')
#     search_fields = ('retailer__name', 'id')
    
#     def colored_status(self, obj):
#         colors = {
#             'pending': 'orange',
#             'processing': 'blue',
#             'shipped': 'purple',
#             'delivered': 'green',
#             'cancelled': 'red',
#             'returned': 'gray'
#         }
#         return format_html(
#             '<span style="color: {};">{}</span>',
#             colors.get(obj.status, 'black'),
#             obj.get_status_display()
#         )
#     colored_status.short_description = 'Status'
    
#     def get_queryset(self, request):
#         return super().get_queryset(request).select_related(
#             'retailer', 'salesman', 'processed_by'
#         )

# @admin.register(OrderDetail)
# class OrderDetailAdmin(admin.ModelAdmin):
#     list_display = ('order', 'product', 'quantity', 'unit_price', 'subtotal')
#     search_fields = ('order__id', 'product__name')
    
#     def get_queryset(self, request):
#         return super().get_queryset(request).select_related('order', 'product')

# # Register User model with custom admin
# admin.site.register(User, CustomUserAdmin)

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from django.db import transaction
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
import logging
from django.db import connection
from django.db.models import Count
from .models import Product, Order, Category, Supplier, Retailer
from .models import *
from django.http import JsonResponse
from django.urls import path
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models.functions import TruncMonth
from django.utils import timezone
import datetime

logger = logging.getLogger(__name__)
User = get_user_model()

class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        exclude = ('last_login',)

class UserRoleInline(admin.TabularInline):
    model = UserRole
    extra = 1
    fk_name = 'user'
    fields = ('role', 'additional_info')
    verbose_name = "User Role"
    verbose_name_plural = "User Roles"

class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    inlines = [UserRoleInline]
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active', 'contact_number')
    list_filter = ('is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'contact_number')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('date_joined',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email', 'contact_number'),
        }),
    )
    
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, UserRole) and not instance.pk:
                instance.created_by = request.user
            instance.save()
        formset.save_m2m()

class BaseAdmin(admin.ModelAdmin):
    """Base admin class with common functionality"""
    exclude = ('created_by',)
    readonly_fields = ('created_at',)
    
    def save_model(self, request, obj, form, change):
        """Auto-set created_by to current user for new objects"""
        try:
            if not obj.pk and not obj.created_by and hasattr(obj, 'created_by'):
                obj.created_by = request.user
            
            # Save the main object first
            super().save_model(request, obj, form, change)
            
        except IntegrityError as e:
            logger.error(f"Integrity error saving {obj.__class__.__name__}: {e}")
            raise ValidationError(f"Database integrity error: {e}")
        except Exception as e:
            logger.error(f"Error saving {obj.__class__.__name__}: {e}")
            raise

@admin.register(Category)
class CategoryAdmin(BaseAdmin):
    list_display = ('name', 'description', 'created_at', 'created_by')
    search_fields = ('name', 'description')
    list_filter = ('created_at',)

@admin.register(Supplier)
class SupplierAdmin(BaseAdmin):
    list_display = ('name', 'contact_person', 'email', 'phone', 'created_at', 'created_by')
    search_fields = ('name', 'contact_person', 'email')
    list_filter = ('created_at',)

@admin.register(Product)
class ProductAdmin(BaseAdmin):
    list_display = ('name', 'category', 'sku', 'selling_price', 'current_stock_display', 'created_by')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'sku', 'barcode')
    
    def current_stock_display(self, obj):
        inventory = obj.inventory_records.first()
        if inventory:
            stock = inventory.current_stock
            color = 'green' if stock > inventory.reorder_level else 'red'
            return format_html('<span style="color: {};">{}</span>', color, stock)
        return 0
    current_stock_display.short_description = 'Current Stock'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('inventory_records')

@admin.register(Inventory)
class InventoryAdmin(BaseAdmin):
    list_display = ('product', 'supplier', 'current_stock', 'reorder_level', 'last_stock_update', 'updated_by')
    list_filter = ('supplier', 'last_stock_update')
    search_fields = ('product__name', 'product__sku')
    
    def save_model(self, request, obj, form, change):
        if not change:  # New inventory record
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'supplier', 'updated_by')

@admin.register(Retailer)
class RetailerAdmin(BaseAdmin):
    list_display = ('name', 'contact_person', 'email', 'phone', 'assigned_salesman', 'created_by')
    list_filter = ('assigned_salesman', 'created_at')
    search_fields = ('name', 'contact_person', 'email')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('assigned_salesman')

@admin.register(Order)
class OrderAdmin(BaseAdmin):
    list_display = ('id', 'retailer', 'order_date', 'colored_status', 'total_amount', 'salesman', 'processed_by')
    list_filter = ('status', 'order_date', 'payment_method')
    search_fields = ('retailer__name', 'id')
    
    def save_model(self, request, obj, form, change):
        if not change:  # New order
            obj.processed_by = request.user
        super().save_model(request, obj, form, change)
    
    def colored_status(self, obj):
        colors = {
            'pending': 'orange',
            'processing': 'blue',
            'shipped': 'purple',
            'delivered': 'green',
            'cancelled': 'red',
            'returned': 'gray'
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    colored_status.short_description = 'Status'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'retailer', 'salesman', 'processed_by'
        )

@admin.register(OrderDetail)
class OrderDetailAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'unit_price', 'subtotal')
    search_fields = ('order__id', 'product__name')
    
    def save_model(self, request, obj, form, change):
        try:
            with transaction.atomic():
                super().save_model(request, obj, form, change)
        except Exception as e:
            logger.error(f"Error saving OrderDetail: {e}")
            raise
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'product')

admin.site.register(User, CustomUserAdmin)

# Patch admin index to add dashboard stats
original_admin_index = admin.site.index

def custom_admin_index(self, request, extra_context=None):
    if extra_context is None:
        extra_context = {}
    extra_context['total_products'] = Product.objects.count()
    extra_context['total_orders'] = Order.objects.count()
    extra_context['total_categories'] = Category.objects.count()
    extra_context['total_suppliers'] = Supplier.objects.count()
    extra_context['total_retailers'] = Retailer.objects.count()
    extra_context['total_inventory'] = Inventory.objects.count()
    return original_admin_index(request, extra_context=extra_context)
admin.site.index = custom_admin_index.__get__(admin.site)

# Set custom admin site titles from settings
from django.conf import settings
admin.site.site_header = getattr(settings, 'ADMIN_SITE_HEADER', 'Django Administration')
admin.site.site_title = getattr(settings, 'ADMIN_SITE_TITLE', 'Django site admin')
admin.site.index_title = getattr(settings, 'ADMIN_INDEX_TITLE', 'Site administration')

@staff_member_required
def admin_dashboard_charts(request):
    # Orders per month (last 6 months)
    now = timezone.now()
    six_months_ago = now - datetime.timedelta(days=180)
    months = []
    sales = []
    qs = (
        Order.objects.filter(order_date__gte=six_months_ago)
        .annotate(month=TruncMonth('order_date'))
        .values('month')
        .annotate(total=Count('id'))
        .order_by('month')
    )
    for group in qs:
        months.append(group['month'].strftime('%b %Y'))
        sales.append(group['total'])
    # Products per category
    cat_labels = []
    cat_counts = []
    for c in Category.objects.annotate(num=Count('product')).order_by('-num'):
        cat_labels.append(c.name)
        cat_counts.append(c.num)
    return JsonResponse({
        'orders_by_month': {'labels': months, 'data': sales},
        'products_by_category': {'labels': cat_labels, 'data': cat_counts},
    })

# Patch admin URLs to add chart endpoint
old_get_urls = admin.site.get_urls

def get_urls():
    urls = old_get_urls()
    custom = [path('dashboard-charts/', admin_dashboard_charts, name='admin_dashboard_charts')]
    return custom + urls
admin.site.get_urls = get_urls