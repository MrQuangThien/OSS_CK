from django import forms
from django.contrib.auth.models import User
from .models import SanPham, LoaiHang, KhoHang, KhachHang

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

class LoaiHangForm(forms.ModelForm):
    class Meta:
        model = LoaiHang
        fields = ['ma_loai', 'ten_loai'] # Chỉ có một trường duy nhất là tên loại
        labels = {'ma_loai' : 'Mã loại hàng', 'ten_loai': 'Tên loại hàng'}
        widgets = {
            'ten_loai': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ví dụ: Laptop Gaming, Phụ kiện...'})
        }

class KhoHangForm(forms.ModelForm):
    class Meta:
        model = KhoHang
        fields = ['so_luong_ton'] # Chỉ cho phép sửa số lượng
        labels = {'so_luong_ton': 'Số lượng tồn kho (Chiếc)'}
        widgets = {
            'so_luong_ton': forms.NumberInput(attrs={'class': 'form-control fw-bold', 'min': '0'})
        }

class KhachHangForm(forms.ModelForm):
    class Meta:
        model = KhachHang
        fields = ['ho_ten', 'so_dien_thoai', 'dia_chi']
        widgets = {
            'ho_ten': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập họ và tên...'}),
            'so_dien_thoai': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập số điện thoại...'}),
            'dia_chi': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Nhập địa chỉ nhận hàng...', 'rows': 3}),
        }
    
class NhanVienForm(forms.Form):
    username = forms.CharField(label="Tên đăng nhập", max_length=150)
    password = forms.CharField(label="Mật khẩu", required=False, widget=forms.PasswordInput, 
                               help_text="Điền mật khẩu khi tạo mới. Khi sửa, nếu để trống sẽ giữ nguyên mật khẩu cũ.")
    first_name = forms.CharField(label="Họ và Tên", max_length=150)
    email = forms.EmailField(label="Email", required=False)
    chuc_vu = forms.CharField(label="Chức vụ", max_length=100, help_text="Ví dụ: Kế toán, Thủ kho, Chăm sóc khách hàng...")
