from django.contrib import admin
from .models import LoaiHang, SanPham, KhachHang, NhanVien, KhoHang, NhapKho, DonHang, ChiTietDonHang

# Đăng ký các bảng để hệ thống Admin nhận diện
admin.site.register(LoaiHang)
admin.site.register(SanPham)
admin.site.register(KhachHang)
admin.site.register(NhanVien)
admin.site.register(KhoHang)
admin.site.register(NhapKho)
admin.site.register(DonHang)
admin.site.register(ChiTietDonHang)