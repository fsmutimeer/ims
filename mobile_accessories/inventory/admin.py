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
from django.db.models import Count, F, Sum, ExpressionWrapper, DecimalField
from .models import Product, Order, OrderDetail, Category, Supplier, Retailer, Inventory, UserRole
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
    # Add total revenue and profit
    total_revenue = Order.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    # Profit: sum((unit_price - product.cost_price) * quantity) for all order details
    profit_qs = OrderDetail.objects.select_related('product').annotate(
        profit=ExpressionWrapper(
            (F('unit_price') - F('product__cost_price')) * F('quantity'),
            output_field=DecimalField(max_digits=12, decimal_places=2)
        )
    )
    total_profit = profit_qs.aggregate(total=Sum('profit'))['total'] or 0
    extra_context['total_revenue'] = total_revenue
    extra_context['total_profit'] = total_profit
    return original_admin_index(request, extra_context=extra_context)
admin.site.index = custom_admin_index.__get__(admin.site)

# Set custom admin site titles from settings
from django.conf import settings
admin.site.site_header = getattr(settings, 'ADMIN_SITE_HEADER', 'Django Administration')
admin.site.site_title = getattr(settings, 'ADMIN_SITE_TITLE', 'Django site admin')
admin.site.index_title = getattr(settings, 'ADMIN_INDEX_TITLE', 'Site administration')

