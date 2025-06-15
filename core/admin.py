from django.contrib import admin
from .models import (
    User, Ingredient, Product, RecipeItem, Sale, Order, Expense, 
    MpesaTransaction, Customer, Category, ProductVariant, StockHistory,
    CustomerPurchase, Recipe, RecipeIngredient, ActivityLog, EmployeeAttendance,
    Employee, Supplier, SupplierProduct, PurchaseOrder, PurchaseOrderItem
)
from django.contrib.auth.admin import UserAdmin

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'current_stock', 'reorder_point', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'sku')
    ordering = ('name',)

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('customer__name', 'id')
    ordering = ('-created_at',)

class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'product', 'qty', 'price', 'payment_type', 'date')
    list_filter = ('payment_type', 'date')
    search_fields = ('customer__name', 'product__name')
    ordering = ('-date',)

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'loyalty_points', 'total_purchases')
    search_fields = ('name', 'phone', 'email')
    ordering = ('name',)

class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('category', 'amount', 'description', 'date', 'created_by')
    list_filter = ('category', 'date')
    search_fields = ('description',)
    ordering = ('-date',)

class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('user', 'position', 'salary', 'created_at')
    list_filter = ('position', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    ordering = ('-created_at',)

class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone', 'email', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'contact_person', 'phone', 'email')
    ordering = ('name',)

class SupplierProductAdmin(admin.ModelAdmin):
    list_display = ('supplier', 'product', 'supplier_price', 'min_order_quantity', 'is_preferred')
    list_filter = ('is_preferred', 'supplier')
    search_fields = ('supplier__name', 'product__name')
    ordering = ('supplier', 'product')

class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'supplier', 'status', 'order_date', 'expected_delivery_date', 'total_amount')
    list_filter = ('status', 'order_date', 'supplier')
    search_fields = ('order_number', 'supplier__name')
    ordering = ('-order_date',)

class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ('purchase_order', 'product', 'quantity', 'unit_price', 'total_price', 'received_quantity')
    list_filter = ('purchase_order__status',)
    search_fields = ('purchase_order__order_number', 'product__name')
    ordering = ('purchase_order', 'product')

# Register models with their admin classes
admin.site.register(User, CustomUserAdmin)
admin.site.register(Category)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductVariant)
admin.site.register(Ingredient)
admin.site.register(RecipeItem)
admin.site.register(Recipe)
admin.site.register(RecipeIngredient)
admin.site.register(Sale, SaleAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Expense, ExpenseAdmin)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(CustomerPurchase)
admin.site.register(StockHistory)
admin.site.register(MpesaTransaction)
admin.site.register(ActivityLog)
admin.site.register(EmployeeAttendance)
admin.site.register(Employee, EmployeeAdmin)
admin.site.register(Supplier, SupplierAdmin)
admin.site.register(SupplierProduct, SupplierProductAdmin)
admin.site.register(PurchaseOrder, PurchaseOrderAdmin)
admin.site.register(PurchaseOrderItem, PurchaseOrderItemAdmin)
