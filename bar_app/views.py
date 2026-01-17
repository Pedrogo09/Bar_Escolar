"""
Views da aplicação bar escolar
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Sum, Count, F 
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth import logout as auth_logout, authenticate, login as auth_login
from decimal import Decimal
from django.db import transaction
from django.db.utils import IntegrityError 
from django.core.exceptions import ObjectDoesNotExist 

from .models import (
    User, Product, Category, Order, OrderItem,
    Transaction, StockMovement
)
from .forms import UserRegistrationForm, OrderForm, TopUpForm, ProductForm


def home(request):
    """Página inicial"""
    featured_products = Product.objects.filter(is_available=True)[:6]
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'featured_products': featured_products,
        'categories': categories,
    }
    return render(request, 'bar_app/home.html', context)


def login_view(request):
    """Login de utilizador"""
    if request.user.is_authenticated:
        return redirect('bar_app:menu')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            auth_login(request, user)
            messages.success(request, f'Bem-vindo de volta, {user.first_name or user.username}!')
            next_url = request.GET.get('next', 'bar_app:menu')
            return redirect(next_url)
        else:
            messages.error(request, 'Nome de utilizador ou palavra-passe incorretos.')
    
    return render(request, 'bar_app/login.html')


def register(request):
    """Registo de novo utilizador"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        user_type = request.POST.get('user_type')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # Validações
        if password1 != password2:
            messages.error(request, 'As palavras-passe não coincidem.')
            return render(request, 'bar_app/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Este nome de utilizador já existe.')
            return render(request, 'bar_app/register.html')
        
        if email and User.objects.filter(email=email).exists():
            messages.error(request, 'Este email já está registado.')
            return render(request, 'bar_app/register.html')
        
        # Criar utilizador
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name,
                user_type=user_type
            )
            
            if user_type in ['staff', 'admin']:
                user.is_staff = True
            if user_type == 'admin':
                user.is_superuser = True
            user.save()
            
            # Login automático
            auth_login(request, user)
            messages.success(request, 'Conta criada com sucesso!')
            return redirect('bar_app:menu')
        except Exception as e:
            messages.error(request, f'Erro ao criar conta: {str(e)}')
            return render(request, 'bar_app/register.html')
    
    return render(request, 'bar_app/register.html')


def menu(request):
    """Listagem de produtos (menu)"""
    category_id = request.GET.get('category')
    search = request.GET.get('search')
    
    products = Product.objects.filter(is_available=True)
    
    if category_id:
        products = products.filter(category_id=category_id)
    
    if search:
        products = products.filter(
            Q(name__icontains=search) | Q(description__icontains=search)
        )
    
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'products': products,
        'categories': categories,
        'selected_category': category_id,
        'search': search,
    }
    return render(request, 'bar_app/menu.html', context)


def product_detail(request, pk):
    """Detalhe de um produto"""
    product = get_object_or_404(Product, pk=pk)
    related_products = Product.objects.filter(
        category=product.category,
        is_available=True
    ).exclude(pk=pk)[:4]
    
    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'bar_app/product_detail.html', context)


@login_required
def cart(request):
    """Carrinho de compras"""
    cart_items = request.session.get('cart', {})
    
    items = []
    total = Decimal('0.00')
    
    for product_id, quantity in cart_items.items():
        try:
            product = Product.objects.get(pk=product_id)
            subtotal = product.price * quantity
            total += subtotal
            items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal,
                # Unit price is needed for checkout logic below
                'unit_price': product.price 
            })
        except Product.DoesNotExist:
            pass 
    
    context = {
        'items': items,
        'total': total,
    }
    return render(request, 'bar_app/cart.html', context)


@login_required
def add_to_cart(request, product_id):
    """Adicionar produto ao carrinho"""
    product = get_object_or_404(Product, pk=product_id)
    
    if not product.is_in_stock():
        messages.error(request, 'Produto sem stock.')
        return redirect('bar_app:menu')
    
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)
    
    if product_id_str in cart:
        if product.stock < cart[product_id_str] + 1:
            messages.error(request, f'Stock insuficiente para adicionar mais {product.name}. Stock atual: {product.stock}.')
            return redirect('bar_app:menu')
            
        cart[product_id_str] += 1
    else:
        cart[product_id_str] = 1
    
    request.session['cart'] = cart
    messages.success(request, f'{product.name} adicionado ao carrinho.')
    
    return redirect('bar_app:menu')


