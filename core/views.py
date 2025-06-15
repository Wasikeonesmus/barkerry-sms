from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse
from .models import Sale, Order, Ingredient, Expense, Product, MpesaTransaction, Customer, OrderItem, Employee, User, Supplier, PurchaseOrder, PurchaseOrderItem, StockUpdate, Category, StockHistory, Settings
from .forms import CustomUserCreationForm, IngredientForm, CustomerForm
import json
import requests
import base64
from datetime import datetime, timedelta
import os
import logging
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
import csv
import re
from django.urls import reverse
from django.db import transaction

logger = logging.getLogger(__name__)

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'registration/login.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully! You can now login.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

# Create your views here.

@login_required
def dashboard(request):
    today = timezone.now().date()
    
    # Get today's sales
    today_sales = Sale.objects.filter(date__date=today).aggregate(
        total=Sum(ExpressionWrapper(F('price') * F('qty'), output_field=DecimalField()))
    )['total'] or 0
    
    # Get pending orders count
    pending_orders = Order.objects.filter(status='pending').count()
    
    # Get low stock items
    low_stock_items = Product.objects.filter(current_stock__lte=F('reorder_point')).count()
    
    # Get today's expenses
    today_expenses = Expense.objects.filter(created_at__date=today).aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Get recent sales
    recent_sales = Sale.objects.select_related('product').order_by('-date')[:5]
    
    # Get pending orders list
    pending_orders_list = Order.objects.select_related('customer', 'created_by').filter(status='pending')[:5]
    
    context = {
        'today_sales': today_sales,
        'pending_orders': pending_orders,
        'low_stock_items': low_stock_items,
        'today_expenses': today_expenses,
        'recent_sales': recent_sales,
        'pending_orders_list': pending_orders_list,
    }
    return render(request, 'dashboard.html', context)

@login_required
def pos(request):
    products = Product.objects.filter(is_active=True).order_by('category__name', 'name')
    categories = Category.objects.all()
    
    # Handle adding product from inventory
    add_product_id = request.GET.get('add_product')
    if add_product_id:
        try:
            product = Product.objects.get(id=add_product_id)
            if product.is_active:
                # Add to session cart
                cart = request.session.get('cart', {})
                cart[str(product.id)] = cart.get(str(product.id), 0) + 1
                request.session['cart'] = cart
                messages.success(request, f'Added {product.name} to cart')
            else:
                messages.error(request, 'This product is not available')
        except Product.DoesNotExist:
            messages.error(request, 'Product not found')
    
    return render(request, 'pos.html', {
        'title': 'Point of Sale',
        'products': products,
        'categories': categories
    })

@login_required
def inventory(request):
    products = Product.objects.all().order_by('category__name', 'name')
    categories = Category.objects.all()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        product_id = request.POST.get('product_id')
        
        try:
            product = Product.objects.get(id=product_id)
            
            if action == 'update_stock':
                new_stock = int(request.POST.get('new_stock', 0))
                if new_stock >= 0:
                    product.current_stock = new_stock
                    product.save()
                    messages.success(request, f'Stock updated for {product.name}')
                else:
                    messages.error(request, 'Stock cannot be negative')
                    
            elif action == 'toggle_active':
                product.is_active = not product.is_active
                product.save()
                status = 'activated' if product.is_active else 'deactivated'
                messages.success(request, f'{product.name} has been {status}')
                
        except Product.DoesNotExist:
            messages.error(request, 'Product not found')
            
    return render(request, 'inventory.html', {
        'title': 'Inventory Management',
        'products': products,
        'categories': categories
    })

