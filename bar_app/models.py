"""
Modelos do sistema de gestão do bar escolar
Implementa herança de utilizadores e gestão de pedidos
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from datetime import datetime


class User(AbstractUser):
    """
    Modelo base de utilizador
    """
    USER_TYPE_CHOICES = (
        ('aluno', 'Aluno'),
        ('professor', 'Professor'),
        ('staff', 'Funcionário'),
        ('admin', 'Administrador'),
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='aluno', verbose_name='Tipo de Utilizador')
    phone = models.CharField(max_length=15, blank=True, verbose_name='Telefone')
    photo = models.ImageField(upload_to='users/', blank=True, null=True, verbose_name='Foto')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Saldo')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = "Utilizador" 
        verbose_name_plural = "Utilizadores" 
        ordering = ['username']
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_user_type_display()})"
    
    def is_priority_user(self):
        """Professores e funcionários têm prioridade"""
        return self.user_type in ['professor', 'staff', 'admin']
    
    def can_place_order(self):
        """Verifica se pode fazer pedidos"""
        return self.is_active and self.balance >= 0


class Student(models.Model):
    """
    Extensão do modelo User para alunos
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    student_number = models.CharField(max_length=20, unique=True, verbose_name='Número de Aluno')
    grade = models.CharField(max_length=10, verbose_name='Ano')
    class_name = models.CharField(max_length=10, verbose_name='Turma')
    parent_phone = models.CharField(max_length=15, blank=True, verbose_name='Telefone do Encarregado')

    class Meta:
        verbose_name = "Aluno" 
        verbose_name_plural = "Alunos" 
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.student_number}"


class Teacher(models.Model):
    """
    Extensão do modelo User para professores
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    employee_number = models.CharField(max_length=20, unique=True, verbose_name='Número de Funcionário')
    department = models.CharField(max_length=100, verbose_name='Departamento')
    
    class Meta:
        verbose_name = "Professor" 
        verbose_name_plural = "Professores" 

    def __str__(self):
        return f"Prof. {self.user.get_full_name()}"


class Staff(models.Model):
    """
    Extensão do modelo User para funcionários
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    employee_number = models.CharField(max_length=20, unique=True, verbose_name='Número de Funcionário')
    position = models.CharField(max_length=100, verbose_name='Cargo')
    
    class Meta:
        verbose_name = "Funcionário" 
        verbose_name_plural = "Funcionários" 
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.position}"


