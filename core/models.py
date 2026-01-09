from django.db import models
from django.core.exceptions import ValidationError
from datetime import timedelta, date


class Category(models.Model):
    """Thể loại sách"""
    name = models.CharField(max_length=100, verbose_name="Tên thể loại")
    
    class Meta:
        verbose_name = "Thể loại"
        verbose_name_plural = "Thể loại"
    
    def __str__(self):
        return self.name


class ActiveBookManager(models.Manager):
    """Custom manager to filter only active books by default"""
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class Book(models.Model):
    """Kho sách"""
    code = models.CharField(max_length=50, unique=True, verbose_name="Mã sách")
    title = models.CharField(max_length=200, verbose_name="Tên sách")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, verbose_name="Thể loại")
    author = models.CharField(max_length=200, verbose_name="Tác giả")
    publisher = models.CharField(max_length=200, verbose_name="Nhà xuất bản")
    price = models.IntegerField(verbose_name="Giá bìa")
    total_quantity = models.IntegerField(verbose_name="Tổng số lượng")
    available = models.IntegerField(verbose_name="Số lượng hiện có")
    is_active = models.BooleanField(default=True, verbose_name="Đang sử dụng")
    
    # Use custom manager
    objects = ActiveBookManager()
    all_objects = models.Manager()  # Access all books including inactive
    
    class Meta:
        verbose_name = "Sách"
        verbose_name_plural = "Sách"
    
    def __str__(self):
        return f"{self.code} - {self.title}"
    
    def clean(self):
        """Validate available quantity"""
        if self.available < 0:
            raise ValidationError({'available': 'Số lượng hiện có không thể âm'})
        if self.available > self.total_quantity:
            raise ValidationError({'available': 'Số lượng hiện có không thể lớn hơn tổng số lượng'})


class Reader(models.Model):
    """Bạn đọc"""
    card_id = models.CharField(max_length=50, unique=True, verbose_name="Mã thẻ")
    full_name = models.CharField(max_length=200, verbose_name="Họ tên")
    phone = models.CharField(max_length=20, verbose_name="Số điện thoại")
    created_at = models.DateField(auto_now_add=True, verbose_name="Ngày cấp thẻ")
    
    class Meta:
        verbose_name = "Bạn đọc"
        verbose_name_plural = "Bạn đọc"
    
    def __str__(self):
        return f"{self.card_id} - {self.full_name}"


class Loan(models.Model):
    """Phiếu mượn sách"""
    STATUS_CHOICES = [
        ('borrowing', 'Đang mượn'),
        ('returned', 'Đã trả'),
    ]
    
    reader = models.ForeignKey(Reader, on_delete=models.PROTECT, verbose_name="Bạn đọc")
    book = models.ForeignKey(Book, on_delete=models.PROTECT, related_name='loans', verbose_name="Sách")
    borrow_date = models.DateField(default=date.today, verbose_name="Ngày mượn")
    due_date = models.DateField(verbose_name="Hạn trả")
    return_date = models.DateField(null=True, blank=True, verbose_name="Ngày trả thực tế")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='borrowing', verbose_name="Trạng thái")
    
    class Meta:
        verbose_name = "Phiếu mượn"
        verbose_name_plural = "Phiếu mượn"
    
    def __str__(self):
        return f"{self.reader.full_name} - {self.book.title}"
    
    @property
    def fine(self):
        """Calculate fine for overdue returns (1,000 VNĐ per day)"""
        if self.return_date and self.return_date > self.due_date:
            overdue_days = (self.return_date - self.due_date).days
            return overdue_days * 1000
        return 0
    
    def save(self, *args, **kwargs):
        # Auto-set due_date if not provided (14 days from borrow_date)
        if not self.due_date:
            self.due_date = self.borrow_date + timedelta(days=14)
        
        # Check if this is a new loan
        is_new = self.pk is None
        
        # Get old status if updating
        old_status = None
        if not is_new:
            try:
                old_loan = Loan.objects.get(pk=self.pk)
                old_status = old_loan.status
            except Loan.DoesNotExist:
                pass
        
        # Validate book availability for new loans or status change to borrowing
        if is_new and self.status == 'borrowing':
            if self.book.available <= 0:
                raise ValidationError(f'Sách "{self.book.title}" đã hết. Không thể mượn.')
        elif not is_new and old_status == 'returned' and self.status == 'borrowing':
            # Changing from returned to borrowing: check availability
            if self.book.available <= 0:
                raise ValidationError(f'Sách "{self.book.title}" đã hết. Không thể chuyển về trạng thái đang mượn.')
        
        # Save the loan
        super().save(*args, **kwargs)
        
        # Update book availability based on status changes
        if is_new and self.status == 'borrowing':
            # New loan: decrease available
            self.book.available -= 1
            self.book.save()
        elif not is_new and old_status == 'borrowing' and self.status == 'returned':
            # Changed from borrowing to returned: increase available
            self.book.available += 1
            self.book.save()
        elif not is_new and old_status == 'returned' and self.status == 'borrowing':
            # Changed from returned to borrowing: decrease available
            self.book.available -= 1
            self.book.save()
