from django.shortcuts import render, redirect
from .models import UpcycledProduct, TrashItem
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from users.models import CustomUser  # adjust if needed
from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .forms import UpcycledProductForm, TrashItemForm
from django.contrib.contenttypes.models import ContentType
from .models import CartItem, Order, OrderItem
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.contrib.contenttypes.models import ContentType
from decimal import Decimal
import datetime
from marketplace.models import Review
from django.db.models import Avg
from users.models import DriverProfile, DriverRating
from django.db.models import Q, Count, Sum
from itertools import chain
import requests
import json
import base64
from django.conf import settings
from users.models import CustomUser


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.role == role:
                login(request, user)
                if role == 'driver':
                    return redirect('driver_dashboard')
                elif role == 'admin':
                    return redirect('admin_dashboard')
                else:
                    return redirect('home')  # or redirect based on role if you want
            else:
                messages.error(request, 'Invalid role selected.')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'login1.html')


def logout_view(request):
    logout(request)
    return redirect('home')  # Redirect to home page after logout

def home(request):
    featured_products = UpcycledProduct.objects.filter(approval_status=True).order_by('-id')[:4]
    featured_trash_items = TrashItem.objects.filter(approval_status=True).order_by('-id')[:4]  # or any filter you like

    context = {
        'featured_products': featured_products,
        'featured_trash_items': featured_trash_items,
    }
    return render(request, 'home.html', context)


@login_required
def driver_dashboard(request):
    if request.user.role != 'driver':
        return HttpResponseForbidden("You are not authorized to view this page.")

    # Fetch all orders assigned to this driver
    orders = Order.objects.filter(assigned_delivery_guy=request.user)

    return render(request, 'driver_dashboard.html', {
        'orders': orders
    })

@login_required
def update_delivery_status(request, order_id):
    if request.user.role != 'driver':
        return HttpResponseForbidden()

    order = get_object_or_404(
        Order,
        id=order_id,
        assigned_delivery_guy=request.user
    )

    if request.method == 'POST':
        new_status = request.POST.get('delivery_status')
        allowed = ['packed','on_the_way','delivered','returned']
        if new_status in allowed:
            order.delivery_status = new_status
            order.save()
    return redirect('driver_dashboard')

@login_required
def update_expected_delivery(request, order_id):
    if request.user.role != 'driver':
        return HttpResponseForbidden()

    order = get_object_or_404(
        Order, 
        id=order_id, 
        assigned_delivery_guy=request.user
    )

    if request.method == 'POST':
        date_str = request.POST.get('expected_delivery')
        if date_str:
            # parse YYYY-MM-DD from the date input
            order.expected_delivery = datetime.strptime(date_str, '%Y-%m-%d')
            order.save()
    return redirect('driver_dashboard')


def delivery_history(request):
    driver = request.user  # assuming only logged-in drivers can access
    orders = Order.objects.filter(assigned_delivery_guy=request.user)

    active_deliveries = orders.exclude(delivery_status__in=['delivered', 'returned'])
    completed_deliveries = orders.filter(delivery_status__in=['delivered', 'returned'])

    context = {
        'active_deliveries': active_deliveries,
        'completed_deliveries': completed_deliveries,
    }
    return render(request, 'delivery_history.html', context)

def contact(request):
    from .forms import ContactForm
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Process the form (e.g., send email)
            # For now, just show success message
            messages.success(request, 'Thank you for your message! We will get back to you soon.')
            return redirect('contact')
    else:
        form = ContactForm()
    return render(request, 'contact.html', {'form': form})

def privacy(request):
    return render(request, 'privacy.html')

def help(request):
    return render(request, 'help.html')

def terms(request):
    return render(request, 'terms.html')

@login_required
def cart(request):
    if request.user.role == 'driver':
        return HttpResponseForbidden("You are not authorized to view this page.")

    cart_items = CartItem.objects.filter(buyer=request.user)
    # Filter out items with deleted products
    valid_cart_items = [item for item in cart_items if item.item is not None]
    # Remove invalid cart items from database
    invalid_items = [item for item in cart_items if item.item is None]
    for invalid_item in invalid_items:
        invalid_item.delete()

    total = sum(item.subtotal() for item in valid_cart_items)
    return render(request, 'cart.html', {
        'cart_items': valid_cart_items,
        'total': total
    })
    
    
def about(request):
    return render(request, 'about.html')

from django.core.paginator import Paginator

@login_required
def listed_products(request):
    if request.user.role != 'artisan':
        return HttpResponseForbidden("You are not authorized to view this page.")

    products = UpcycledProduct.objects.filter(artisan=request.user)

    # Pagination logic
    paginator = Paginator(products, 12) # 12 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'listed_products.html', {
        'products': products,  # Keep this if you want to use it elsewhere
        'page_obj': page_obj   # This is the one your grid uses
    })

@login_required
def order_history(request):
    if request.user.role != 'artisan':
        return HttpResponseForbidden("You are not authorized to view this page.")
    
    # Assuming you have an Order model to fetch order history
    # orders = Order.objects.filter(buyer=request.user)
    # return render(request, 'order_history.html', {'orders': orders})
    return render(request, 'order_history.html')

@login_required
def product_listing(request):
    if request.user.role != 'artisan':
        return HttpResponseForbidden("Not allowed")

    if request.method == 'POST':
        form = UpcycledProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.artisan        = request.user
            product.approval_status = False
            product.save()
            messages.success(request, "Product listed successfully! Pending admin approval.")
            return redirect('listed_products')
    else:
        form = UpcycledProductForm()

    return render(request, 'product_listing.html', {'form': form})

@login_required
def checkout(request):
    # 1) grab all cart items for the current user
    cart_items = CartItem.objects.filter(buyer=request.user)

    # 2) compute the overall subtotal
    subtotal = sum(item.subtotal() for item in cart_items)

    # 3) render with both in the context
    return render(request, 'checkout.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
    })

#profile_views

@login_required
def driver_profile(request):
    if request.user.role != 'driver':
        return HttpResponseForbidden("Access denied.")

    profile = request.user.driverprofile
    return render(request, 'driver_profile.html', {'profile': profile})

@login_required
def artisan_profile(request):
    if request.user.role != 'artisan':
        return HttpResponseForbidden("Access denied.")

    profile = request.user.artisanprofile
    return render(request, 'artisan_profile.html', {'profile': profile})

@login_required
def buyer_profile(request):
    if request.user.role != 'buyer':
        return HttpResponseForbidden("Access denied.")

    profile = request.user.buyerprofile
    return render(request, 'buyer_profile.html', {'profile': profile})


def upcycled_product_details(request, slug):
    # Allow admins to view pending products, regular users can only see approved ones
    if request.user.is_authenticated and request.user.role == 'admin':
        product = get_object_or_404(UpcycledProduct, slug=slug)
    else:
        product = get_object_or_404(UpcycledProduct, slug=slug, approval_status=True)
    return render(request, 'upcycled_product_details.html', {'product': product})


def upcycled_products(request):
    products = UpcycledProduct.objects.filter(approval_status=True).order_by('-id')
    paginator = Paginator(products, 12)  # 12 products per page

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'upcycled_products.html', {'page_obj': page_obj})



@login_required
def edit_product(request, pk):
    product = get_object_or_404(UpcycledProduct, pk=pk, artisan=request.user)
    if request.method == 'POST':
        form = UpcycledProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('listed_products')
    else:
        form = UpcycledProductForm(instance=product)
    return render(request, 'edit_product.html', {'form': form, 'product': product})


@login_required
def delete_product(request, pk):
    product = get_object_or_404(UpcycledProduct, pk=pk, artisan=request.user)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully.')
        return redirect('listed_products')
    return redirect('listed_products')


# views.py


@login_required
def add_to_cart(request, model_name, object_id):
    # 1. Identify what model we’re adding
    ct = get_object_or_404(ContentType, model=model_name)
    product = get_object_or_404(ct.model_class(), pk=object_id)

    # 2. Role‑based guardrails
    if request.user.role == 'artisan' and ct.model_class().__name__ != 'TrashItem':
        messages.error(request, "As an Artisan you can only add trash materials to your cart.")
        # Determine which detail view to redirect to based on product type
        if isinstance(product, TrashItem):
            return redirect('trash_item_details', slug=product.slug)
        else:
            return redirect('upcycled_product_details', slug=product.slug)


    if request.user.role not in ('artisan','buyer'):
        messages.error(request, "Only Buyers or Artisans can add items to cart.")
        # Determine which detail view to redirect to based on product type
        if isinstance(product, TrashItem):
            return redirect('trash_item_details', slug=product.slug)
        else:
            return redirect('upcycled_product_details', slug=product.slug)


    # 3. Handle GET or POST
    if request.method == 'GET':
        qty = 1
        action = request.GET.get('action')
        next_url = request.GET.get('next')
    else:
        qty = int(request.POST.get('quantity', 1))
        action = request.POST.get('action')
        next_url = request.POST.get('next')

    # clamp to product.quantity for trash, or product.stock_availability for upcycled
    max_stock = getattr(product, 'quantity', None) or product.stock_availability
    qty = max(1, min(qty, max_stock))

    # 4. Create or update
    cart_item, created = CartItem.objects.get_or_create(
        buyer=request.user,
        content_type=ct,
        object_id=object_id,
        defaults={'quantity': qty}
    )
    if not created:
        cart_item.quantity = min(cart_item.quantity + qty, max_stock)
        cart_item.save()

    messages.success(request, "Item added to cart!")

    if action == 'buy':
        return redirect('cart')

    return redirect(next_url or 'home')


@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, buyer=request.user)
    item.delete()
    return redirect('cart')


def trash_item_list(request):
    items = TrashItem.objects.filter(product_status="active", approval_status=True)  # Add filters as needed
    paginator = Paginator(items, 12)  # Or however many per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "trash_items.html", {"page_obj": page_obj})


def trash_item_details(request, slug):
    product = get_object_or_404(TrashItem, slug=slug, approval_status=True)
    return render(request, 'trash_item_details.html', {'product': product})


def checkout_view(request):
    cart_items = CartItem.objects.filter(buyer=request.user)
    subtotal = sum([item.subtotal() for item in cart_items])
    return render(request, 'checkout.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
    })



@csrf_exempt
def place_order(request):
    if request.method == "POST":
        cart_items = CartItem.objects.filter(buyer=request.user)
        if not cart_items.exists():
            return redirect_with_message("Your cart is empty.")

        # Calculate subtotal
        subtotal = sum(item.subtotal() for item in cart_items)

        # Create order
        order = Order.objects.create(
            buyer=request.user,
            first_name=request.POST.get("first_name"),
            last_name=request.POST.get("last_name"),
            company=request.POST.get("company"),
            country=request.POST.get("country"),
            street_address=request.POST.get("street_address"),
            city=request.POST.get("city"),
            state=request.POST.get("state"),
            zip_code=request.POST.get("zip"),
            phone=request.POST.get("phone"),
            email=request.POST.get("email"),
            payment_method=request.POST.get("payment_method"),
            total_amount=Decimal(subtotal),
        )

        # Create OrderItems
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                content_type=item.content_type,
                object_id=item.object_id,
                quantity=item.quantity,
                price=item.item.price
            )

        # Clear user's cart
        cart_items.delete()

        return redirect('order_success')

    return redirect('checkout')



@csrf_exempt
def initiate_payment(request):
    if request.method != 'POST':
        return redirect('checkout')

    post_data = request.POST
    user = request.user

    print(f"Initiating payment for user: {user.username}")

    # 1) Gather cart
    cart_items = CartItem.objects.filter(buyer=user)
    if not cart_items.exists():
        print("❌ Cart is empty")
        return redirect_with_message("Your cart is empty.")

    subtotal = sum(item.subtotal() for item in cart_items)
    print(f"Cart subtotal: {subtotal}")

    # 2) Pre-create Order (Pending)
    try:
        order = Order.objects.create(
            buyer=user,
            first_name=post_data.get("first_name"),
            last_name=post_data.get("last_name"),
            company=post_data.get("company"),
            country=post_data.get("country"),
            street_address=post_data.get("street_address"),
            city=post_data.get("city"),
            state=post_data.get("state"),
            zip_code=post_data.get("zip"),
            phone=post_data.get("phone"),
            email=post_data.get("email"),
            payment_method='mpesa',
            total_amount=Decimal(subtotal),
            payment_status='pending',
            delivery_status='ready',
            checkout_request_id='',  # Will update after STK Push
        )
        print(f"✅ Created order {order.id}")
    except Exception as e:
        print(f"❌ Failed to create order: {e}")
        return redirect_with_message("Failed to create order.")

    # 3) Create its OrderItems
    try:
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                content_type=item.content_type,
                object_id=item.object_id,
                quantity=item.quantity,
                price=item.item.price
            )
        print(f"✅ Created {cart_items.count()} order items")
    except Exception as e:
        print(f"❌ Failed to create order items: {e}")
        order.delete()  # Clean up
        return redirect_with_message("Failed to process cart items.")

    # 4) Save pending order ID in session
    request.session['pending_order_id'] = order.id

    # 5) Initiate STK Push for MPESA payment
    phone_number = post_data.get("phone")
    if not phone_number:
        print("❌ Phone number required for MPESA payment")
        order.delete()
        return redirect_with_message("Phone number is required for MPESA payment.")

    # Ensure phone number starts with 254
    if phone_number.startswith('0'):
        phone_number = '254' + phone_number[1:]
    elif not phone_number.startswith('254'):
        phone_number = '254' + phone_number

    # Get MPESA credentials from settings
    consumer_key = getattr(settings, 'MPESA_CONSUMER_KEY', '')
    consumer_secret = getattr(settings, 'MPESA_CONSUMER_SECRET', '')
    shortcode = getattr(settings, 'MPESA_SHORTCODE', '')
    passkey = getattr(settings, 'MPESA_PASSKEY', '')

    if not all([consumer_key, consumer_secret, shortcode, passkey]):
        print("❌ MPESA credentials not configured")
        order.delete()
        return redirect_with_message("Payment system not configured.")

    # Get access token
    access_token = get_mpesa_access_token(consumer_key, consumer_secret)
    if not access_token:
        print("❌ Failed to get MPESA access token")
        order.delete()
        return redirect_with_message("Failed to connect to payment system.")

    # Initiate STK Push
    account_reference = f"TTS_{order.id}"
    stk_response = initiate_stk_push(access_token, shortcode, passkey, phone_number, str(int(subtotal)), account_reference)

    if stk_response and 'CheckoutRequestID' in stk_response:
        order.checkout_request_id = stk_response['CheckoutRequestID']
        order.save()
        print(f"✅ STK Push initiated - CheckoutRequestID: {order.checkout_request_id}")
    else:
        print(f"❌ STK Push failed: {stk_response}")
        order.delete()
        return redirect_with_message("Failed to initiate payment. Please try again.")

    request.session['checkout_request_id'] = order.checkout_request_id
    request.session['total_amount'] = str(subtotal)  # Store amount for template

    print(f"✅ Payment initiated - Order: {order.id}, Amount: {subtotal}, CheckoutRequestID: {order.checkout_request_id}")

    return redirect('payment_waiting')  # Redirect to a waiting page with STK Push instructions


