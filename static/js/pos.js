// Initialize variables
let cart = [];
const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', function() {
    // Load cart from localStorage
    const savedCart = localStorage.getItem('cart');
    if (savedCart) {
        try {
            cart = JSON.parse(savedCart);
            updateCart();
        } catch (error) {
            console.error('Error parsing cart from localStorage:', error);
            cart = [];
            localStorage.removeItem('cart');
        }
    }

    // Initialize event listeners
    initializeEventListeners();
});

function initializeEventListeners() {
    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Toggle shortcuts help
        if (e.key === '?') {
            const shortcuts = document.getElementById('keyboardShortcuts');
            shortcuts.innerHTML = 'Keyboard Shortcuts:<br>? Show/Hide shortcuts<br>Esc Close modal<br>Ctrl + F Focus search<br>Ctrl + Enter Process payment';
            setTimeout(() => {
                shortcuts.innerHTML = 'Press ? for shortcuts';
            }, 5000);
        }
        
        // Focus search
        if (e.ctrlKey && e.key === 'f') {
            e.preventDefault();
            document.getElementById('searchInput').focus();
        }
        
        // Process payment
        if (e.ctrlKey && e.key === 'Enter') {
            const processPaymentBtn = document.getElementById('processPayment');
            if (!processPaymentBtn.disabled) {
                processPaymentBtn.click();
            }
        }
    });

    // Search functionality
    document.getElementById('searchInput').addEventListener('input', function(e) {
        const searchTerm = e.target.value.toLowerCase();
        const products = document.querySelectorAll('.product-card');
        products.forEach(product => {
            const productName = product.querySelector('.product-title').textContent.toLowerCase();
            const shouldShow = productName.includes(searchTerm);
            product.style.display = shouldShow ? 'block' : 'none';
        });
    });

    document.getElementById('clearSearch').addEventListener('click', function() {
        document.getElementById('searchInput').value = '';
        document.querySelectorAll('.product-card').forEach(product => {
            product.style.display = 'block';
        });
    });

    // Category filtering
    document.querySelectorAll('.category-pill').forEach(pill => {
        pill.addEventListener('click', function() {
            const category = this.dataset.category;
            
            // Update active state
            document.querySelectorAll('.category-pill').forEach(p => p.classList.remove('active'));
            this.classList.add('active');
            
            // Filter products
            document.querySelectorAll('.product-card').forEach(product => {
                if (category === 'all' || product.dataset.category === category) {
                    product.style.display = 'block';
                } else {
                    product.style.display = 'none';
                }
            });
        });
    });

    // View Cart button
    document.getElementById('viewCartBtn').addEventListener('click', function() {
        const cartModal = new bootstrap.Modal(document.getElementById('cartModal'));
        cartModal.show();
    });

    // Proceed to payment button in cart modal
    document.getElementById('proceedToPayment').addEventListener('click', function() {
        const cartModal = bootstrap.Modal.getInstance(document.getElementById('cartModal'));
        cartModal.hide();
        proceedToPayment();
    });

    // Payment method selection
    document.querySelectorAll('input[name="payment_type"]').forEach(radio => {
        radio.addEventListener('change', function() {
            const mpesaPhoneGroup = document.getElementById('mpesaPhoneGroup');
            if (this.value === 'mpesa') {
                mpesaPhoneGroup.style.display = 'block';
            } else {
                mpesaPhoneGroup.style.display = 'none';
            }
        });
    });

    // Process payment button
    document.getElementById('processPayment').addEventListener('click', function() {
        const selectedPayment = document.querySelector('input[name="payment_type"]:checked');
        if (!selectedPayment) {
            alert('Please select a payment method');
            return;
        }
        
        if (selectedPayment.value === 'mpesa') {
            const phone = document.getElementById('phone').value;
            if (!phone || !/^[0-9]{9}$/.test(phone)) {
                alert('Please enter a valid M-Pesa phone number');
                return;
            }
        }
        
        processPayment(selectedPayment.value);
    });
}