class Category(models.Model):
    """
    Categoria de produtos
    """
    name = models.CharField(max_length=100, unique=True, verbose_name='Nome')
    description = models.TextField(blank=True, verbose_name='Descrição')
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name='Imagem')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    
    class Meta:
        verbose_name = "Categoria" 
        verbose_name_plural = "Categorias" 
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Produto disponível no bar
    """
    name = models.CharField(max_length=200, verbose_name='Nome')
    description = models.TextField(blank=True, verbose_name='Descrição')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products', verbose_name='Categoria')
    price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], verbose_name='Preço')
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name='Imagem')
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)], verbose_name='Stock')
    min_stock = models.IntegerField(default=10, validators=[MinValueValidator(0)], verbose_name='Stock Mínimo')
    is_available = models.BooleanField(default=True, verbose_name='Disponível')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = "Produto" 
        verbose_name_plural = "Produtos" 
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} - €{self.price}"
    
    def is_in_stock(self):
        """Verifica se há stock disponível"""
        return self.stock > 0
    
    def needs_restock(self):
        """Verifica se precisa de reabastecimento"""
        return self.stock <= self.min_stock


class Order(models.Model):
    """
    Pedido realizado por um utilizador
    """
    STATUS_CHOICES = (
        ('pending', 'Pendente'),
        ('confirmed', 'Confirmado'),
        ('preparing', 'Em Preparação'),
        ('ready', 'Pronto'),
        ('delivered', 'Entregue'),
        ('cancelled', 'Cancelado'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('card', 'Cartão Pré-carregado'),
        ('atm', 'Multibanco'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', verbose_name='Utilizador')
    order_number = models.CharField(max_length=20, unique=True, editable=False, verbose_name='Nº Pedido')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Estado')
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, verbose_name='Método de Pagamento')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Valor Total')
    scheduled_date = models.DateField(verbose_name='Data Agendada')
    scheduled_time = models.TimeField(verbose_name='Hora Agendada')
    notes = models.TextField(blank=True, verbose_name='Notas')
    is_priority = models.BooleanField(default=False, verbose_name='Prioridade')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = "Pedido" 
        verbose_name_plural = "Pedidos" 
        ordering = ['-is_priority', 'scheduled_date', 'scheduled_time', 'created_at']
    
    def __str__(self):
        return f"Pedido {self.order_number} - {self.user.username}"
    
    # ... (métodos save, calculate_total, can_be_cancelled)


class OrderItem(models.Model):
    """
    Item individual de um pedido
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='Pedido')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name='Produto')
    quantity = models.IntegerField(validators=[MinValueValidator(1)], verbose_name='Quantidade')
    unit_price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Preço Unitário')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Subtotal')
    
    class Meta:
        verbose_name = "Item do Pedido" 
        verbose_name_plural = "Itens do Pedido" 
        ordering = ['product__name']
    
    def __str__(self):
        return f"{self.quantity}x {self.product.name}"
    
    # ... (método save)


class Transaction(models.Model):
    """
    Transação financeira (carregamentos e pagamentos)
    """
    TRANSACTION_TYPE_CHOICES = (
        ('topup', 'Carregamento'),
        ('payment', 'Pagamento'),
        ('refund', 'Reembolso'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions', verbose_name='Utilizador')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES, verbose_name='Tipo de Transação')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions', verbose_name='Pedido Relacionado')
    description = models.CharField(max_length=200, verbose_name='Descrição')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    
    class Meta:
        verbose_name = "Transação" 
        verbose_name_plural = "Transações" 
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - €{self.amount} - {self.user.username}"
    
    # 🛑 CORREÇÃO CRUCIAL: Atualizar o saldo do utilizador ao guardar a transação 🛑
    def save(self, *args, **kwargs):
        # Verifica se o objeto está a ser criado (e não atualizado)
        if self.pk is None:
            # Obtém o utilizador para atualização
            user_to_update = self.user
            
            # Ajusta o saldo do utilizador: aumenta em carregamento/reembolso, diminui em pagamento
            if self.transaction_type == 'topup' or self.transaction_type == 'refund':
                user_to_update.balance += self.amount
            elif self.transaction_type == 'payment':
                user_to_update.balance -= self.amount
            
            # 1. Guarda a Transação na DB
            super().save(*args, **kwargs)
            
            # 2. Guarda o Utilizador com o saldo atualizado
            user_to_update.save()
            return
            
        # Se for uma atualização de uma transação existente, apenas guarda a transação.
        super().save(*args, **kwargs)


class StockMovement(models.Model):
    """
    Movimento de stock (entradas e saídas)
    """
    MOVEMENT_TYPE_CHOICES = (
        ('in', 'Entrada'),
        ('out', 'Saída'),
        ('adjustment', 'Ajuste'),
    )
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='movements', verbose_name='Produto')
    movement_type = models.CharField(max_length=15, choices=MOVEMENT_TYPE_CHOICES, verbose_name='Tipo de Movimento')
    quantity = models.IntegerField(verbose_name='Quantidade')
    reason = models.CharField(max_length=200, verbose_name='Razão')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Pedido Relacionado')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='Criado por')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    
    class Meta:
        verbose_name = "Movimento de Stock" 
        verbose_name_plural = "Movimentos de Stock" 
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product.name} - {self.get_movement_type_display()} - {self.quantity}"