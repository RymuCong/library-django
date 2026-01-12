from django.db import models
from django.core.exceptions import ValidationError
from datetime import timedelta, date


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Tên thể loại")
    
    class Meta:
        verbose_name = verbose_name_plural = "Thể loại"
    
    def __str__(self):
        return self.name


class ActiveBookManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class Book(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="Mã sách")
    title = models.CharField(max_length=200, verbose_name="Tên sách")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, verbose_name="Thể loại")
    author = models.CharField(max_length=200, verbose_name="Tác giả")
    publisher = models.CharField(max_length=200, verbose_name="Nhà xuất bản")
    price = models.IntegerField(verbose_name="Giá bìa")
    total_quantity = models.IntegerField(verbose_name="Tổng số lượng")
    available = models.IntegerField(verbose_name="Số lượng hiện có")
    is_active = models.BooleanField(default=True, verbose_name="Đang sử dụng")
    
    objects = ActiveBookManager()
    all_objects = models.Manager()
    
    class Meta:
        verbose_name = verbose_name_plural = "Sách"
    
    def __str__(self):
        return f"{self.code} - {self.title}"
    
    def clean(self):
        if self.available < 0 or self.available > self.total_quantity:
            raise ValidationError({'available': 'Số lượng không hợp lệ'})


class Reader(models.Model):
    card_id = models.CharField(max_length=50, unique=True, verbose_name="Mã thẻ")
    full_name = models.CharField(max_length=200, verbose_name="Họ tên")
    phone = models.CharField(max_length=20, verbose_name="Số điện thoại")
    created_at = models.DateField(auto_now_add=True, verbose_name="Ngày cấp thẻ")
    
    class Meta:
        verbose_name = verbose_name_plural = "Bạn đọc"
    
    def __str__(self):
        return f"{self.card_id} - {self.full_name}"


class Loan(models.Model):
    STATUS_CHOICES = [('borrowing', 'Đang mượn'), ('returned', 'Đã trả')]
    
    reader = models.ForeignKey(Reader, on_delete=models.PROTECT, verbose_name="Bạn đọc")
    book = models.ForeignKey(Book, on_delete=models.PROTECT, related_name='loans', verbose_name="Sách")
    borrow_date = models.DateField(default=date.today, verbose_name="Ngày mượn")
    due_date = models.DateField(verbose_name="Hạn trả")
    return_date = models.DateField(null=True, blank=True, verbose_name="Ngày trả thực tế")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='borrowing', verbose_name="Trạng thái")
    
    class Meta:
        verbose_name = verbose_name_plural = "Phiếu mượn"
    
    def __str__(self):
        return f"{self.reader.full_name} - {self.book.title}"
    
    @property
    def fine(self):
        if self.return_date and self.return_date > self.due_date:
            return (self.return_date - self.due_date).days * 1000
        return 0
    
    def save(self, *args, **kwargs):
        if not self.due_date:
            self.due_date = self.borrow_date + timedelta(days=14)
        
        is_new = self.pk is None
        old_status = None if is_new else Loan.objects.filter(pk=self.pk).values_list('status', flat=True).first()
        
        if (is_new or old_status == 'returned') and self.status == 'borrowing' and self.book.available <= 0:
            raise ValidationError(f'Sách "{self.book.title}" đã hết')
        
        super().save(*args, **kwargs)
        
        if is_new and self.status == 'borrowing':
            self.book.available -= 1
            self.book.save()
        elif not is_new and old_status != self.status:
            if old_status == 'borrowing' and self.status == 'returned':
                self.book.available += 1
                self.book.save()
            elif old_status == 'returned' and self.status == 'borrowing':
                self.book.available -= 1
                self.book.save()


class Damage(models.Model):
    DAMAGE_TYPE_CHOICES = [('lost', 'Mất sách'), ('torn', 'Rách/Hư hỏng nặng'), 
                           ('water_damaged', 'Ướt/Hư do nước'), ('minor', 'Hư hỏng nhẹ')]
    
    loan = models.ForeignKey(Loan, on_delete=models.PROTECT, verbose_name="Phiếu mượn")
    damage_type = models.CharField(max_length=20, choices=DAMAGE_TYPE_CHOICES, verbose_name="Loại hư hỏng")
    reported_date = models.DateField(default=date.today, verbose_name="Ngày phát hiện")
    compensation_fee = models.IntegerField(verbose_name="Phí bồi thường")
    is_paid = models.BooleanField(default=False, verbose_name="Đã thanh toán")
    notes = models.TextField(blank=True, verbose_name="Ghi chú")
    
    class Meta:
        verbose_name = verbose_name_plural = "Hư hỏng sách"
        ordering = ['-reported_date']
    
    @property
    def book(self):
        return self.loan.book
    
    @property
    def reader(self):
        return self.loan.reader
    
    def __str__(self):
        return f"{self.book.title} - {self.get_damage_type_display()} ({self.reader.full_name})"
    
    def save(self, *args, **kwargs):
        if not self.compensation_fee:
            fees = {'lost': self.book.price * 2, 'torn': self.book.price, 
                    'water_damaged': self.book.price, 'minor': int(self.book.price * 0.3)}
            self.compensation_fee = fees.get(self.damage_type, 0)
        
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new and self.damage_type == 'lost':
            self.book.total_quantity -= 1
            if self.book.available > self.book.total_quantity:
                self.book.available = self.book.total_quantity
            self.book.save()
