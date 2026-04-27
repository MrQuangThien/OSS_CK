from django import forms
from .models import SanPham, LoaiHang, KhoHang
class KhoHangForm(forms.ModelForm):
    class Meta:
        model = KhoHang
        fields = ['so_luong_ton'] # Chỉ cho phép sửa số lượng
        labels = {'so_luong_ton': 'Số lượng tồn kho (Chiếc)'}
        widgets = {
            'so_luong_ton': forms.NumberInput(attrs={'class': 'form-control fw-bold', 'min': '0'})
        }
class LoaiHangForm(forms.ModelForm):
    class Meta:
        model = LoaiHang
        fields = ['ten_loai'] # Chỉ có một trường duy nhất là tên loại
        labels = {'ten_loai': 'Tên loại hàng'}
        widgets = {
            'ten_loai': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ví dụ: Laptop Gaming, Phụ kiện...'})
        }
class SanPhamForm(forms.ModelForm):
    class Meta:
        model = SanPham
        fields = '__all__' # Lấy tất cả các cột làm trường nhập liệu
        widgets = {
            'ten_san_pham': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập tên sản phẩm'}),
            'loai_hang': forms.Select(attrs={'class': 'form-select'}),
            'gia_ban': forms.NumberInput(attrs={'class': 'form-control'}),
            'mo_ta': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'hinh_anh': forms.FileInput(attrs={'class': 'form-control'}),
            'la_san_pham_moi': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }