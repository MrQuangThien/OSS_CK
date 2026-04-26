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