def get_mpesa_access_token(consumer_key, consumer_secret):
    api_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    response = requests.get(api_url, auth=(consumer_key, consumer_secret))
    if response.status_code == 200:
        return response.json()['access_token']
    return None


def initiate_stk_push(access_token, shortcode, passkey, phone_number, amount, account_reference):
    api_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode((shortcode + passkey + timestamp).encode()).decode()

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    payload = {
        'BusinessShortCode': shortcode,
        'Password': password,
        'Timestamp': timestamp,
        'TransactionType': 'CustomerPayBillOnline',
        'Amount': amount,
        'PartyA': phone_number,
        'PartyB': shortcode,
        'PhoneNumber': phone_number,
        'CallBackURL': 'https://yourdomain.com/mpesa/callback/',  # Replace with actual callback URL
        'AccountReference': account_reference,
        'TransactionDesc': 'TakaHub Order Payment'
    }

    response = requests.post(api_url, json=payload, headers=headers)
    return response.json() if response.status_code == 200 else None


@login_required
def payment_waiting(request):
    # Get the checkout request ID and amount from session
    checkout_request_id = request.session.get('checkout_request_id')
    total_amount = request.session.get('total_amount')

    if not checkout_request_id:
        messages.error(request, "No active payment session found.")
        return redirect('cart')

    context = {
        'checkout_request_id': checkout_request_id,
        'total_amount': total_amount,
        'debug': settings.DEBUG  # Only show debug info in development
    }

    return render(request, 'payment_waiting.html', context)


