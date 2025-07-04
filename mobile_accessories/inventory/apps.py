from django.apps import AppConfig

class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventory'

    def ready(self):
        # Import inside ready() to avoid circular imports
        from django.contrib.auth import get_user_model
        User = get_user_model()

        def get_current_user():
            """Helper to get the currently logged-in user"""
            from django.utils.functional import SimpleLazyObject
            from django.contrib.auth import get_user
            from django.db import close_old_connections
            
            def inner():
                from django.http import HttpRequest
                request = HttpRequest()
                user = get_user(request)
                close_old_connections()
                return user if user.is_authenticated else None
            
            return SimpleLazyObject(inner)

        # Connect signals only after all models are loaded
        from django.apps import apps
        from django.db.models import Model
        
        models_to_track = [
            'Product', 'Order', 'Supplier', 'Category', 
            'Inventory', 'Retailer', 'OrderDetail'
        ]
        
        for model_name in models_to_track:
            try:
                model = apps.get_model('inventory', model_name)
                # post_save.connect(log_create_update, sender=model, weak=False)
                # post_delete.connect(log_delete, sender=model, weak=False)
            except LookupError:
                continue