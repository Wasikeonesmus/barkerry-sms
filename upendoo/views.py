from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from models import Expense

@login_required
def add_expense(request):
    if request.method == 'POST':
        description = request.POST.get('description')
        amount = request.POST.get('amount')
        date = request.POST.get('date')
        
        try:
            Expense.objects.create(
                description=description,
                amount=amount,
                date=date
            )
            messages.success(request, 'Expense added successfully!')
        except Exception as e:
            messages.error(request, f'Error adding expense: {str(e)}')
        
        return redirect('expenses')
    return redirect('expenses')

@login_required
def edit_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)
    
    if request.method == 'POST':
        try:
            expense.description = request.POST.get('description')
            expense.amount = request.POST.get('amount')
            expense.date = request.POST.get('date')
            expense.save()
            messages.success(request, 'Expense updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating expense: {str(e)}')
        
        return redirect('expenses')
    
    return render(request, 'edit_expense.html', {'expense': expense})

@login_required
def delete_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)
    
    try:
        expense.delete()
        messages.success(request, 'Expense deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting expense: {str(e)}')
    
    return redirect('expenses') 