@login_required
def add_ingredient(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        unit = request.POST.get('unit')
        quantity = float(request.POST.get('quantity', 0))
        alert_level = float(request.POST.get('alert_level', 0))
        image = request.FILES.get('image')
        
        ingredient = Ingredient.objects.create(
            name=name,
            unit=unit,
            quantity=quantity,
            alert_level=alert_level,
            image=image
        )
        
        # Record initial stock
        if quantity > 0:
            StockUpdate.objects.create(
                ingredient=ingredient,
                quantity_change=quantity,
                notes='Initial stock'
            )
            
        messages.success(request, f'Ingredient {name} added successfully!')
    return redirect('inventory')

@login_required
def edit_ingredient(request, ingredient_id):
    ingredient = get_object_or_404(Ingredient, id=ingredient_id)
    if request.method == 'POST':
        ingredient.name = request.POST.get('name')
        ingredient.unit = request.POST.get('unit')
        ingredient.alert_level = float(request.POST.get('alert_level', 0))
        ingredient.save()
        messages.success(request, f'Ingredient {ingredient.name} updated successfully!')
    return redirect('inventory')

@login_required
def update_stock(request, ingredient_id):
    ingredient = get_object_or_404(Ingredient, id=ingredient_id)
    if request.method == 'POST':
        quantity_change = float(request.POST.get('quantity_change'))
        ingredient.quantity += quantity_change
        ingredient.save()
        messages.success(request, f'Stock updated for {ingredient.name}!')
    return redirect('inventory')

@login_required
def sales(request):
    sales = Sale.objects.all().order_by('-date')
    return render(request, 'sales.html', {'sales': sales})

@login_required
def orders(request):
    orders = Order.objects.all().order_by('-created_at')
    products = Product.objects.all()
    return render(request, 'orders.html', {'orders': orders, 'products': products})

@login_required
def add_order(request):
    if request.method == 'POST':
        try:
            # Get form data
            customer_name = request.POST.get('customer_name')
            phone = request.POST.get('phone')
            product_id = request.POST.get('product')
            qty = int(request.POST.get('qty'))
            delivery_type = request.POST.get('delivery_type')

            # Clean phone number
            phone = re.sub(r'\D', '', phone)
            if phone.startswith('255'):
                phone = '0' + phone[3:]
            if not phone.startswith('0'):
                phone = '0' + phone

            # First try to get existing customer
            try:
                customer = Customer.objects.get(phone=phone)
                # Update customer name if it has changed
                if customer.name != customer_name:
                    customer.name = customer_name
                    customer.save()
            except Customer.DoesNotExist:
                # Create new customer
                customer = Customer.objects.create(
                    name=customer_name,
                    phone=phone,
                    email=request.POST.get('email', ''),
                    address=request.POST.get('address', '')
                )

            # Process the order
            product = get_object_or_404(Product, id=product_id)
            
            # Check stock
            if product.current_stock < qty:
                messages.error(request, f'Not enough stock for {product.name}. Available: {product.current_stock}')
                return redirect('orders')

            total_amount = product.price * qty
            delivery_address = request.POST.get('delivery_address', '')
            delivery_notes = request.POST.get('delivery_notes', '')

            # Create the order
            order = Order.objects.create(
                customer=customer,
                status='pending',
                total_amount=total_amount,
                delivery_address=delivery_address,
                delivery_notes=delivery_notes,
                delivery_type=delivery_type,
                created_by=request.user
            )

            # Add the product and quantity via OrderItem
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=qty,
                price=product.price
            )

            # Update product stock
            product.current_stock -= qty
            product.save()

            # Record stock history
            StockHistory.objects.create(
                product=product,
                quantity_change=-qty,
                notes=f'Ordered in order #{order.id}',
                created_by=request.user
            )

            messages.success(request, 'Order added successfully!')
            return redirect('orders')

        except Exception as e:
            messages.error(request, f'Error creating order: {str(e)}')
            return redirect('orders')

    return redirect('orders')

@login_required
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        order.status = new_status
        order.save()
        messages.success(request, f'Order status updated to {new_status}!')
    return redirect('orders')

@login_required
def expenses(request):
    expenses = Expense.objects.all().order_by('-date')
    return render(request, 'expenses.html', {'expenses': expenses})

@login_required
def add_expense(request):
    if request.method == 'POST':
        description = request.POST.get('description')
        category = request.POST.get('category')
        amount = float(request.POST.get('amount'))
        
        Expense.objects.create(
            description=description,
            category=category,
            amount=amount,
            date=timezone.now()
        )
        messages.success(request, 'Expense added successfully!')
    return redirect('expenses')

@login_required
def edit_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)
    if request.method == 'POST':
        expense.description = request.POST.get('description')
        expense.category = request.POST.get('category')
        expense.amount = float(request.POST.get('amount'))
        expense.save()
        messages.success(request, 'Expense updated successfully!')
    return redirect('expenses')

@login_required
@csrf_exempt
def delete_expense(request, expense_id):
    try:
        expense = get_object_or_404(Expense, id=expense_id)
        if request.method == 'POST':
            # Delete the expense
            expense.delete()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Expense deleted successfully.'
                })
            else:
                messages.success(request, 'Expense deleted successfully.')
                return redirect('expenses')
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f'Error deleting expense: {str(e)}'
            }, status=400)
        else:
            messages.error(request, f'Error deleting expense: {str(e)}')
            return redirect('expenses')