@csrf_exempt
def mpesa_callback(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print(f"MPESA Callback received: {json.dumps(data, indent=2)}")

            # Process C2B callback data (different from STK Push)
            transaction_type = data.get('TransactionType')
            trans_id = data.get('TransID')
            trans_time = data.get('TransTime')
            trans_amount = data.get('TransAmount')
            business_short_code = data.get('BusinessShortCode')
            bill_ref_number = data.get('BillRefNumber')  # This should match our TTS_{order.id}
            invoice_number = data.get('InvoiceNumber')
            org_account_balance = data.get('OrgAccountBalance')
            third_party_trans_id = data.get('ThirdPartyTransID')
            msisdn = data.get('MSISDN')
            first_name = data.get('FirstName')
            middle_name = data.get('MiddleName')
            last_name = data.get('LastName')

            print(f"Processing payment - BillRef: {bill_ref_number}, Amount: {trans_amount}")

            # Extract order ID from BillRefNumber (format: TTS_{order_id})
            if bill_ref_number and bill_ref_number.startswith('TTS_'):
                order_id = bill_ref_number.replace('TTS_', '')
                print(f"Extracted order ID: {order_id}")

                try:
                    order = Order.objects.get(id=order_id)
                    print(f"Found order {order_id}, expected amount: {order.total_amount}")

                    # Verify amount matches (allow small floating point differences)
                    expected_amount = float(order.total_amount)
                    received_amount = float(trans_amount)

                    if abs(expected_amount - received_amount) < 0.01:  # Allow 1 cent difference
                        order.payment_status = 'paid'
                        order.save()
                        # Clear cart for the buyer
                        CartItem.objects.filter(buyer=order.buyer).delete()
                        print(f"✅ Payment confirmed for order {order_id}, amount: {trans_amount}")
                        return HttpResponse('Payment processed successfully')
                    else:
                        print(f"❌ Amount mismatch for order {order_id}: expected {expected_amount}, got {received_amount}")
                        return HttpResponse('Amount mismatch')

                except Order.DoesNotExist:
                    print(f"❌ Order not found: {order_id}")
                    return HttpResponse('Order not found')
                except Exception as e:
                    print(f"❌ Error processing payment: {e}")
                    return HttpResponse('Processing error')
            else:
                print(f"❌ Invalid BillRefNumber format: {bill_ref_number}")
                return HttpResponse('Invalid reference')

        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in callback: {e}")
            return HttpResponse('Invalid JSON')
        except Exception as e:
            print(f"❌ Unexpected error in callback: {e}")
            return HttpResponse('Unexpected error')

    return HttpResponse('Callback received')

def redirect_with_message(message):
    print(f"Redirecting with message: {message}")
    return HttpResponse(f"""
        <html>
            <head>
                <meta charset="UTF-8">
                <title>Redirecting...</title>
                <script>
                    setTimeout(function() {{
                        window.location.href = '/';
                    }}, 3000); // Redirects after 3 seconds
                </script>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        background-color: #f4f4f4;
                    }}
                    .message {{
                        padding: 20px;
                        background: white;
                        border-radius: 10px;
                        box-shadow: 0 0 10px rgba(0,0,0,0.1);
                        font-size: 18px;
                        color: #333;
                        text-align: center;
                    }}
                </style>
            </head>
            <body>
                <div class="message">{message}<br><small>Redirecting to homepage...</small></div>
            </body>
        </html>
    """)

@csrf_exempt
def payment_success(request):
    tran_id = request.POST.get('tran_id') or request.GET.get('tran_id')
    print(f"Payment success called with tran_id: {tran_id}")

    if not tran_id or not tran_id.startswith("TTS_"):
        print("❌ Invalid transaction ID format")
        return redirect_with_message("❌ Invalid transaction ID.")

    order_id = tran_id.replace("TTS_", "")
    print(f"Processing payment success for order: {order_id}")

    try:
        order = Order.objects.get(id=order_id)
        print(f"Found order {order_id}, current status: {order.payment_status}")

        if order.payment_status == 'paid':
            print("⚠️ Order already marked as paid")
            return redirect_with_message("✅ Order already confirmed!")

        # Mark as paid and clear cart
        order.payment_status = 'paid'
        order.save()
        CartItem.objects.filter(buyer=order.buyer).delete()

        print(f"✅ Payment successful for order {order_id}")
        return redirect_with_message("✅ Payment successful and order placed!")

    except Order.DoesNotExist:
        print(f"❌ Order {order_id} not found")
        return redirect_with_message("❌ Order not found.")
    except Exception as e:
        print(f"❌ Error processing payment success: {e}")
        return redirect_with_message("❌ Payment processing failed.")

@csrf_exempt
def payment_fail(request):
    print("Payment failed callback received")
    return redirect_with_message("❌ Payment failed.")

@csrf_exempt
def payment_cancel(request):
    print("Payment cancelled callback received")
    return redirect_with_message("⚠️ Payment canceled.")

@csrf_exempt
def payment_ipn(request):
    return HttpResponse("IPN received.")

@csrf_exempt
def order_success(request):
    return redirect_with_message("Order placed successfully!")

@login_required
def my_orders(request):
    # Get orders for the logged-in user
    orders = Order.objects.filter(buyer=request.user)  # Assuming user is a ForeignKey in Order model
    
    context = {
        'orders': orders
    }

    return render(request, 'my_orders.html', context)

def order_details(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    ordered_items = order.items.all()
    for item in ordered_items:
        item.subtotal = item.quantity * item.price

    # only allow reviews once order is delivered or returned
    pending_review = False
    if order.delivery_status in ['delivered', 'returned']:
        # check each product
        for item in ordered_items:
            ct = ContentType.objects.get_for_model(item.item)
            if not Review.objects.filter(
                    reviewer=request.user,
                    content_type=ct,
                    object_id=item.item.id
                ).exists():
                pending_review = True
                break
        # if all products already reviewed, check driver
        if not pending_review and order.assigned_delivery_guy:
            dp = order.assigned_delivery_guy.driverprofile
            ct = ContentType.objects.get_for_model(dp)
            if not Review.objects.filter(
                reviewer=request.user,
                content_type=ct,
                object_id=dp.id
            ).exists():
                pending_review = True

    return render(request, 'order_details.html', {
        'order': order,
        'ordered_items': ordered_items,
        'pending_review': pending_review,
    })


@login_required
def admin_dashboard(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden("Access denied.")

    # Analytics data
    total_users = CustomUser.objects.count()
    total_upcycled_products = UpcycledProduct.objects.filter(approval_status=True).count()
    total_trash_items = TrashItem.objects.filter(approval_status=True).count()
    total_orders = Order.objects.count()
    pending_upcycled = UpcycledProduct.objects.filter(approval_status=False)

    # User role breakdown
    user_roles = CustomUser.objects.values('role').annotate(count=Count('role')).order_by('role')

    # Recent orders (last 10)
    recent_orders = Order.objects.select_related('buyer').order_by('-id')[:10]

    # Revenue calculation (if orders have payment_status='paid')
    total_revenue = Order.objects.filter(payment_status='paid').aggregate(
        total=Sum('total_amount')
    )['total'] or 0

    context = {
        'pending_upcycled': pending_upcycled,
        'total_users': total_users,
        'total_upcycled_products': total_upcycled_products,
        'total_trash_items': total_trash_items,
        'total_orders': total_orders,
        'user_roles': user_roles,
        'recent_orders': recent_orders,
        'total_revenue': total_revenue,
    }
    return render(request, 'admin_dashboard.html', context)


@login_required
def approve_product(request, model_name, object_id):
    if request.user.role != 'admin':
        return HttpResponseForbidden("Access denied.")

    ct = get_object_or_404(ContentType, model=model_name)
    product = get_object_or_404(ct.model_class(), pk=object_id)

    if hasattr(product, 'approval_status'):
        product.approval_status = True
        product.save()
        messages.success(request, f"{model_name.title()} approved successfully.")
    else:
        messages.error(request, "Invalid product type.")

    return redirect('admin_dashboard')


@login_required
def admin_user_management(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden("Access denied.")

    # Get all users with pagination
    users = CustomUser.objects.all().order_by('-date_joined')
    paginator = Paginator(users, 20)  # 20 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # User statistics
    total_users = users.count()
    active_users = users.filter(account_status='active').count()
    suspended_users = users.filter(account_status='suspended').count()

    # Role breakdown
    role_stats = users.values('role').annotate(count=Count('role')).order_by('role')

    context = {
        'page_obj': page_obj,
        'total_users': total_users,
        'active_users': active_users,
        'suspended_users': suspended_users,
        'role_stats': role_stats,
    }
    return render(request, 'admin_user_management.html', context)


@login_required
def admin_user_detail(request, user_id):
    if request.user.role != 'admin':
        return HttpResponseForbidden("Access denied.")

    user = get_object_or_404(CustomUser, id=user_id)

    context = {
        'user': user,
    }
    return render(request, 'admin_user_detail.html', context)


@login_required
def admin_toggle_user_status(request, user_id):
    if request.user.role != 'admin':
        return HttpResponseForbidden("Access denied.")

    user = get_object_or_404(CustomUser, id=user_id)

    if user == request.user:
        messages.error(request, "You cannot modify your own account status.")
        return redirect('admin_user_management')

    # Toggle status between active and suspended
    if user.account_status == 'active':
        user.account_status = 'suspended'
        messages.success(request, f"User {user.username} has been suspended.")
    elif user.account_status == 'suspended':
        user.account_status = 'active'
        messages.success(request, f"User {user.username} has been reactivated.")
    else:
        messages.error(request, "Cannot modify deleted user accounts.")

    user.save()

    # If it's an AJAX request, return JSON response
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'new_status': user.account_status,
            'message': f"User {user.username} status updated successfully."
        })

    return redirect('admin_user_management')


@login_required
def admin_order_management(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden("Access denied.")

    # Get all orders with related data
    orders = Order.objects.select_related('buyer').prefetch_related('items').order_by('-created_at')
    paginator = Paginator(orders, 20)  # 20 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Order statistics
    total_orders = orders.count()
    pending_orders = orders.filter(payment_status='pending').count()
    paid_orders = orders.filter(payment_status='paid').count()
    completed_orders = orders.filter(delivery_status='delivered').count()

    context = {
        'page_obj': page_obj,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'paid_orders': paid_orders,
        'completed_orders': completed_orders,
    }
    return render(request, 'admin_order_management.html', context)


@login_required
def admin_order_detail(request, order_id):
    if request.user.role != 'admin':
        return HttpResponseForbidden("Access denied.")

    order = get_object_or_404(Order, id=order_id)
    ordered_items = order.items.all()

    # Calculate subtotal for each item
    for item in ordered_items:
        item.subtotal = item.quantity * item.price

    context = {
        'order': order,
        'ordered_items': ordered_items,
    }
    return render(request, 'admin_order_detail.html', context)


@login_required
def admin_update_order_status(request, order_id):
    if request.user.role != 'admin':
        return HttpResponseForbidden("Access denied.")

    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        payment_status = request.POST.get('payment_status')
        delivery_status = request.POST.get('delivery_status')
        assigned_driver_id = request.POST.get('assigned_driver')

        if payment_status:
            order.payment_status = payment_status
        if delivery_status:
            order.delivery_status = delivery_status
        if assigned_driver_id:
            driver = get_object_or_404(CustomUser, id=assigned_driver_id, role='driver')
            order.assigned_delivery_guy = driver

        order.save()
        messages.success(request, f"Order #{order.id} updated successfully.")
        return redirect('admin_order_detail', order_id=order.id)

    # Get available drivers
    available_drivers = CustomUser.objects.filter(role='driver', account_status='active')

    context = {
        'order': order,
        'available_drivers': available_drivers,
    }
    return render(request, 'admin_update_order_status.html', context)


@login_required
def admin_bulk_product_action(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden("Access denied.")

    if request.method == 'POST':
        action = request.POST.get('action')
        product_ids = request.POST.getlist('product_ids')

        if not product_ids:
            messages.error(request, "No products selected.")
            return redirect('admin_dashboard')

        if action == 'approve':
            UpcycledProduct.objects.filter(id__in=product_ids, approval_status=False).update(approval_status=True)
            messages.success(request, f"Approved {len(product_ids)} product(s).")
        elif action == 'reject':
            UpcycledProduct.objects.filter(id__in=product_ids, approval_status=False).delete()
            messages.success(request, f"Rejected and removed {len(product_ids)} product(s).")

    return redirect('admin_dashboard')


@login_required
def admin_content_moderation(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden("Access denied.")

    # Get pending products with filtering
    status_filter = request.GET.get('status', 'pending')
    category_filter = request.GET.get('category', '')
    search_query = request.GET.get('search', '')

    products = UpcycledProduct.objects.all()

    if status_filter == 'pending':
        products = products.filter(approval_status=False)
    elif status_filter == 'approved':
        products = products.filter(approval_status=True)

    if category_filter:
        products = products.filter(category__icontains=category_filter)

    if search_query:
        products = products.filter(
            Q(product_name__icontains=search_query) |
            Q(artisan__name__icontains=search_query) |
            Q(artisan__username__icontains=search_query)
        )

    products = products.select_related('artisan').order_by('-listing_date')
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get statistics
    pending_count = UpcycledProduct.objects.filter(approval_status=False).count()
    approved_count = UpcycledProduct.objects.filter(approval_status=True).count()

    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'search_query': search_query,
        'pending_count': pending_count,
        'approved_count': approved_count,
    }
    return render(request, 'admin_content_moderation.html', context)


@login_required
def reject_product(request, model_name, object_id):
    if request.user.role != 'admin':
        return HttpResponseForbidden("Access denied.")

    ct = get_object_or_404(ContentType, model=model_name)
    product = get_object_or_404(ct.model_class(), pk=object_id)

    if hasattr(product, 'approval_status'):
        product.delete()  # Or set to rejected status if you want to keep records
        messages.success(request, f"{model_name.title()} rejected and removed.")
    else:
        messages.error(request, "Invalid product type.")

    return redirect('admin_dashboard')

def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if order.delivery_status in ['ready', 'packed']:
        order.delivery_status = 'cancelled'
        order.save()
        messages.success(request, f"Order #{order.id} has been cancelled successfully.")
    elif order.delivery_status == 'on the way':
        messages.warning(request, f"Order #{order.id} is on the way and cannot be cancelled.")
    else:
        messages.error(request, f"Order #{order.id} cannot be cancelled at this stage.")

    return redirect('my_orders')  # Adjust this to your actual orders list view name


@login_required
def write_review(request, order_id):
    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    # only allow reviews once delivered or returned
    if order.delivery_status not in ['delivered','returned']:
        return redirect('order_details', order_id=order.id)

    # gather items that still need a review
    reviewable_items = []
    for item in order.items.all():
        ct = ContentType.objects.get_for_model(item.item)
        already = Review.objects.filter(
            reviewer=request.user,
            content_type=ct,
            object_id=item.item.id
        ).exists()
        if not already:
            reviewable_items.append(item.item)

    # check if driver needs review
    driver_pending = False
    driver_profile = None

    if order.assigned_delivery_guy:
        try:
            driver_profile = order.assigned_delivery_guy.driverprofile
        except DriverProfile.DoesNotExist:
            # if you want, create one on the fly:
            driver_profile, created = DriverProfile.objects.get_or_create(user=order.assigned_delivery_guy)
        
        # now driver_profile is guaranteed
        ct_drv = ContentType.objects.get_for_model(driver_profile)
        has_review = DriverRating.objects.filter(
            driver=driver_profile,
            rated_by=request.user,
            order=order
        ).exists()
        driver_pending = not has_review


    if request.method == 'POST':
        # Create reviews for products
        for idx, product in enumerate(reviewable_items):
            rating = int(request.POST.get(f"rating_{idx}", 0))
            comment = request.POST.get(f"comment_{idx}", "").strip()
            if rating:
                ct = ContentType.objects.get_for_model(product)
                Review.objects.create(
                    reviewer=request.user,
                    rating=rating,
                    comment=comment,
                    content_type=ct,
                    object_id=product.id
                )
                # update product's avg
                avg = Review.objects.filter(
                    content_type=ct, object_id=product.id
                ).aggregate(Avg('rating'))['rating__avg'] or 0
                # save back to model
                if isinstance(product, UpcycledProduct):
                    product.rating = avg
                else:
                    product.rating = avg
                product.save()

        # Create review for driver
        if driver_pending:
            dr_rating = int(request.POST.get("rating_driver", 0))
            dr_comment = request.POST.get("comment_driver", "").strip()
            if dr_rating:
                DriverRating.objects.create(
                    driver   = driver_profile,
                    rated_by = request.user,
                    order    = order,
                    rating   = dr_rating,
                    comment  = dr_comment
                )
                # update driver's avg over all DriverRating
                avg = driver_profile.ratings.aggregate(
                          avg=Avg('rating')
                      )['avg'] or 0
                driver_profile.rating = avg
                driver_profile.save()

        return redirect('order_details', order_id=order.id)
    print("Assigned driver:", order.assigned_delivery_guy)
    print("DriverProfile:", driver_profile)
    print("Driver pending?:", driver_pending)

    return render(request, 'write_review.html', {
        'order': order,
        'reviewable_items': reviewable_items,
        'driver_pending': driver_pending,
        'driver': driver_profile,
    })
    
@login_required
def driver_reviews(request):
    if request.user.role != 'driver':
        return HttpResponseForbidden("Access denied.")

    # fetch the DriverProfile
    try:
        driver = request.user.driverprofile
    except DriverProfile.DoesNotExist:
        return HttpResponseForbidden("No driver profile found.")

    # **use DriverRating**, not Review**
    reviews = DriverRating.objects.filter(
        driver=driver
    ).order_by('-created_at')

    return render(request, 'driver_reviews.html', {
        'driver':  driver,
        'reviews': reviews,
    })
 

@login_required
def waste_seller_listed_waste(request):
    if request.user.role != 'waste_seller':
        return HttpResponseForbidden("You are not authorized to view this page.")

    waste_items = TrashItem.objects.filter(seller=request.user)

    # Pagination logic
    paginator = Paginator(waste_items, 12) # 12 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'waste_seller_listed_waste.html', {
        'waste_items': waste_items,
        'page_obj': page_obj
    })

@login_required
def add_waste_listing(request):
    if request.user.role != 'waste_seller':
        return HttpResponseForbidden("Not allowed")

    if request.method == 'POST':
        # You'll need to create a TrashItemForm similar to UpcycledProductForm
        # For now, let's assume you have it
        form = TrashItemForm(request.POST, request.FILES)
        if form.is_valid():
            waste_item = form.save(commit=False)
            waste_item.seller = request.user
            waste_item.product_status = 'active'
            waste_item.approval_status = True  # Auto-approved for waste items
            waste_item.save()
            messages.success(request, "Waste item listed successfully!")
            return redirect('waste_seller_listed_waste')
    else:
        form = TrashItemForm()

    return render(request, 'add_waste_listing.html', {'form': form})

@login_required
def edit_waste_listing(request, pk):
    waste_item = get_object_or_404(TrashItem, pk=pk, seller=request.user)
    if request.method == 'POST':
        form = TrashItemForm(request.POST, request.FILES, instance=waste_item)
        if form.is_valid():
            form.save()
            return redirect('waste_seller_listed_waste')
    else:
        form = TrashItemForm(instance=waste_item)
    return render(request, 'edit_waste_listing.html', {'form': form, 'waste_item': waste_item})

@login_required
def delete_waste_listing(request, pk):
    waste_item = get_object_or_404(TrashItem, pk=pk, seller=request.user)
    if request.method == 'POST':
        waste_item.delete()
        messages.success(request, 'Waste item deleted successfully.')
        return redirect('waste_seller_listed_waste')
    return redirect('waste_seller_listed_waste')

@login_required
def search_page(request):
    q = request.GET.get('q', '').strip()
    type_filter = request.GET.get('type', 'all')  # all | trash | upcycled
    sort = request.GET.get('sort', '')  # ← new

    # Base QuerySets
    trash_qs = TrashItem.objects.none()
    upcycled_qs = UpcycledProduct.objects.none()

    if q:
        if type_filter in ('all', 'trash'):
            trash_qs = TrashItem.objects.filter(
                Q(material_name__icontains=q) |
                Q(category__icontains=q) |
                Q(tags__icontains=q),
                product_status='active',
                approval_status=True
            )
            for obj in trash_qs:
                setattr(obj, 'stype', 'trash')

        if type_filter in ('all', 'upcycled'):
            upcycled_qs = UpcycledProduct.objects.filter(
                Q(product_name__icontains=q) |
                Q(category__icontains=q) |
                Q(tags__icontains=q),
                product_status='active',
                approval_status=True
            )
            for obj in upcycled_qs:
                setattr(obj, 'stype', 'upcycled')

    # Merge and sort by newest listing_date
    combined = sorted(
        chain(trash_qs, upcycled_qs),
        key=lambda x: x.listing_date,
        reverse=True
    )
    
     # apply sorting
    if sort == 'price_low':
        combined.sort(key=lambda x: x.price)
    elif sort == 'price_high':
        combined.sort(key=lambda x: x.price, reverse=True)
    else:
        # default: newest listing_date (or created_at)
        combined.sort(
            key=lambda x: getattr(x, 'listing_date', x.listing_date),
            reverse=True
        )

    # Paginate
    paginator = Paginator(combined, 12)  # 12 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'search.html', {
        'query': q,
        'type_filter': type_filter,
        'sort':         sort,     
        'page_obj': page_obj,
    })