from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.utils import timezone

class User(AbstractUser):
    contact_number = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
        related_name='created_%(class)s'
    )
    
    class Meta:
        abstract = True
        
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

class UserRole(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('salesman', 'Salesman')
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='assigned_user_roles'  # Changed to avoid conflict
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    assigned_date = models.DateField(auto_now_add=True)
    additional_info = models.JSONField(null=True, blank=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='created_role_assignments'  # Changed to avoid conflict
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

class Category(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Supplier(BaseModel):
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    address = models.TextField()
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    tax_id = models.CharField(max_length=50)
    
    def __str__(self):
        return f"{self.name} ({self.contact_person})"

class Product(BaseModel):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    sku = models.CharField(max_length=50, unique=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    barcode = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.sku})"

class Inventory(BaseModel):
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='inventory_records'
    )
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True)
    current_stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    reorder_level = models.IntegerField(default=5, validators=[MinValueValidator(0)])
    last_stock_update = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='inventory_updates'
    )
    last_supply_date = models.DateTimeField(null=True, blank=True)
    last_purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    def __str__(self):
        return f"{self.product.name} - Stock: {self.current_stock}"

class Retailer(BaseModel):
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    address = models.TextField()
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    tax_id = models.CharField(max_length=50)
    assigned_salesman = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='managed_retailers'
    )
    
    def __str__(self):
        return f"{self.name} ({self.contact_person})"

class Order(BaseModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned')
    ]
    
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('credit_card', 'Credit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('digital_wallet', 'Digital Wallet')
    ]
    
    retailer = models.ForeignKey(Retailer, on_delete=models.CASCADE)
    order_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    salesman = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='orders_as_salesman'
    )
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    shipping_address = models.TextField()
    notes = models.TextField(blank=True)
    processed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='processed_orders'
    )
    
    def __str__(self):
        return f"Order #{self.id} - {self.retailer.name} ({self.get_status_display()})"

class OrderDetail(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        is_new = not self.pk
        old_values = None
        
        if not is_new:
            old = self.__class__.objects.get(pk=self.pk)
            old_values = {f.name: getattr(old, f.name) for f in self._meta.fields}
        
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)