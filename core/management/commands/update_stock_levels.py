from django.core.management.base import BaseCommand
from core.models import Product, StockHistory
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Updates stock levels for all products to be above their reorder points'

    def handle(self, *args, **options):
        # Get the first superuser for creating stock history records
        admin_user = User.objects.filter(is_superuser=True).first()
        
        if not admin_user:
            self.stdout.write(self.style.ERROR('No superuser found. Please create a superuser first.'))
            return

        products = Product.objects.all()
        updated_count = 0

        for product in products:
            if product.current_stock <= product.reorder_point:
                # Set current stock to be 20% above reorder point
                new_stock = int(product.reorder_point * 1.2) + 1
                old_stock = product.current_stock
                
                # Update product stock
                product.current_stock = new_stock
                product.save()

                # Create stock history record
                StockHistory.objects.create(
                    product=product,
                    transaction_type='adjustment',
                    quantity=new_stock - old_stock,
                    previous_stock=old_stock,
                    new_stock=new_stock,
                    unit_price=product.cost_price,
                    total_price=float(product.cost_price) * (new_stock - old_stock),
                    notes='Stock level adjustment to fix low stock alerts',
                    created_by=admin_user
                )

                updated_count += 1
                self.stdout.write(f'Updated {product.name}: {old_stock} -> {new_stock}')

        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count} products')) 