@login_required
def reports(request):
    # Get date range from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Set default dates if not provided
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    try:
        # Convert string dates to datetime objects
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Get sales data
        sales = Sale.objects.filter(date__date__range=[start_date, end_date])
        total_sales = sales.aggregate(
            total=Sum(ExpressionWrapper(F('price') * F('qty'), output_field=DecimalField()))
        )['total'] or 0
        
        # Get expenses data
        expenses = Expense.objects.filter(date__range=[start_date, end_date])
        total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
        
        # Calculate profit
        profit = total_sales - total_expenses
        
        # Get top selling products
        top_products = Sale.objects.filter(
            date__date__range=[start_date, end_date]
        ).values(
            'product__name'
        ).annotate(
            total_quantity=Sum('qty'),
            total_revenue=Sum(ExpressionWrapper(F('price') * F('qty'), output_field=DecimalField()))
        ).order_by('-total_quantity')[:5]
        
        # Get sales by payment method
        sales_by_payment = sales.values(
            'payment_type'
        ).annotate(
            total=Sum(ExpressionWrapper(F('price') * F('qty'), output_field=DecimalField()))
        ).order_by('-total')
        
        context = {
            'start_date': start_date,
            'end_date': end_date,
            'total_sales': total_sales,
            'total_expenses': total_expenses,
            'profit': profit,
            'top_products': top_products,
            'sales_by_payment': sales_by_payment,
            'sales': sales,
            'expenses': expenses,
        }
        
        return render(request, 'reports.html', context)
        
    except ValueError as e:
        messages.error(request, f"Invalid date format: {str(e)}")
        return redirect('reports')

def get_mpesa_access_token():
    try:
        # Debug: Print current working directory
        logger.debug(f"Current working directory: {os.getcwd()}")
        
        # Debug: Check if .env file exists
        env_path = os.path.join(os.getcwd(), '.env')
        logger.debug(f"Looking for .env file at: {env_path}")
        logger.debug(f".env file exists: {os.path.exists(env_path)}")
        
        consumer_key = os.getenv('MPESA_CONSUMER_KEY')
        consumer_secret = os.getenv('MPESA_CONSUMER_SECRET')
        
        # Debug logging
        logger.debug(f"Consumer Key: {consumer_key}")
        logger.debug(f"Consumer Secret: {consumer_secret}")
        
        if not consumer_key or not consumer_secret:
            logger.error("M-Pesa credentials not found in environment variables")
            raise ValueError("M-Pesa credentials not configured. Please check your .env file.")
        
        api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        auth = base64.b64encode(f"{consumer_key}:{consumer_secret}".encode()).decode()
        
        headers = {
            "Authorization": f"Basic {auth}"
        }
        
        logger.debug(f"Making request to: {api_url}")
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        data = response.json()
        logger.debug(f"Response data: {data}")
        
        if 'access_token' not in data:
            logger.error(f"Access token not found in response: {data}")
            raise ValueError("Failed to get M-Pesa access token")
            
        return data['access_token']
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error while getting M-Pesa access token: {str(e)}")
        raise ValueError(f"Network error: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting M-Pesa access token: {str(e)}")
        raise ValueError(f"Error: {str(e)}")

def initiate_mpesa_payment(phone, amount):
    try:
        access_token = get_mpesa_access_token()
        api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        
        # Format phone number (remove leading 0 and add country code)
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        elif not phone.startswith('254'):
            phone = '254' + phone
        
        # Remove any spaces or special characters
        phone = ''.join(filter(str.isdigit, phone))
        
        # Ensure amount is an integer (in KES)
        amount = int(float(amount))
        
        # Validate minimum amount
        if amount < 1:
            raise ValueError("Minimum payment amount is KES 1")
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        business_shortcode = "174379"  # Sandbox shortcode
        passkey = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"  # Sandbox passkey
        
        # Generate password
        password_str = f"{business_shortcode}{passkey}{timestamp}"
        password = base64.b64encode(password_str.encode()).decode()
        
        # Use a public callback URL for development
        callback_url = "https://upendo-bakery.herokuapp.com/mpesa/callback/"
        
        payload = {
            "BusinessShortCode": business_shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone,
            "PartyB": business_shortcode,
            "PhoneNumber": phone,
            "CallBackURL": callback_url,
            "AccountReference": "Upendo Bakery",
            "TransactionDesc": "Payment for bakery items"
        }
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"Initiating M-Pesa payment for phone: {phone}, amount: {amount}")
        logger.debug(f"Request payload: {payload}")
        
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"M-Pesa response: {data}")
        
        if data.get('ResponseCode') == '0':
            return data
        else:
            error_msg = data.get('ResponseDescription', 'Unknown error')
            logger.error(f"M-Pesa error: {error_msg}")
            raise ValueError(f"M-Pesa error: {error_msg}")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during M-Pesa payment: {str(e)}")
        raise ValueError(f"Network error: {str(e)}")
    except Exception as e:
        logger.error(f"Error during M-Pesa payment: {str(e)}")
        raise ValueError(f"Error: {str(e)}")

