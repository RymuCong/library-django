from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from .models import Category, Book, Reader, Loan, Reservation, Damage


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
    fields = ['book', 'borrow_date', 'due_date', 'return_date', 'status']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


class ReservationInline(admin.TabularInline):
    model = Reservation
    extra = 0
    fields = ['book', 'reserved_date', 'status', 'notified_date', 'expire_date']


class DamageInline(admin.TabularInline):
    model = Damage
    extra = 0
    fields = ['book', 'damage_type', 'reported_date', 'compensation_fee', 'is_paid']


@admin.register(Reader)
class ReaderAdmin(admin.ModelAdmin):
    list_display = ['card_id', 'full_name', 'phone', 'created_at', 'unpaid_damages_count']
    search_fields = ['card_id', 'full_name', 'phone']
    inlines = [LoanInline, ReservationInline, DamageInline]
    
    @admin.display(description='Nợ bồi thường')
    def unpaid_damages_count(self, obj):
        unpaid = Damage.objects.filter(reader=obj, is_paid=False).count()
        if unpaid > 0:
            return format_html('<span style="color: red; font-weight: bold;">{} chưa trả</span>', unpaid)
        return "0"


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


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['reader', 'book', 'reserved_date', 'status', 'display_queue_position', 'notified_date', 'expire_date']
    list_filter = ['status', 'reserved_date']
    search_fields = ['reader__card_id', 'reader__full_name', 'book__code', 'book__title']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('book', 'reader')
    
    @admin.display(description='Vị trí')
    def display_queue_position(self, obj):
        return f"#{obj.queue_position}" if obj.queue_position else "-"


@admin.register(Damage)
class DamageAdmin(admin.ModelAdmin):
    list_display = ['book', 'reader', 'damage_type', 'reported_date', 'display_compensation', 'is_paid', 'loan']
    list_filter = ['damage_type', 'is_paid', 'reported_date']
    search_fields = ['reader__card_id', 'reader__full_name', 'book__code', 'book__title']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('book', 'reader', 'loan')
    
    @admin.display(description='Phí bồi thường', ordering='compensation_fee')
    def display_compensation(self, obj):
        amt = f'{obj.compensation_fee:,}'
        color = 'red' if not obj.is_paid else 'green'
        status = 'Chưa thanh toán' if not obj.is_paid else 'Đã thanh toán'
        return format_html(f'<span style="color: {color}; font-weight: bold;">{amt} VNĐ ({status})</span>')
