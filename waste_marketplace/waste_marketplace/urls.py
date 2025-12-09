from django.contrib import admin
from django.urls import path
from marketplace.views import login_view, home, checkout
from marketplace.views import driver_dashboard, contact, cart, about, product_listing
from users.views import signup_view, buyer_profile, artisan_profile, driver_profile, waste_seller_profile
from marketplace.views import logout_view  # Assuming you have a logout view
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from marketplace.views import listed_products, order_history  # Assuming you have a view for listed products
from marketplace import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),  # Assuming you have a logout view
    path('signup/', signup_view, name='signup'),  
    path('', home, name='home'),  
    path('driver_dashboard/', driver_dashboard, name='driver_dashboard'),
    path('cart/', cart, name='cart'),
    path('contact/', contact, name='contact'),
    path('about/', about, name='about'),
    path('product_listing/', product_listing, name='product_listing'),
    path('checkout/', checkout, name='checkout'),
    path('buyer_profile/', buyer_profile, name='buyer_profile'),  # Buyer profile page
    path('artisan_profile/', artisan_profile, name='artisan_profile'),
    path('driver_profile/', driver_profile, name='driver_profile'),
    path('waste_seller_profile/', waste_seller_profile, name='waste_seller_profile'),
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='password_change.html'), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='password_change_done.html'), name='password_change_done'),
    path('listed_products/', listed_products, name='listed_products'),  # Artisan's listed products
    path('order_history/', order_history, name='order_history'),
    path('products/<slug:slug>/', views.upcycled_product_details, name='upcycled_product_details'),
    path('upcycled_products/', views.upcycled_products, name='upcycled_products'),
    path('product/<int:pk>/edit/', views.edit_product,   name='edit_product'),
    path('product/<int:pk>/delete/', views.delete_product, name='delete_product'),
    path('add-to-cart/<str:model_name>/<int:object_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('trash-items/', views.trash_item_list, name='trash_item_list'),
    path('trash/<slug:slug>/', views.trash_item_details, name='trash_item_details'),
    path('checkout/place_order/', views.place_order, name='place_order'),
    path('order-success/', views.order_success, name='order_success'),
    path('initiate-payment/', views.initiate_payment, name='initiate_payment'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/fail/', views.payment_fail, name='payment_fail'),
    path('payment/cancel/', views.payment_cancel, name='payment_cancel'),
    path('payment/ipn/', views.payment_ipn, name='payment_ipn'),
    path('payment/waiting/', views.payment_waiting, name='payment_waiting'),
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('order/<int:order_id>/', views.order_details, name='order_details'),
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('driver/update-status/<int:order_id>/',views.update_delivery_status,name='update_delivery_status'),
    path('driver/update-expected/<int:order_id>/',views.update_expected_delivery,name='update_expected_delivery'),
    path('driver/delivery-history/', views.delivery_history, name='delivery_history'),
    path('orders/<int:order_id>/review/', views.write_review, name='write_review'),
    path('driver/reviews/', views.driver_reviews, name='driver_reviews'),
    path('search/', views.search_page, name='search_results'),
    path('waste_seller/listed-waste/', views.waste_seller_listed_waste, name='waste_seller_listed_waste'),
    path('waste_seller/add-waste/', views.add_waste_listing, name='add_waste_listing'),
    path('waste_seller/edit-waste/<int:pk>/', views.edit_waste_listing, name='edit_waste_listing'),
    path('waste_seller/delete-waste/<int:pk>/', views.delete_waste_listing, name='delete_waste_listing'),
    path('privacy/', views.privacy, name='privacy'),
    path('help/', views.help, name='help'),
    path('terms/', views.terms, name='terms'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/users/', views.admin_user_management, name='admin_user_management'),
    path('admin-panel/users/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
    path('admin-panel/users/<int:user_id>/toggle-status/', views.admin_toggle_user_status, name='admin_toggle_user_status'),
    path('admin-panel/orders/', views.admin_order_management, name='admin_order_management'),
    path('admin-panel/orders/<int:order_id>/', views.admin_order_detail, name='admin_order_detail'),
    path('admin-panel/orders/<int:order_id>/update/', views.admin_update_order_status, name='admin_update_order_status'),
    path('admin-panel/content/', views.admin_content_moderation, name='admin_content_moderation'),
    path('admin-panel/bulk-product-action/', views.admin_bulk_product_action, name='admin_bulk_product_action'),
    path('approve/<str:model_name>/<int:object_id>/', views.approve_product, name='approve_product'),
    path('reject/<str:model_name>/<int:object_id>/', views.reject_product, name='reject_product'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)