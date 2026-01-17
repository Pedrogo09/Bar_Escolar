from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Student, Teacher, Staff,
    Category, Product, Order, OrderItem,
    Transaction, StockMovement
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'user_type', 'balance', 'is_active']
    list_filter = ['user_type', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informação Adicional', {
            'fields': ('user_type', 'phone', 'photo', 'balance')
        }),
    )


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['user', 'student_number', 'grade', 'class_name']
    search_fields = ['user__username', 'student_number', 'user__first_name', 'user__last_name']
    list_filter = ['grade', 'class_name']


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['user', 'employee_number', 'department']
    search_fields = ['user__username', 'employee_number', 'user__first_name', 'user__last_name']
    list_filter = ['department']


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['user', 'employee_number', 'position']
    search_fields = ['user__username', 'employee_number', 'user__first_name', 'user__last_name']
    list_filter = ['position']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'is_available', 'needs_restock']
    list_filter = ['category', 'is_available']
    search_fields = ['name', 'description']
    list_editable = ['price', 'is_available']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['subtotal']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'status', 'payment_method', 'total_amount', 'scheduled_date', 'scheduled_time', 'is_priority']
    list_filter = ['status', 'payment_method', 'is_priority', 'scheduled_date']
    search_fields = ['order_number', 'user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ['order_number', 'total_amount', 'is_priority']
    inlines = [OrderItemInline]
    date_hierarchy = 'scheduled_date'


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'transaction_type', 'amount', 'description', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['user__username', 'description']
    date_hierarchy = 'created_at'


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['product', 'movement_type', 'quantity', 'reason', 'created_by', 'created_at']
    list_filter = ['movement_type', 'created_at']
    search_fields = ['product__name', 'reason']
    date_hierarchy = 'created_at'