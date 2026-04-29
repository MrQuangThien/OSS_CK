from django.db import models
from django.contrib.auth.models import User

# 1. Bảng Loại Hàng (Category)
class LoaiHang(models.Model):
    ma_loai = models.CharField(max_length=10, null=True, blank=True, verbose_name="Mã loại")
    ten_loai = models.CharField(max_length=200)

    def __str__(self):
        if self.ma_loai:
            return f"{self.ma_loai} - {self.ten_loai}"
        return self.ten_loai

# 2. Bảng Sản Phẩm (Product)
class SanPham(models.Model):
    loai_hang = models.ForeignKey(LoaiHang, on_delete=models.CASCADE)
    ten_san_pham = models.CharField(max_length=255)
    gia_ban = models.DecimalField(max_digits=10, decimal_places=0) 
    hinh_anh = models.ImageField(upload_to='san_pham/', null=True, blank=True)
    la_san_pham_moi = models.BooleanField(default=True) 
    la_san_pham_noi_bat = models.BooleanField(default=False)
    mo_ta_ngan = models.TextField(blank=True, null=True, verbose_name="Mô tả ngắn")
    uu_dai = models.TextField(blank=True, null=True, verbose_name="Ưu đãi đặc biệt")
    mo_ta_chi_tiet = models.TextField(blank=True, null=True, verbose_name="Mô tả chi tiết")

    def __str__(self):
        return self.ten_san_pham
    
    @property
    def ton_kho(self):
        from .models import KhoHang # Import tại đây để tránh lỗi vòng lặp
        # Tìm xem sản phẩm này đã có trong kho chưa
        kho = KhoHang.objects.filter(san_pham=self).first()
        return kho.so_luong_ton if kho else 0
    
class HinhAnhSanPham(models.Model):
    san_pham = models.ForeignKey(SanPham, on_delete=models.CASCADE)
    hinh_anh = models.ImageField(upload_to='san_pham_gallery/')
    
    def __str__(self):
        return f"Ảnh phụ của {self.san_pham.ten_san_pham}"
    
# 3. Bảng Khách Hàng (Customer)
class KhachHang(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Thêm các trường này
    ho_ten = models.CharField(max_length=255, null=True, blank=True, verbose_name="Họ tên")
    so_dien_thoai = models.CharField(max_length=15, null=True, blank=True, verbose_name="Số điện thoại")
    dia_chi = models.TextField(null=True, blank=True, verbose_name="Địa chỉ giao hàng")

    def __str__(self):
        return self.ho_ten if self.ho_ten else self.user.username

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
# 6. Bảng Nhập Kho (Stock In)
class NhapKho(models.Model):
    san_pham = models.ForeignKey(SanPham, on_delete=models.CASCADE)
    nhan_vien = models.ForeignKey(NhanVien, on_delete=models.SET_NULL, null=True, blank=True)
    so_luong_nhap = models.IntegerField()
    ngay_nhap = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Nhập {self.so_luong_nhap} - {self.san_pham.ten_san_pham}"

    # Hàm tự động chạy mỗi khi bạn bấm Lưu phiếu nhập kho
    def save(self, *args, **kwargs):
        # Kiểm tra xem đây là phiếu tạo mới (chưa có ID) hay là đang sửa phiếu cũ
        la_phieu_moi = self.pk is None 
        
        # 1. Bắt buộc: Lưu phiếu nhập kho này vào Database trước
        super().save(*args, **kwargs) 
        
        # 2. Nếu là phiếu mới, tự động tìm và cộng dồn số lượng vào Kho
        if la_phieu_moi:
            # Tìm xem sản phẩm này đã có dữ liệu trong Kho chưa.
            # Nếu chưa có (created=True), Django sẽ tự động tạo một dòng Kho mới cho nó.
            kho, created = KhoHang.objects.get_or_create(san_pham=self.san_pham)
            
            # Cộng dồn số lượng nhập vào số lượng tồn hiện tại
            kho.so_luong_ton += self.so_luong_nhap
            
            # Lưu lại dữ liệu Kho đã được cập nhật
            kho.save()

# 7. Bảng Đơn Hàng (Order)
class DonHang(models.Model):
    khach_hang = models.ForeignKey(KhachHang, on_delete=models.CASCADE)
    ngay_dat_hang = models.DateTimeField(auto_now_add=True)
    tong_tien = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    trang_thai = models.CharField(max_length=50, default="Chờ xử lý")
    nhan_vien_tao = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='don_hang_tao')
    ghi_chu = models.TextField(blank=True, null=True)
    
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
    
    # Bảng lưu thông tin chung của 1 lần nhập hàng
class PhieuNhap(models.Model):
    ngay_nhap = models.DateTimeField(auto_now_add=True)
    nguoi_nhap = models.ForeignKey(User, on_delete=models.SET_NULL, null=True) # Ai là người thao tác
    ghi_chu = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Phiếu nhập #{self.id} - {self.ngay_nhap.strftime('%d/%m/%Y')}"

# Bảng lưu chi tiết từng sản phẩm trong phiếu nhập đó
class ChiTietPhieuNhap(models.Model):
    phieu_nhap = models.ForeignKey(PhieuNhap, on_delete=models.CASCADE, related_name='chi_tiet')
    san_pham = models.ForeignKey(SanPham, on_delete=models.CASCADE)
    so_luong_nhap = models.IntegerField(default=0)


class GioHang(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    san_pham = models.ForeignKey(SanPham, on_delete=models.CASCADE)
    so_luong = models.IntegerField(default=1)

    # Hàm tự động tính thành tiền cho từng món
    @property
    def thanh_tien(self):
        return self.so_luong * self.san_pham.gia_ban

    def __str__(self):
        return f"{self.user.username} - {self.san_pham.ten_san_pham}"