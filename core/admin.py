from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from .models import Category, Book, Reader, Loan


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['code', 'title', 'category', 'author', 'publisher', 'price', 
                    'total_quantity', 'available', 'is_active', 'loan_count']
    list_filter = ['category', 'is_active']
    search_fields = ['code', 'title', 'author']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Use all_objects to show inactive books in admin
        qs = Book.all_objects.annotate(loan_count=Count('loans'))
        return qs
    
    @admin.display(description='Số lần mượn', ordering='loan_count')
    def loan_count(self, obj):
        return obj.loan_count


class LoanInline(admin.TabularInline):
    model = Loan
    extra = 0
    readonly_fields = ['borrow_date', 'due_date', 'return_date', 'book', 'status']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Reader)
class ReaderAdmin(admin.ModelAdmin):
    list_display = ['card_id', 'full_name', 'phone', 'created_at']
    search_fields = ['card_id', 'full_name', 'phone']
    inlines = [LoanInline]


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ['reader', 'book', 'borrow_date', 'due_date', 'return_date', 'status', 'display_fine']
    list_filter = ['status', 'borrow_date', 'due_date']
    search_fields = ['reader__card_id', 'reader__full_name', 'book__code', 'book__title']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('book', 'reader')
    
    @admin.display(description='Tiền phạt', ordering='due_date')
    def display_fine(self, obj):
        fine_amount = obj.fine
        if fine_amount > 0:
            formatted_amount = f'{fine_amount:,}'
            return format_html('<span style="color: red; font-weight: bold;">{} VNĐ</span>', formatted_amount)
        return '0 VNĐ'