@login_required
@csrf_exempt
def process_sale(request):
    if request.method == 'POST':
        try:
            data = request.POST
            items = data.getlist('items[]')
            payment_type = data.get('payment_type')
            phone = data.get('phone', '')  # For Mpesa payments
            
            if not items:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No items in cart'
                })
            
            # Validate each item has a price
            for item in items:
                if 'price' not in item:
                    return JsonResponse({'success': False, 'message': 'Price missing for one or more items'})
            
            total_amount = 0
            sales = []
            
            # First, validate stock for all items
            for item in items:
                item_data = json.loads(item)
                product = get_object_or_404(Product, id=item_data['id'])
                quantity = int(item_data['quantity'])
                
                if product.current_stock < quantity:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Not enough stock for {product.name}. Available: {product.current_stock}'
                    })
            
            # If all stock checks pass, process the sales
            for item in items:
                item_data = json.loads(item)
                product = get_object_or_404(Product, id=item_data['id'])
                
                # Create the sale record
                sale = Sale.objects.create(
                    product=product,
                    qty=item_data['quantity'],
                    price=product.price,
                    payment_type=payment_type,
                    user=request.user
                )
                sales.append(sale)
                total_amount += product.price * item_data['quantity']
            
            # If it's an Mpesa payment, initiate the payment
            if payment_type == 'mpesa' and phone:
                try:
                    mpesa_response = initiate_mpesa_payment(phone, total_amount)
                    
                    # Create transaction record
                    MpesaTransaction.objects.create(
                        phone=phone,
                        amount=total_amount,
                        transaction_id=mpesa_response.get('CheckoutRequestID'),
                        status='pending'
                    )
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': 'M-Pesa prompt sent successfully. Please check your phone.'
                    })
                    
                except ValueError as e:
                    return JsonResponse({
                        'status': 'error',
                        'message': str(e)
                    })
                except Exception as e:
                    logger.error(f"Unexpected error during M-Pesa payment: {str(e)}")
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Unexpected error: {str(e)}'
                    })
            
            return JsonResponse({'status': 'success'})
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid data format'
            })
        except Exception as e:
            logger.error(f"Error processing sale: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'Error processing sale: {str(e)}'
            })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    })

@login_required
def employees(request):
    employees = Employee.objects.select_related('user').all()
    return render(request, 'employees.html', {'employees': employees})