function addToCart(id, name, price, maxStock) {
    const quantityInput = document.getElementById(`qty-${id}`);
    const quantity = parseInt(quantityInput.value);
    
    if (quantity < 1) {
        alert('Please enter a valid quantity');
        return;
    }
    
    if (quantity > maxStock) {
        alert(`Only ${maxStock} items available in stock`);
        return;
    }
    
    // Check if item already exists in cart
    const existingItemIndex = cart.findIndex(item => item.id === id);
    if (existingItemIndex !== -1) {
        // Update quantity if item exists
        const newQuantity = cart[existingItemIndex].quantity + quantity;
        if (newQuantity > maxStock) {
            alert(`Cannot add more than ${maxStock} items`);
            return;
        }
        cart[existingItemIndex].quantity = newQuantity;
    } else {
        // Add new item to cart
        cart.push({
            id: id,
            name: name,
            price: price,
            quantity: quantity
        });
    }
    
    // Reset quantity input
    quantityInput.value = 1;
    
    // Update cart display
    updateCart();
    
    // Show cart summary
    const cartSummary = document.getElementById('cartSummary');
    cartSummary.classList.add('show');
}

function proceedToPayment() {
    if (cart.length === 0) {
        alert('Your cart is empty');
        return;
    }
    const paymentModal = new bootstrap.Modal(document.getElementById('paymentModal'));
    paymentModal.show();
}

function updateCart() {
    const cartItems = document.getElementById('cartItems');
    const cartTotal = document.getElementById('cartTotal');
    const cartSummaryTotal = document.getElementById('cartSummaryTotal');
    const checkoutBtn = document.getElementById('checkoutBtn');
    const cartSummary = document.getElementById('cartSummary');
    const cartItemCount = document.getElementById('cartItemCount');
    
    cartItems.innerHTML = '';
    let total = 0;
    let itemCount = 0;
    
    cart.forEach((item, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${item.name}</td>
            <td>
                <div class="input-group input-group-sm" style="width: 120px;">
                    <button class="btn btn-outline-secondary" type="button" onclick="updateItemQuantity(${index}, -1)">-</button>
                    <input type="number" class="form-control text-center" value="${item.quantity}" min="1" onchange="updateItemQuantity(${index}, 0, this.value)">
                    <button class="btn btn-outline-secondary" type="button" onclick="updateItemQuantity(${index}, 1)">+</button>
                </div>
            </td>
            <td>KES ${parseFloat(item.price).toFixed(2)}</td>
            <td>KES ${(parseFloat(item.price) * item.quantity).toFixed(2)}</td>
            <td>
                <button class="btn btn-sm btn-danger" onclick="removeFromCart(${index})">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        cartItems.appendChild(row);
        total += parseFloat(item.price) * item.quantity;
        itemCount += item.quantity;
    });
    
    cartTotal.textContent = `KES ${total.toFixed(2)}`;
    cartSummaryTotal.textContent = `KES ${total.toFixed(2)}`;
    document.getElementById('paymentTotal').textContent = `KES ${total.toFixed(2)}`;
    cartItemCount.textContent = `${itemCount} item${itemCount !== 1 ? 's' : ''}`;
    
    // Show/hide cart summary and enable/disable checkout button
    if (cart.length > 0) {
        cartSummary.classList.add('show');
        checkoutBtn.disabled = false;
        document.getElementById('proceedToPayment').disabled = false;
    } else {
        cartSummary.classList.remove('show');
        checkoutBtn.disabled = true;
        document.getElementById('proceedToPayment').disabled = true;
    }
    
    // Update receipt preview
    const receiptItems = document.getElementById('receiptItems');
    const receiptTotal = document.getElementById('receiptTotal');
    receiptItems.innerHTML = cart.map(item => `
        <div class="d-flex justify-content-between">
            <span>${item.name} x${item.quantity}</span>
            <span>KES ${(parseFloat(item.price) * item.quantity).toFixed(2)}</span>
        </div>
    `).join('');
    receiptTotal.textContent = `KES ${total.toFixed(2)}`;
    
    // Save cart to localStorage
    localStorage.setItem('cart', JSON.stringify(cart));
}

function updateItemQuantity(index, change, newValue) {
    const item = cart[index];
    if (newValue !== undefined) {
        item.quantity = parseInt(newValue);
    } else {
        item.quantity += change;
    }
    
    if (item.quantity < 1) {
        removeFromCart(index);
    } else {
        updateCart();
    }
}

function removeFromCart(index) {
    cart.splice(index, 1);
    updateCart();
}