@login_required
def remove_from_cart(request, product_id):
    """Remover produto do carrinho"""
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)
    
    if product_id_str in cart:
        del cart[product_id_str]
        request.session['cart'] = cart
        messages.success(request, 'Produto removido do carrinho.')
    
    return redirect('bar_app:cart')


@login_required
def update_cart(request, product_id):
    """Atualizar quantidade no carrinho"""
    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
        except ValueError:
            messages.error(request, 'Quantidade inválida.')
            return redirect('bar_app:cart')
            
        cart = request.session.get('cart', {})
        product_id_str = str(product_id)
        
        if quantity > 0:
            product = get_object_or_404(Product, pk=product_id)
            if product.stock < quantity:
                messages.error(request, f'Stock insuficiente para {product.name}. Stock atual: {product.stock}.')
                return redirect('bar_app:cart')
            
            cart[product_id_str] = quantity
        else:
            del cart[product_id_str]
        
        request.session['cart'] = cart
    
    return redirect('bar_app:cart')


@login_required
def checkout(request):
    """Finalizar pedido com tratamento de retry para IntegrityError"""
    cart = request.session.get('cart', {})
    
    if not cart:
        messages.warning(request, 'O seu carrinho está vazio.')
        return redirect('bar_app:menu')
    
    # ----------------------------------------------------
    # LÓGICA POST (Criação do Pedido)
    # ----------------------------------------------------
    if request.method == 'POST':
        form = OrderForm(request.POST)
        
        if form.is_valid():
            
            max_retries = 3
            final_order = None # Variável para guardar o pedido salvo com sucesso

            # Loop para retry em caso de IntegrityError (race condition)
            for attempt in range(max_retries):
                
                # CORREÇÃO: Usamos um bloco atómico para ISOLAR cada tentativa
                # Se ocorrer um erro (como IntegrityError), apenas este bloco é quebrado/rolado para trás, 
                # permitindo que o loop continue e comece uma nova transação.
                try:
                    with transaction.atomic():
                        
                        # Criar uma nova instância de Order em cada tentativa
                        order = form.save(commit=False)
                        order.user = request.user
                        
                        # Se for uma tentativa de retry (attempt > 0), 
                        # limpamos o PK e order_number para forçar a criação de um novo valor único.
                        if attempt > 0:
                            order.pk = None 
                            order.order_number = None 

                        # Primeira operação de escrita no DB. 
                        # Se falhar por 'UNIQUE constraint', a exceção é levantada e o bloco atomic rola para trás.
                        order.save() 
                        
                        total_amount = Decimal('0.00')

                        # ----------------------------------------------------------------
                        # Lógica de criação de OrderItems, atualização de Stock e Transações
                        # ----------------------------------------------------------------
                        for product_id, quantity in cart.items():
                            try:
                                product = Product.objects.get(pk=product_id)
                            except ObjectDoesNotExist:
                                messages.error(request, f'O produto com ID {product_id} não existe.')
                                raise # Força o rollback
                                
                            quantity = int(quantity)

                            if product.stock < quantity:
                                messages.error(request, f'Stock insuficiente para {product.name}. Stock atual: {product.stock}.')
                                raise # Força o rollback
                            
                            subtotal_value = product.price * quantity 
                            total_amount += subtotal_value
                
                            OrderItem.objects.create(
                                order=order,
                                product=product,
                                quantity=quantity,
                                unit_price=product.price,
                                subtotal=subtotal_value,
                            )
                            
                            StockMovement.objects.create(
                                product=product,
                                movement_type='out',
                                quantity=quantity,
                                reason=f'Pedido {order.order_number}',
                                order=order,
                                created_by=request.user
                            )
                            
                            # Atualizar stock no DB
                            product.stock -= quantity
                            product.save()

                        # Finalizar Order principal (guardar o total)
                        order.total_amount = total_amount
                        order.save()
                        
                        # Processar pagamento
                        if order.payment_method == 'card':
                            if request.user.balance < order.total_amount:
                                messages.error(request, 'Saldo insuficiente. Por favor, carregue o seu saldo.')
                                raise # Força o rollback
                            
                            # Débito do saldo
                            request.user.balance -= order.total_amount
                            request.user.save()
                            
                            Transaction.objects.create(
                                user=request.user,
                                transaction_type='payment',
                                amount=order.total_amount,
                                order=order,
                                description=f'Pagamento pedido {order.order_number}'
                            )
                        
                        # Se chegar aqui, a transação foi commitada com sucesso
                        final_order = order 
                        break # Sai do loop de retry

                except IntegrityError as e:
                    # Captura o erro UNIQUE constraint
                    if 'UNIQUE constraint failed: bar_app_order.order_number' in str(e) and attempt < max_retries - 1:
                        # O bloco atómico rolou para trás. Tenta novamente (próxima iteração do loop)
                        continue 
                    else:
                        # Se for outro IntegrityError ou última tentativa, falha.
                        messages.error(request, 'Erro grave e irrecuperável ao finalizar o pedido. Tente novamente mais tarde.')
                        return redirect('bar_app:cart') 

                except Exception:
                    # Captura exceções levantadas dentro do bloco atómico (e.g., stock, saldo insuficiente, produto não encontrado)
                    # O bloco atómico já fez o rollback (não há TransactionManagementError)
                    return redirect('bar_app:cart') # Redireciona com as mensagens de erro já setadas
            
            
            if final_order:
                # Limpar carrinho e redirecionar
                request.session['cart'] = {}
                messages.success(request, f'Pedido {final_order.order_number} criado com sucesso!')
                return redirect('bar_app:order_detail', pk=final_order.pk)
            
            # Se saiu do loop sem sucesso (todas as retries falharam)
            messages.error(request, 'Não foi possível finalizar o pedido após várias tentativas. Tente novamente.')
            return redirect('bar_app:cart')

        else:
            messages.error(request, 'Erro ao processar o pedido. Verifique os dados.')
            
    # ----------------------------------------------------
    # LÓGICA GET (Renderizar a página de Checkout)
    # ----------------------------------------------------
    else:
        form = OrderForm()
    
    # Calcular total do carrinho para o contexto
    items = []
    total = Decimal('0.00')
    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(pk=product_id)
            subtotal = product.price * quantity
            total += subtotal
            items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal,
            })
        except Product.DoesNotExist:
            continue
    
    context = {
        'form': form,
        'items': items,
        'total': total,
    }
    return render(request, 'bar_app/checkout.html', context)


