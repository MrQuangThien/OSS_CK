from django.db import models
from django.contrib.auth.models import User

# 1. Bảng Loại Hàng (Category)
class LoaiHang(models.Model):
    ten_loai = models.CharField(max_length=200)

    def __str__(self):
        return self.ten_loai

# 2. Bảng Sản Phẩm (Product)
class SanPham(models.Model):
    loai_hang = models.ForeignKey(LoaiHang, on_delete=models.CASCADE)
    ten_san_pham = models.CharField(max_length=255)
    gia_ban = models.DecimalField(max_digits=10, decimal_places=0) 
    la_san_pham_moi = models.BooleanField(default=True) 
    la_san_pham_noi_bat = models.BooleanField(default=False) 

    def __str__(self):
        return self.ten_san_pham

# 3. Bảng Khách Hàng (Customer)
class KhachHang(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    so_dien_thoai = models.CharField(max_length=15)
    dia_chi = models.TextField()

    def __str__(self):
        return self.user.username

# 4. Bảng Nhân Viên (Employee)
class NhanVien(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    chuc_vu = models.CharField(max_length=100)

    def __str__(self):
        return self.user.username

# 5. Bảng Kho Hàng (Inventory)
class KhoHang(models.Model):
    san_pham = models.OneToOneField(SanPham, on_delete=models.CASCADE)
    so_luong_ton = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.san_pham.ten_san_pham} - Tồn: {self.so_luong_ton}"

# 6. Bảng Nhập Kho (Stock In)
class NhapKho(models.Model):
    san_pham = models.ForeignKey(SanPham, on_delete=models.CASCADE)
    nhan_vien = models.ForeignKey(NhanVien, on_delete=models.SET_NULL, null=True)
    so_luong_nhap = models.IntegerField()
    ngay_nhap = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Nhập {self.so_luong_nhap} - {self.san_pham.ten_san_pham}"

# 7. Bảng Đơn Hàng (Order)
class DonHang(models.Model):
    khach_hang = models.ForeignKey(KhachHang, on_delete=models.CASCADE)
    ngay_dat_hang = models.DateTimeField(auto_now_add=True)
    tong_tien = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    trang_thai = models.CharField(max_length=50, default="Chờ xử lý")

    def __str__(self):
        return f"Đơn hàng {self.id} - {self.khach_hang.user.username}"

# 8. Bảng Chi Tiết Đơn Hàng (Order Detail)
class ChiTietDonHang(models.Model):
    don_hang = models.ForeignKey(DonHang, on_delete=models.CASCADE)
    san_pham = models.ForeignKey(SanPham, on_delete=models.CASCADE)
    so_luong_mua = models.IntegerField()
    don_gia = models.DecimalField(max_digits=10, decimal_places=0)

    def __str__(self):
        return f"{self.don_hang.id} - {self.san_pham.ten_san_pham}"