@login_required
def add_employee(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        email = request.POST.get('email')
        role = request.POST.get('role')
        position = request.POST.get('position')
        phone = request.POST.get('phone')
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return render(request, 'add_employee.html', {
                'form_data': request.POST
            })
        
        try:
            # Create user with a default password
            user = User.objects.create_user(
                username=username,
                email=email,
                password='changeme123',  # Default password
                first_name=first_name,
                last_name='',  # Empty last name
                is_staff=True,
                role=role,  # Set role on User model
                phone=phone  # Set phone on User model
            )
            
            # Create employee profile
            Employee.objects.create(
                user=user,
                position=position,
                salary=0.00  # Default salary
            )
            
            messages.success(request, 'Employee added successfully')
            return redirect('employees')
            
        except Exception as e:
            messages.error(request, f'Error adding employee: {str(e)}')
            return render(request, 'add_employee.html', {
                'form_data': request.POST
            })
    
    return render(request, 'add_employee.html')

@login_required
def edit_employee(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    if request.method == 'POST':
        user = employee.user
        user.first_name = request.POST.get('first_name')
        user.email = request.POST.get('email')
        user.role = request.POST.get('role')
        user.phone = request.POST.get('phone')
        user.save()
        
        employee.position = request.POST.get('position')
        employee.salary = request.POST.get('salary')
        employee.save()
        
        messages.success(request, 'Employee updated successfully')
        return redirect('employees')
    return render(request, 'edit_employee.html', {'employee': employee})

@login_required
def suppliers(request):
    suppliers = Supplier.objects.all()
    return render(request, 'suppliers.html', {'suppliers': suppliers})

@login_required
def add_supplier(request):
    if request.method == 'POST':
        Supplier.objects.create(
            name=request.POST.get('name'),
            contact_person=request.POST.get('contact_person'),
            phone=request.POST.get('phone'),
            email=request.POST.get('email'),
            address=request.POST.get('address'),
            tax_number=request.POST.get('tax_number'),
            payment_terms=request.POST.get('payment_terms'),
            bank_details=request.POST.get('bank_details'),
            notes=request.POST.get('notes')
        )
        messages.success(request, 'Supplier added successfully!')
        return redirect('suppliers')
    return render(request, 'add_supplier.html')

@login_required
def edit_supplier(request, supplier_id):
    supplier = get_object_or_404(Supplier, id=supplier_id)
    if request.method == 'POST':
        supplier.name = request.POST.get('name')
        supplier.contact_person = request.POST.get('contact_person')
        supplier.phone = request.POST.get('phone')
        supplier.email = request.POST.get('email')
        supplier.address = request.POST.get('address')
        supplier.tax_number = request.POST.get('tax_number')
        supplier.payment_terms = request.POST.get('payment_terms')
        supplier.bank_details = request.POST.get('bank_details')
        supplier.notes = request.POST.get('notes')
        supplier.save()
        
        messages.success(request, 'Supplier updated successfully!')
        return redirect('suppliers')
    return render(request, 'edit_supplier.html', {'supplier': supplier})

@login_required
def purchase_orders(request):
    orders = PurchaseOrder.objects.select_related('supplier').all()
    return render(request, 'purchase_orders.html', {'orders': orders})

@login_required
def add_purchase_order(request):
    if request.method == 'POST':
        supplier = get_object_or_404(Supplier, id=request.POST.get('supplier'))
        order = PurchaseOrder.objects.create(
            supplier=supplier,
            order_number=request.POST.get('order_number'),
            order_date=request.POST.get('order_date'),
            expected_delivery_date=request.POST.get('expected_delivery_date'),
            total_amount=request.POST.get('total_amount'),
            notes=request.POST.get('notes'),
            created_by=request.user
        )
        
        # Add order items
        items = json.loads(request.POST.get('items', '[]'))
        for item in items:
            product = get_object_or_404(Product, id=item['product_id'])
            PurchaseOrderItem.objects.create(
                purchase_order=order,
                product=product,
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                total_price=item['total_price']
            )
        
        messages.success(request, 'Purchase order created successfully!')
        return redirect('purchase_orders')
    
    suppliers = Supplier.objects.filter(is_active=True)
    products = Product.objects.filter(is_active=True)
    return render(request, 'add_purchase_order.html', {
        'suppliers': suppliers,
        'products': products
    })

@login_required
def edit_purchase_order(request, order_id):
    order = get_object_or_404(PurchaseOrder, id=order_id)
    if request.method == 'POST':
        order.status = request.POST.get('status')
        order.expected_delivery_date = request.POST.get('expected_delivery_date')
        order.notes = request.POST.get('notes')
        order.save()
        
        # Update received quantities
        items = json.loads(request.POST.get('items', '[]'))
        for item in items:
            order_item = get_object_or_404(PurchaseOrderItem, id=item['id'])
            order_item.received_quantity = item['received_quantity']
            order_item.notes = item.get('notes', '')
            order_item.save()
        
        messages.success(request, 'Purchase order updated successfully!')
        return redirect('purchase_orders')
    
    return render(request, 'edit_purchase_order.html', {'order': order})

@csrf_exempt
def mpesa_callback(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            logger.info(f"M-Pesa callback received: {data}")
            
            # Extract transaction details
            merchant_request_id = data.get('MerchantRequestID')
            checkout_request_id = data.get('CheckoutRequestID')
            result_code = data.get('ResultCode')
            result_desc = data.get('ResultDesc')
            
            # Find the transaction
            transaction = MpesaTransaction.objects.get(transaction_id=checkout_request_id)
            
            if result_code == 0:
                # Payment successful
                transaction.status = 'completed'
                transaction.save()
                
                # Update related sale records
                sales = Sale.objects.filter(
                    payment_type='mpesa',
                    date__gte=transaction.date - timedelta(minutes=5)
                )
                for sale in sales:
                    sale.status = 'completed'
                    sale.save()
                
                logger.info(f"Payment completed for transaction {checkout_request_id}")
            else:
                # Payment failed
                transaction.status = 'failed'
                transaction.save()
                logger.error(f"Payment failed for transaction {checkout_request_id}: {result_desc}")
            
            return JsonResponse({'status': 'success'})
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON in M-Pesa callback")
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except MpesaTransaction.DoesNotExist:
            logger.error(f"Transaction not found: {checkout_request_id}")
            return JsonResponse({'status': 'error', 'message': 'Transaction not found'}, status=404)
        except Exception as e:
            logger.error(f"Error processing M-Pesa callback: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@login_required
@csrf_exempt
def delete_order(request, order_id):
    try:
        order = get_object_or_404(Order, id=order_id)
        if request.method == 'POST':
            order.delete()
            messages.success(request, 'Order deleted successfully.')
        return redirect('orders')
    except Exception as e:
        messages.error(request, f'Error deleting order: {str(e)}')
        return redirect('orders')

@login_required
@csrf_exempt
def delete_employee(request, employee_id):
    try:
        employee = get_object_or_404(Employee, id=employee_id)
        if request.method == 'POST':
            employee.delete()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Employee deleted successfully.'
                })
            else:
                messages.success(request, 'Employee deleted successfully.')
                return redirect('employees')
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f'Error deleting employee: {str(e)}'
            }, status=400)
        else:
            messages.error(request, f'Error deleting employee: {str(e)}')
            return redirect('employees')

@login_required
@csrf_exempt
def delete_sale(request, sale_id):
    try:
        sale = get_object_or_404(Sale, id=sale_id)
        if request.method == 'POST':
            # Restore the product's stock
            if sale.variant:
                sale.variant.stock += sale.qty
                sale.variant.save()
            else:
                sale.product.current_stock += sale.qty
                sale.product.save()
            
            # Create stock history record for the deletion
            StockHistory.objects.create(
                product=sale.product,
                quantity_change=sale.qty,  # Positive change since we're restoring stock
                notes=f"Sale #{sale.id} deleted - Stock restored",
                created_by=request.user
            )
            
            # Delete the sale
            sale.delete()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Sale deleted successfully.'
                })
            else:
                messages.success(request, 'Sale deleted successfully.')
                return redirect('sales')
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f'Error deleting sale: {str(e)}'
            }, status=400)
        else:
            messages.error(request, f'Error deleting sale: {str(e)}')
            return redirect('sales')

