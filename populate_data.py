# -*- coding: utf-8 -*-
"""
Script to populate test data for Library Management System
Run: python populate_data.py
"""
import os
import django
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_system.settings')
django.setup()

from core.models import Category, Book, Reader, Loan

# Clear existing data
Loan.objects.all().delete()
Book.all_objects.all().delete()
Reader.objects.all().delete()
Category.objects.all().delete()

print("Creating categories...")
cat_van_hoc = Category.objects.create(name="Văn học")
cat_khtn = Category.objects.create(name="Khoa học tự nhiên")
cat_thieu_nhi = Category.objects.create(name="Thiếu nhi")
print(f"✓ Created {Category.objects.count()} categories")

print("\nCreating books...")
book1 = Book.objects.create(
    code="VH001",
    title="Dế Mèn Phiêu Lưu Ký",
    category=cat_thieu_nhi,
    author="Tô Hoài",
    publisher="NXB Kim Đồng",
    price=50000,
    total_quantity=5,
    available=5
)
book2 = Book.objects.create(
    code="VH002",
    title="Số Đỏ",
    category=cat_van_hoc,
    author="Vũ Trọng Phụng",
    publisher="NXB Văn học",
    price=80000,
    total_quantity=3,
    available=3
)
book3 = Book.objects.create(
    code="KH001",
    title="Vật Lý Đại Cương",
    category=cat_khtn,
    author="Nguyễn Văn A",
    publisher="NXB Giáo dục",
    price=120000,
    total_quantity=4,
    available=4
)
book4 = Book.objects.create(
    code="VH003",
    title="Chí Phèo",
    category=cat_van_hoc,
    author="Nam Cao",
    publisher="NXB Văn học",
    price=60000,
    total_quantity=2,
    available=2
)
book5 = Book.objects.create(
    code="TN001",
    title="Doraemon Tập 1",
    category=cat_thieu_nhi,
    author="Fujiko F. Fujio",
    publisher="NXB Kim Đồng",
    price=25000,
    total_quantity=10,
    available=10
)
# Create an inactive (deleted) book
book6 = Book.all_objects.create(
    code="VH999",
    title="Sách Đã Hủy",
    category=cat_van_hoc,
    author="Unknown",
    publisher="NXB Test",
    price=10000,
    total_quantity=1,
    available=0,
    is_active=False
)
print(f"✓ Created {Book.all_objects.count()} books (including 1 inactive)")

print("\nCreating readers...")
reader1 = Reader.objects.create(
    card_id="BD001",
    full_name="Nguyễn Văn A",
    phone="0901234567"
)
reader2 = Reader.objects.create(
    card_id="BD002",
    full_name="Trần Thị B",
    phone="0912345678"
)
reader3 = Reader.objects.create(
    card_id="BD003",
    full_name="Lê Văn C",
    phone="0923456789"
)
print(f"✓ Created {Reader.objects.count()} readers")

print("\nCreating loans...")
# Test case 1: Normal loan (should decrease available)
loan1 = Loan.objects.create(
    reader=reader1,
    book=book1,
    borrow_date=date(2026, 1, 1),
    due_date=date(2026, 1, 15),
    status='borrowing'
)
print(f"✓ Loan 1: {reader1.full_name} borrowed {book1.title}")
print(f"  Book available: {Book.objects.get(pk=book1.pk).available} (should be 4)")

# Test case 2: Overdue loan (returned late, should have fine)
loan2 = Loan.objects.create(
    reader=reader2,
    book=book2,
    borrow_date=date(2026, 1, 1),
    due_date=date(2026, 1, 7),
    return_date=date(2026, 1, 10),  # 3 days late
    status='returned'
)
print(f"✓ Loan 2: {reader2.full_name} returned {book2.title} late")
print(f"  Fine: {loan2.fine} VNĐ (should be 3000)")
print(f"  Book available: {Book.objects.get(pk=book2.pk).available} (should be 3)")

# Test case 3: Another active loan
loan3 = Loan.objects.create(
    reader=reader3,
    book=book3,
    borrow_date=date(2026, 1, 5),
    due_date=date(2026, 1, 19),
    status='borrowing'
)
print(f"✓ Loan 3: {reader3.full_name} borrowed {book3.title}")

# Test case 4: Multiple loans from same book
loan4 = Loan.objects.create(
    reader=reader2,
    book=book5,
    borrow_date=date(2025, 12, 20),
    due_date=date(2026, 1, 3),
    return_date=date(2026, 1, 2),
    status='returned'
)
loan5 = Loan.objects.create(
    reader=reader3,
    book=book5,
    borrow_date=date(2025, 12, 25),
    due_date=date(2026, 1, 8),
    return_date=date(2026, 1, 8),
    status='returned'
)
print(f"✓ Created multiple loans for {book5.title}")
print(f"  Total loans: {book5.loans.count()} (for statistics test)")

print("\n" + "="*60)
print("TEST DATA SUMMARY")
print("="*60)
print(f"Categories: {Category.objects.count()}")
print(f"Books (active): {Book.objects.count()}")
print(f"Books (total): {Book.all_objects.count()}")
print(f"Readers: {Reader.objects.count()}")
print(f"Loans: {Loan.objects.count()}")
print("\nACCEPTANCE CRITERIA TO VERIFY:")
print("1. Check book 'Dế Mèn' has available = 4 (decreased)")
print("2. Check loan by Trần Thị B shows fine = 3,000 VNĐ in RED")
print("3. Try to borrow book with available = 0 (should fail)")
print("4. Check 'Doraemon Tập 1' shows loan_count = 2 in book list")
print("5. Check reader detail page shows inline loan history")
print("6. Check inactive book not shown in loan book dropdown")
print("\nLogin: admin / admin")
print("URL: http://127.0.0.1:8000/admin/")
print("="*60)