function processPayment(paymentType) {
    const paymentData = {
        items: cart.map(item => ({
            id: item.id,
            name: item.name,
            price: item.price,
            quantity: item.quantity
        })),
        payment_type: paymentType,
        total_amount: cart.reduce((sum, item) => sum + (parseFloat(item.price) * item.quantity), 0)
    };
    
    if (paymentType === 'mpesa') {
        paymentData.phone = document.getElementById('phone').value;
    }
    
    // Show loading state
    const processPaymentBtn = document.getElementById('processPayment');
    processPaymentBtn.disabled = true;
    processPaymentBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
    
    // Send payment data to server
    fetch('/pos/process-payment/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify(paymentData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Clear cart and show success message
            cart = [];
            localStorage.removeItem('cart');
            updateCart();
            
            // Close payment modal
            const paymentModal = bootstrap.Modal.getInstance(document.getElementById('paymentModal'));
            paymentModal.hide();
            
            // Print receipt
            printReceipt(data.receipt_data);
            
            // Show success message
            alert('Payment processed successfully!');
        } else {
            throw new Error(data.message || 'Payment failed');
        }
    })
    .catch(error => {
        console.error('Payment error:', error);
        alert(error.message || 'An error occurred while processing the payment');
    })
    .finally(() => {
        // Reset button state
        processPaymentBtn.disabled = false;
        processPaymentBtn.innerHTML = '<i class="fas fa-check me-2"></i> Process Payment';
    });
}

function printReceipt(receiptData) {
    // Create receipt content
    const receiptContent = `
        <div style="font-family: 'Courier New', monospace; width: 300px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; margin-bottom: 20px;">
                <h2 style="margin: 0;">Upendo Mini Bakery</h2>
                <p style="margin: 5px 0;">Receipt</p>
                <p style="margin: 5px 0;">${receiptData.date}</p>
                <p style="margin: 5px 0;">Sale #${receiptData.sale_id}</p>
            </div>
            <div style="border-top: 1px dashed #000; border-bottom: 1px dashed #000; padding: 10px 0;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span>Item</span>
                    <span>Qty</span>
                    <span>Price</span>
                    <span>Total</span>
                </div>
                ${receiptData.items.map(item => `
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span>${item.name}</span>
                        <span>${item.quantity}</span>
                        <span>KES ${parseFloat(item.price).toFixed(2)}</span>
                        <span>KES ${(parseFloat(item.price) * item.quantity).toFixed(2)}</span>
                    </div>
                `).join('')}
            </div>
            <div style="margin-top: 20px;">
                <div style="display: flex; justify-content: space-between; font-weight: bold;">
                    <span>Total Amount:</span>
                    <span>KES ${receiptData.total_amount.toFixed(2)}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-top: 5px;">
                    <span>Payment Method:</span>
                    <span>${receiptData.payment_type.toUpperCase()}</span>
                </div>
                ${receiptData.phone ? `
                    <div style="display: flex; justify-content: space-between; margin-top: 5px;">
                        <span>M-Pesa Phone:</span>
                        <span>+254${receiptData.phone}</span>
                    </div>
                ` : ''}
            </div>
            <div style="text-align: center; margin-top: 20px; border-top: 1px dashed #000; padding-top: 10px;">
                <p style="margin: 5px 0;">Thank you for your purchase!</p>
                <p style="margin: 5px 0;">Please come again</p>
            </div>
        </div>
    `;

    // Create a new window for printing
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <html>
            <head>
                <title>Receipt</title>
                <style>
                    @media print {
                        body { margin: 0; }
                        @page { margin: 0; }
                    }
                </style>
            </head>
            <body>
                ${receiptContent}
                <script>
                    window.onload = function() {
                        window.print();
                        window.onafterprint = function() {
                            window.close();
                        };
                    };
                </script>
            </body>
        </html>
    `);
    printWindow.document.close();
}

// Update payment summary
function updatePaymentSummary(subtotal) {
    const paymentSubtotal = document.getElementById('paymentSubtotal');
    const paymentVAT = document.getElementById('paymentVAT');
    const paymentTotal = document.getElementById('paymentTotal');
    
    if (paymentSubtotal && paymentVAT && paymentTotal) {
        const vat = parseFloat(subtotal) * 0.16;
        const finalTotal = parseFloat(subtotal) + vat;
        
        paymentSubtotal.textContent = `KES ${parseFloat(subtotal).toFixed(2)}`;
        paymentVAT.textContent = `KES ${vat.toFixed(2)}`;
        paymentTotal.textContent = `KES ${finalTotal.toFixed(2)}`;
    }
} 