@login_required
@csrf_exempt
def delete_customer(request, customer_id):
    try:
        customer = get_object_or_404(Customer, id=customer_id)
        if request.method == 'POST':
            customer.delete()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Customer deleted successfully.'
                })
            else:
                messages.success(request, 'Customer deleted successfully.')
                return redirect('customers')
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f'Error deleting customer: {str(e)}'
            }, status=400)
        else:
            messages.error(request, f'Error deleting customer: {str(e)}')
            return redirect('customers')

@login_required
@csrf_exempt
def delete_ingredient(request, ingredient_id):
    try:
        ingredient = get_object_or_404(Ingredient, id=ingredient_id)
        if request.method == 'POST':
            ingredient.delete()
            messages.success(request, f'Ingredient {ingredient.name} deleted successfully!')
        return redirect('inventory')
    except Exception as e:
        messages.error(request, f'Error deleting ingredient: {str(e)}')
        return redirect('inventory')

@login_required
def update_ingredient_image(request, ingredient_id):
    ingredient = get_object_or_404(Ingredient, id=ingredient_id)
    if request.method == 'POST':
        if 'image' in request.FILES:
            ingredient.image = request.FILES['image']
            ingredient.save()
            messages.success(request, 'Image updated successfully.')
    return redirect('inventory')

