from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', views.register, name='register'),
    path('pos/', views.pos, name='pos'),
    path('pos/process-sale/', views.process_sale, name='process_sale'),
    path('pos/process-payment/', views.process_payment, name='process_payment'),
    path('inventory/', views.inventory, name='inventory'),
    path('add_product/', views.add_product, name='add_product'),
    path('add_ingredient/', views.add_ingredient, name='add_ingredient'),
    path('edit_ingredient/<int:ingredient_id>/', views.edit_ingredient, name='edit_ingredient'),
    path('delete_ingredient/<int:ingredient_id>/', views.delete_ingredient, name='delete_ingredient'),
    path('update_ingredient/<int:ingredient_id>/', views.update_ingredient, name='update_ingredient'),
    path('update_ingredient_image/<int:ingredient_id>/', views.update_ingredient_image, name='update_ingredient_image'),
    path('bulk_update_stock/', views.bulk_update_stock, name='bulk_update_stock'),
    path('sales/', views.sales, name='sales'),
    path('sales/<int:sale_id>/delete/', views.delete_sale, name='delete_sale'),
    path('orders/', views.orders, name='orders'),
    path('orders/add/', views.add_order, name='add_order'),
    path('orders/<int:order_id>/delete/', views.delete_order, name='delete_order'),
    path('orders/<int:order_id>/update-status/', views.update_order_status, name='update_order_status'),
    path('expenses/', views.expenses, name='expenses'),
    path('expenses/add/', views.add_expense, name='add_expense'),
    path('expenses/<int:expense_id>/edit/', views.edit_expense, name='edit_expense'),
    path('expenses/<int:expense_id>/delete/', views.delete_expense, name='delete_expense'),
    path('settings/', views.settings_view, name='settings'),
    path('reports/', views.reports, name='reports'),
    
    # Employee management
    path('employees/', views.employees, name='employees'),
    path('employees/add/', views.add_employee, name='add_employee'),
    path('employees/<int:employee_id>/edit/', views.edit_employee, name='edit_employee'),
    path('employees/<int:employee_id>/delete/', views.delete_employee, name='delete_employee'),
    
    # Supplier management
    path('suppliers/', views.suppliers, name='suppliers'),
    path('suppliers/add/', views.add_supplier, name='add_supplier'),
    path('suppliers/<int:supplier_id>/edit/', views.edit_supplier, name='edit_supplier'),
    
    # Purchase orders
    path('purchase-orders/', views.purchase_orders, name='purchase_orders'),
    path('purchase-orders/add/', views.add_purchase_order, name='add_purchase_order'),
    path('purchase-orders/<int:order_id>/edit/', views.edit_purchase_order, name='edit_purchase_order'),
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
    path('customers/', views.customer_list, name='customers'),
    path('customers/add/', views.add_customer, name='add_customer'),
    path('customers/<int:customer_id>/delete/', views.delete_customer, name='delete_customer'),
    path('customers/<int:customer_id>/edit/', views.edit_customer, name='edit_customer'),
    path('customers/<int:customer_id>/details/', views.customer_details, name='customer_details'),
] 