@login_required
def order_list(request):
    """Listar pedidos do utilizador"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    return render(request, 'bar_app/order_list.html', context)


@login_required
def order_detail(request, pk):
    """Detalhe de um pedido"""
    order = get_object_or_404(Order, pk=pk)
    
    # Verificar se o utilizador pode ver este pedido
    if order.user != request.user and not request.user.is_staff:
        messages.error(request, 'Não tem permissão para ver este pedido.')
        return redirect('bar_app:order_list')
    
    context = {
        'order': order,
    }
    return render(request, 'bar_app/order_detail.html', context)


@login_required
@transaction.atomic
def cancel_order(request, pk):
    """Cancelar um pedido"""
    order = get_object_or_404(Order, pk=pk, user=request.user)
    
    if order.can_be_cancelled():
        order.status = 'cancelled'
        order.save()
        
        # Devolver stock
        for item in order.orderitem_set.all():
            StockMovement.objects.create(
                product=item.product,
                movement_type='in',
                quantity=item.quantity,
                reason=f'Cancelamento pedido {order.order_number}',
                created_by=request.user
            )
            
            # Atualizar o stock do produto 
            item.product.stock += item.quantity
            item.product.save()
        
        # Reembolsar se já foi pago
        if order.payment_method == 'card':
            order.user.balance += order.total_amount 
            order.user.save()
            
            Transaction.objects.create(
                user=request.user,
                transaction_type='topup',
                amount=order.total_amount,
                order=order,
                description=f'Reembolso pedido {order.order_number}'
            )
        
        messages.success(request, 'Pedido cancelado com sucesso.')
    else:
        messages.error(request, 'Este pedido não pode ser cancelado.')
    
    return redirect('bar_app:order_detail', pk=pk)


@login_required
def profile(request):
    """Perfil do utilizador"""
    recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    recent_transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    context = {
        'recent_orders': recent_orders,
        'recent_transactions': recent_transactions,
    }
    return render(request, 'bar_app/profile.html', context)


@login_required
@transaction.atomic
def topup(request):
    """Carregar saldo"""
    if request.method == 'POST':
        form = TopUpForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            
            # Adicionar saldo ao utilizador
            request.user.balance += amount
            request.user.save()
            
            # Criar a transação
            Transaction.objects.create(
                user=request.user,
                transaction_type='topup',
                amount=amount,
                description='Carregamento de saldo'
            )
            
            messages.success(request, f'Saldo carregado com sucesso! Novo saldo: €{request.user.balance}')
            return redirect('bar_app:profile')
    else:
        form = TopUpForm()
    
    context = {
        'form': form,
    }
    return render(request, 'bar_app/topup.html', context)


@login_required
def transaction_list(request):
    """Histórico de transações"""
    transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'transactions': transactions,
    }
    return render(request, 'bar_app/transaction_list.html', context)


# Views administrativas
def is_staff_user(user):
    return user.is_staff or user.user_type in ['admin', 'staff']


@login_required
@user_passes_test(is_staff_user)
def dashboard(request):
    """Painel administrativo"""
    today = timezone.now().date()
    
    # Estatísticas
    total_orders_today = Order.objects.filter(scheduled_date=today).count()
    pending_orders = Order.objects.filter(status__in=['pending', 'confirmed']).count()
    low_stock_products = Product.objects.filter(stock__lte=F('min_stock')).count()
    
    # Pedidos recentes
    recent_orders = Order.objects.all().order_by('-created_at')[:10]
    
    # Produtos mais vendidos
    top_products = Product.objects.annotate(
        total_sold=Sum('orderitem__quantity')
    ).order_by('-total_sold')[:5]
    
    context = {
        'total_orders_today': total_orders_today,
        'pending_orders': pending_orders,
        'low_stock_products': low_stock_products,
        'recent_orders': recent_orders,
        'top_products': top_products,
    }
    return render(request, 'bar_app/dashboard/dashboard.html', context)


@login_required
@user_passes_test(is_staff_user)
def manage_products(request):
    """Gestão de produtos"""
    products = Product.objects.all().order_by('name')
    
    context = {
        'products': products,
    }
    return render(request, 'bar_app/dashboard/products.html', context)


@login_required
@user_passes_test(is_staff_user)
def manage_orders(request):
    """Gestão de pedidos"""
    status_filter = request.GET.get('status')
    
    orders = Order.objects.all().order_by('-created_at')
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    context = {
        'orders': orders,
        'status_filter': status_filter,
    }
    return render(request, 'bar_app/dashboard/orders.html', context)


@login_required
@user_passes_test(is_staff_user)
def update_order_status(request, pk):
    """Atualizar status de um pedido"""
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(request, f'Pedido {order.order_number} atualizado para {order.get_status_display()}.')
        else:
            messages.error(request, 'Status inválido.')
    
    return redirect('bar_app:manage_orders')


@login_required
@user_passes_test(is_staff_user)
def manage_stock(request):
    """Gestão de stock"""
    low_stock_products = Product.objects.filter(stock__lt=10).order_by('stock')
    all_products = Product.objects.all().order_by('name')
    recent_movements = StockMovement.objects.all().order_by('-created_at')[:20]
    
    context = {
        'products': all_products,
        'low_stock_products': low_stock_products,
        'recent_movements': recent_movements,
    }
    return render(request, 'bar_app/dashboard/stock.html', context)


@login_required
def logout_view(request):
    """Logout do utilizador"""
    auth_logout(request)
    messages.success(request, 'Sessão terminada com sucesso.')
    return redirect('bar_app:home')