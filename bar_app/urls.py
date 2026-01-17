"""
URLs da aplicação bar
"""
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'bar_app'

urlpatterns = [
    # Página inicial
    path('', views.home, name='home'),
    
    # Autenticação
    path('login/', auth_views.LoginView.as_view(template_name='bar_app/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    
    # Menu e produtos
    path('menu/', views.menu, name='menu'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    
    # Carrinho e pedidos
    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:product_id>/', views.update_cart, name='update_cart'),
    path('checkout/', views.checkout, name='checkout'),
    
    # Pedidos
    path('orders/', views.order_list, name='order_list'),
    path('order/<int:pk>/', views.order_detail, name='order_detail'),
    path('order/<int:pk>/cancel/', views.cancel_order, name='cancel_order'),
    
    # Perfil e saldo
    path('profile/', views.profile, name='profile'),
    path('topup/', views.topup, name='topup'),
    path('transactions/', views.transaction_list, name='transaction_list'),
    
    # Painel administrativo (staff)
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/products/', views.manage_products, name='manage_products'),
    path('dashboard/orders/', views.manage_orders, name='manage_orders'),
    path('dashboard/orders/<int:pk>/update-status/', views.update_order_status, name='update_order_status'),
    path('dashboard/stock/', views.manage_stock, name='manage_stock'),
]