@login_required
def bulk_update_stock(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Please upload a CSV file.')
            return redirect('inventory')
        
        try:
            decoded_file = csv_file.read().decode('utf-8')
            csv_reader = csv.DictReader(decoded_file.splitlines())
            
            for row in csv_reader:
                try:
                    ingredient = Ingredient.objects.get(name=row['name'])
                    quantity_change = float(row['quantity_change'])
                    notes = row.get('notes', '')
                    
                    # Update stock
                    ingredient.quantity += quantity_change
                    ingredient.save()
                    
                    # Record the update
                    StockUpdate.objects.create(
                        ingredient=ingredient,
                        quantity_change=quantity_change,
                        notes=notes
                    )
                except Ingredient.DoesNotExist:
                    messages.warning(request, f"Ingredient '{row['name']}' not found.")
                except ValueError:
                    messages.warning(request, f"Invalid quantity for '{row['name']}'.")
            
            messages.success(request, 'Bulk update completed successfully.')
        except Exception as e:
            messages.error(request, f'Error processing CSV file: {str(e)}')
    
    return redirect('inventory')

@login_required
def update_ingredient(request, ingredient_id):
    ingredient = get_object_or_404(Ingredient, id=ingredient_id)
    
    if request.method == 'POST':
        form = IngredientForm(request.POST, request.FILES, instance=ingredient)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ingredient updated successfully!')
            return redirect('inventory')
    else:
        form = IngredientForm(instance=ingredient)
    
    return render(request, 'update_ingredient.html', {
        'form': form,
        'ingredient': ingredient
    })

@login_required
def add_product(request):
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name')
            description = request.POST.get('description')
            price = request.POST.get('price')
            cost_price = request.POST.get('cost_price')
            category_id = request.POST.get('category')
            sku = request.POST.get('sku')
            current_stock = int(request.POST.get('current_stock', 0))
            reorder_point = int(request.POST.get('reorder_point', 10))
            image = request.FILES.get('image')

            # Validate stock and reorder point
            if current_stock < 0:
                messages.error(request, 'Current stock cannot be negative')
                return redirect('add_product')
            
            if reorder_point < 0:
                messages.error(request, 'Reorder point cannot be negative')
                return redirect('add_product')

            # Create the product
            product = Product.objects.create(
                name=name,
                description=description,
                price=price,
                cost_price=cost_price,
                category_id=category_id,
                sku=sku,
                current_stock=current_stock,
                reorder_point=reorder_point,
                image=image
            )

            # Create initial stock history record
            if current_stock > 0:
                StockHistory.objects.create(
                    product=product,
                    quantity_change=current_stock,
                    notes='Initial stock',
                    created_by=request.user
                )

            messages.success(request, f'Product {name} added successfully!')
            return redirect('inventory')
        except Exception as e:
            messages.error(request, f'Error adding product: {str(e)}')
            return redirect('add_product')
    
    categories = Category.objects.all()
    return render(request, 'add_product.html', {'categories': categories})

@login_required
@csrf_exempt
def process_payment(request):
    if request.method == 'POST':
        try:
            # Log the raw request body
            logger.info(f"Raw request body: {request.body}")
            
            data = json.loads(request.body)
            logger.info(f"Parsed request data: {data}")
            
            items = data.get('items', [])
            payment_type = data.get('payment_type')
            mpesa_phone = data.get('mpesa_phone', '')
            total_amount = data.get('total_amount', 0)
            
            logger.info(f"Items: {items}")
            logger.info(f"Payment type: {payment_type}")
            logger.info(f"M-Pesa phone: {mpesa_phone}")
            logger.info(f"Total amount: {total_amount}")
            
            if not items:
                return JsonResponse({'error': 'Cart is empty'}, status=400)
                
            if not payment_type:
                return JsonResponse({'error': 'Payment method is required'}, status=400)
                
            if payment_type == 'mpesa' and not mpesa_phone:
                return JsonResponse({'error': 'M-Pesa phone number is required'}, status=400)
            
            # Validate stock for all items
            stock_errors = []
            for item in items:
                try:
                    if not isinstance(item, dict):
                        logger.error(f"Invalid item format: {item}")
                        return JsonResponse({'error': 'Invalid item format'}, status=400)
                        
                    if 'id' not in item or 'quantity' not in item or 'price' not in item:
                        logger.error(f"Missing required fields in item: {item}")
                        return JsonResponse({'error': 'Missing required fields in item data'}, status=400)
                        
                    product = Product.objects.get(id=item['id'])
                    quantity = int(item['quantity'])
                    price = float(item['price'])
                    
                    logger.info(f"Checking stock for product {product.name}: current={product.current_stock}, requested={quantity}")
                    
                    if product.current_stock < quantity:
                        stock_errors.append(f"{product.name}: Available: {product.current_stock}, Requested: {quantity}")
                except Product.DoesNotExist:
                    logger.error(f"Product not found: {item.get('id')}")
                    return JsonResponse({'error': f'Product with ID {item.get("id")} not found'}, status=400)
                except (ValueError, TypeError) as e:
                    logger.error(f"Invalid quantity or price: {e}")
                    return JsonResponse({'error': f'Invalid quantity or price: {str(e)}'}, status=400)
                except Exception as e:
                    logger.error(f"Error processing item: {str(e)}")
                    return JsonResponse({'error': f'Error processing item: {str(e)}'}, status=400)
            
            if stock_errors:
                error_message = "Insufficient stock for the following items:\n" + "\n".join(stock_errors)
                logger.error(f"Stock validation failed: {error_message}")
                return JsonResponse({'error': error_message}, status=400)
            
            # Create sale records and update stock
            with transaction.atomic():
                # Create a transaction timestamp
                transaction_time = timezone.now()
                first_sale = None
                
                for item in items:
                    product = Product.objects.select_for_update().get(id=item['id'])
                    quantity = int(item['quantity'])
                    price = float(item['price'])
                    
                    # Double-check stock before creating sale
                    if product.current_stock < quantity:
                        raise ValueError(f"Insufficient stock for {product.name}")
                    
                    # Create the sale record with the transaction timestamp
                    sale = Sale.objects.create(
                        product=product,
                        qty=quantity,
                        price=price,
                        payment_type=payment_type,
                        user=request.user,
                        date=transaction_time  # Use the same timestamp for all items
                    )
                    
                    # Keep track of the first sale for the receipt
                    if first_sale is None:
                        first_sale = sale
                    
                    # Update stock after sale is created
                    product.current_stock = max(0, product.current_stock - quantity)
                    product.save()
                    
                    logger.info(f"Updated stock for {product.name}: new stock={product.current_stock}")
                
                # If it's an M-Pesa payment, create a transaction record
                if payment_type == 'mpesa':
                    MpesaTransaction.objects.create(
                        phone=mpesa_phone,
                        amount=total_amount,
                        status='pending'
                    )
                
                if first_sale is None:
                    raise ValueError("No sales were created")
                
                return JsonResponse({'receipt_id': first_sale.id})
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            return JsonResponse({'error': 'Invalid request data format'}, status=400)
        except ValueError as e:
            logger.error(f"Value error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            logger.error(f"Error processing payment: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def receipt(request, sale_id):
    try:
        # Get the first sale to get the date and cashier info
        first_sale = Sale.objects.select_related('product', 'user').get(id=sale_id)
        
        # Get all sales from the same transaction (same date and user)
        # Use a time window of 5 seconds to ensure we get all items
        time_window = first_sale.date + timedelta(seconds=5)
        sales = Sale.objects.select_related('product').filter(
            date__gte=first_sale.date,
            date__lt=time_window,
            user=first_sale.user
        ).order_by('id')
        
        # Calculate total amount
        total_amount = sum(sale.price * sale.qty for sale in sales)
        
        return render(request, 'receipt.html', {
            'title': f'Receipt #{sale_id}',
            'sale': first_sale,  # For date, cashier, and payment info
            'sales': sales,      # For all items
            'total_amount': total_amount
        })
    except Sale.DoesNotExist:
        messages.error(request, 'Sale not found')
        return redirect('pos')

@login_required
def customer_list(request):
    customers = Customer.objects.all().order_by('-created_at')
    return render(request, 'customers.html', {
        'customers': customers,
        'title': 'Customers'
    })

@login_required
def customer_details(request, customer_id):
    try:
        customer = get_object_or_404(Customer, id=customer_id)
        orders = Order.objects.filter(customer=customer).order_by('-created_at')
        
        total_orders = orders.count()
        total_spent = sum(order.total_amount for order in orders)
        
        data = {
            'name': customer.name,
            'email': customer.email,
            'phone': customer.phone,
            'address': customer.address,
            'total_orders': total_orders,
            'total_spent': float(total_spent),
            'orders': [{
                'id': order.id,
                'date': order.created_at.strftime('%Y-%m-%d %H:%M'),
                'total_amount': float(order.total_amount),
                'status': order.get_status_display(),
                'delivery_type': order.get_delivery_type_display(),
                'items': [{
                    'product_name': item.product.name,
                    'quantity': item.quantity,
                    'price': float(item.price)
                } for item in order.orderitem_set.all()]
            } for order in orders]
        }
        return JsonResponse(data)
    except Customer.DoesNotExist:
        return JsonResponse({'error': 'Customer not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def order_details(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        return render(request, 'order_details.html', {
            'order': order,
            'title': f'Order #{order.id} Details'
        })
    except Order.DoesNotExist:
        messages.error(request, 'Order not found')
        return redirect('orders')

@login_required
def delete_product(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
        product_name = product.name
        product.delete()
        messages.success(request, f'Product "{product_name}" has been removed from inventory.')
    except Product.DoesNotExist:
        messages.error(request, 'Product not found.')
    except Exception as e:
        messages.error(request, f'Error deleting product: {str(e)}')
    
    return redirect('inventory')

@login_required
def edit_product(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
        categories = Category.objects.all()
        
        if request.method == 'POST':
            # Update product details
            product.name = request.POST.get('name')
            product.category_id = request.POST.get('category')
            product.price = request.POST.get('price')
            product.reorder_point = request.POST.get('reorder_point')
            product.current_stock = request.POST.get('current_stock')
            
            # Handle image upload
            if 'image' in request.FILES:
                product.image = request.FILES['image']
            
            product.save()
            messages.success(request, f'Product "{product.name}" has been updated.')
            return redirect('inventory')
            
        return render(request, 'edit_product.html', {
            'title': f'Edit {product.name}',
            'product': product,
            'categories': categories
        })
    except Product.DoesNotExist:
        messages.error(request, 'Product not found.')
        return redirect('inventory')
    except Exception as e:
        messages.error(request, f'Error updating product: {str(e)}')
        return redirect('inventory')

@login_required
def add_customer(request):
    if request.method == 'POST':
        try:
            # Clean phone number
            phone = request.POST.get('phone')
            phone = re.sub(r'\D', '', phone)
            if phone.startswith('255'):
                phone = '0' + phone[3:]
            if not phone.startswith('0'):
                phone = '0' + phone

            # Create new customer
            Customer.objects.create(
                name=request.POST.get('name'),
                phone=phone,
                email=request.POST.get('email', ''),
                address=request.POST.get('address', '')
            )
            messages.success(request, 'Customer added successfully!')
            return redirect('customers')
        except Exception as e:
            messages.error(request, f'Error adding customer: {str(e)}')
    return render(request, 'add_customer.html')

@login_required
def edit_customer(request, customer_id):
    try:
        customer = get_object_or_404(Customer, id=customer_id)
        if request.method == 'POST':
            # Update customer information
            customer.name = request.POST.get('name')
            customer.phone = request.POST.get('phone')
            customer.email = request.POST.get('email', '')
            customer.address = request.POST.get('address', '')
            customer.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Customer updated successfully'
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating customer: {str(e)}'
        }, status=400)

@login_required
def settings_view(request):
    if request.method == 'POST':
        try:
            # Get all settings from the form
            for setting in Settings.objects.all():
                new_value = request.POST.get(f'setting_{setting.id}')
                if new_value is not None and new_value != setting.value:
                    # Handle boolean settings
                    if setting.name in ['low_stock_alert', 'email_notifications', 'enable_mpesa', 'enable_cash', 'enable_card']:
                        new_value = 'true' if new_value == 'on' else 'false'
                    setting.value = new_value
                    setting.save()
            
            messages.success(request, 'Settings updated successfully!')
            return redirect('settings')
        except Exception as e:
            messages.error(request, f'Error updating settings: {str(e)}')
    
    # Group settings by type
    settings_by_type = {}
    for setting_type, _ in Settings.SETTING_TYPES:
        settings_by_type[setting_type] = Settings.objects.filter(setting_type=setting_type)
    
    return render(request, 'settings.html', {
        'settings_by_type': settings_by_type,
        'title': 'System Settings'
    })