@staff_member_required
def admin_dashboard_charts(request):
    now = timezone.now()
    orders_range = request.GET.get('orders_range', 'month')
    mode = request.GET.get('mode', 'month')

    # Helper to generate all periods in range
    def get_periods(start, end, kind):
        periods = []
        cur = start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if kind == 'month':
            while cur <= end:
                periods.append(cur)
                if cur.month == 12:
                    cur = cur.replace(year=cur.year+1, month=1)
                else:
                    cur = cur.replace(month=cur.month+1)
        elif kind == 'week':
            cur = cur - datetime.timedelta(days=cur.weekday())
            while cur <= end:
                periods.append(cur)
                cur += datetime.timedelta(weeks=1)
        elif kind == 'year':
            while cur <= end:
                periods.append(cur.replace(month=1))
                cur = cur.replace(year=cur.year+1)
        return periods

    # Orders by selectable range
    if orders_range == 'week':
        start = now - datetime.timedelta(weeks=12)
        trunc = TruncWeek('order_date')
        label_fmt = '%W %b %Y'
        period_kind = 'week'
    elif orders_range == 'year':
        start = now - datetime.timedelta(days=365*5)
        trunc = TruncYear('order_date')
        label_fmt = '%Y'
        period_kind = 'year'
    elif orders_range == 'all':
        start = Order.objects.earliest('order_date').order_date if Order.objects.exists() else now
        trunc = TruncYear('order_date')
        label_fmt = '%Y'
        period_kind = 'year'
    else:  # month (last 6 months)
        start = now - datetime.timedelta(days=180)
        trunc = TruncMonth('order_date')
        label_fmt = '%b %Y'
        period_kind = 'month'
    end = now
    all_periods = get_periods(start, end, period_kind)
    qs = (
        Order.objects.filter(order_date__gte=start)
        .annotate(period=trunc)
        .values('period')
        .annotate(total=Count('id'))
        .order_by('period')
    )
    period_map = {g['period'].strftime(label_fmt): g['total'] for g in qs if g['period']}
    orders_by_labels = [p.strftime(label_fmt) for p in all_periods]
    orders_by_data = [period_map.get(p.strftime(label_fmt), 0) for p in all_periods]

    # Products by category (pie)
    cat_labels = []
    cat_counts = []
    for c in Category.objects.annotate(num=Count('product')).order_by('-num'):
        cat_labels.append(c.name)
        cat_counts.append(c.num)

    # Products added by month (bar, always last 12 months)
    prod_start = (now.replace(day=1) - datetime.timedelta(days=365)).replace(day=1)
    prod_periods = get_periods(prod_start, now, 'month')
    prod_qs = (
        Product.objects.filter(created_at__gte=prod_start)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Count('id'))
        .order_by('month')
    )
    prod_map = {g['month'].strftime('%b %Y'): g['total'] for g in prod_qs if g['month']}
    prod_months = [p.strftime('%b %Y') for p in prod_periods]
    prod_counts = [prod_map.get(p, 0) for p in prod_months]

    # Orders vs Products (comparison line, same periods as orders_by)
    if mode == 'week':
        trunc_cmp = TruncWeek('order_date')
        trunc_cmp_prod = TruncWeek('created_at')
        label_fmt_cmp = '%W %b %Y'
        cmp_kind = 'week'
    else:
        trunc_cmp = TruncMonth('order_date')
        trunc_cmp_prod = TruncMonth('created_at')
        label_fmt_cmp = '%b %Y'
        cmp_kind = 'month'
    cmp_periods = get_periods(start, end, cmp_kind)
    # Orders for comparison
    cmp_orders = (
        Order.objects.filter(order_date__gte=start)
        .annotate(period=trunc_cmp)
        .values('period')
        .annotate(total=Count('id'))
        .order_by('period')
    )
    cmp_orders_map = {g['period'].strftime(label_fmt_cmp): g['total'] for g in cmp_orders if g['period']}
    cmp_labels = [p.strftime(label_fmt_cmp) for p in cmp_periods]
    cmp_orders_data = [cmp_orders_map.get(label, 0) for label in cmp_labels]
    # Products for comparison (by created_at)
    cmp_products = (
        Product.objects.filter(created_at__gte=start)
        .annotate(period=trunc_cmp_prod)
        .values('period')
        .annotate(total=Count('id'))
        .order_by('period')
    )
    cmp_products_map = {g['period'].strftime(label_fmt_cmp): g['total'] for g in cmp_products if g['period']}
    cmp_products_data = [cmp_products_map.get(label, 0) for label in cmp_labels]

    # Orders by Retailer (top 5)
    retailer_qs = (
        Order.objects.values('retailer__name')
        .annotate(total=Count('id'))
        .order_by('-total')[:5]
    )
    retailer_labels = [g['retailer__name'] or 'Unknown' for g in retailer_qs]
    retailer_data = [g['total'] for g in retailer_qs]

    # FIX: Products by Supplier (top 5) via Inventory
    supplier_qs = (
        Inventory.objects.values('supplier__name')
        .annotate(total=Count('product', distinct=True))
        .order_by('-total')[:5]
    )
    supplier_labels = [g['supplier__name'] or 'Unknown' for g in supplier_qs]
    supplier_data = [g['total'] for g in supplier_qs]

    # Profit by month
    profit_by_month_labels = prod_months  # Use same months as products_by_month
    profit_by_month_data = []
    for month_label in profit_by_month_labels:
        # Get first day of month
        try:
            dt = datetime.datetime.strptime(month_label, '%b %Y')
        except Exception:
            profit_by_month_data.append(0)
            continue
        month_start = dt.replace(day=1)
        if month_start.month == 12:
            next_month = month_start.replace(year=month_start.year+1, month=1, day=1)
        else:
            next_month = month_start.replace(month=month_start.month+1, day=1)
        order_ids = Order.objects.filter(order_date__gte=month_start, order_date__lt=next_month).values_list('id', flat=True)
        profit_qs = OrderDetail.objects.filter(order_id__in=order_ids).select_related('product').annotate(
            profit=ExpressionWrapper(
                (F('unit_price') - F('product__cost_price')) * F('quantity'),
                output_field=DecimalField(max_digits=12, decimal_places=2)
            )
        )
        profit = profit_qs.aggregate(total=Sum('profit'))['total'] or 0
        profit_by_month_data.append(float(profit))
    # Profit by year
    profit_by_year_labels = []
    profit_by_year_data = []
    years = set()
    for month_label in prod_months:
        try:
            dt = datetime.datetime.strptime(month_label, '%b %Y')
            years.add(dt.year)
        except Exception:
            continue
    years = sorted(list(years))
    for year in years:
        year_start = datetime.datetime(year, 1, 1)
        year_end = datetime.datetime(year+1, 1, 1)
        order_ids = Order.objects.filter(order_date__gte=year_start, order_date__lt=year_end).values_list('id', flat=True)
        profit_qs = OrderDetail.objects.filter(order_id__in=order_ids).select_related('product').annotate(
            profit=ExpressionWrapper(
                (F('unit_price') - F('product__cost_price')) * F('quantity'),
                output_field=DecimalField(max_digits=12, decimal_places=2)
            )
        )
        profit = profit_qs.aggregate(total=Sum('profit'))['total'] or 0
        profit_by_year_labels.append(str(year))
        profit_by_year_data.append(float(profit))

    return JsonResponse({
        'orders_by': {'labels': orders_by_labels, 'data': orders_by_data},
        'products_by_category': {'labels': cat_labels, 'data': cat_counts},
        'products_by_month': {'labels': prod_months, 'data': prod_counts},
        'orders_vs_products': {'labels': cmp_labels, 'orders': cmp_orders_data, 'products': cmp_products_data},
        'orders_by_retailer': {'labels': retailer_labels, 'data': retailer_data},
        'products_by_supplier': {'labels': supplier_labels, 'data': supplier_data},
        'profit_by_month': {'labels': profit_by_month_labels, 'data': profit_by_month_data},
        'profit_by_year': {'labels': profit_by_year_labels, 'data': profit_by_year_data},
    })

# Patch admin URLs to add chart endpoint
old_get_urls = admin.site.get_urls

def get_urls():
    urls = old_get_urls()
    custom = [path('dashboard-charts/', admin_dashboard_charts, name='admin_dashboard_charts')]
    return custom + urls
admin.site.get_urls = get_urls