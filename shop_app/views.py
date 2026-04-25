from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User # Đây chính là dòng bị thiếu
from django.contrib import messages
from django.core.mail import send_mail
from .models import SanPham, LoaiHang, KhoHang, KhachHang, DonHang, ChiTietDonHang, PhieuNhap, ChiTietPhieuNhap
import os
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from django.shortcuts import get_object_or_404
from .forms import SanPhamForm, LoaiHangForm, KhoHangForm

def trang_chu(request):
    # Lấy TẤT CẢ loại hàng ra để đưa vào Menu bên trái
    danh_sach_loai = LoaiHang.objects.all()
    
    # BẮT TỪ KHÓA TÌM KIẾM
    tu_khoa = request.GET.get('keyword')
    
    if tu_khoa:
        # Nếu khách có gõ tìm kiếm -> Tìm tất cả sản phẩm chứa từ khóa đó
        danh_sach_sp = SanPham.objects.filter(ten_san_pham__icontains=tu_khoa)
    else:
        # Nếu không tìm kiếm -> Hiển thị 8 sản phẩm mới nhất mặc định
        danh_sach_sp = SanPham.objects.filter(la_san_pham_moi=True)[:8]
    
    context = {
        'list_loai_hang': danh_sach_loai,
        'list_san_pham': danh_sach_sp, # Dùng chung biến này cho cả tìm kiếm và mặc định
        'tu_khoa': tu_khoa,
    }
    return render(request, 'shop_app/home.html', context)


def chi_tiet_sp(request, sp_id): # Nhận thêm biến sp_id từ URL
    # 1. Tìm sản phẩm theo ID, nếu không thấy sẽ báo lỗi 404
    san_pham = get_object_or_404(SanPham, id=sp_id)
    
    # 2. Kiểm tra xem sản phẩm này đã được nhập kho chưa
    try:
        kho = KhoHang.objects.get(san_pham=san_pham)
        ton_kho = kho.so_luong_ton
    except KhoHang.DoesNotExist:
        ton_kho = 0 # Nếu chưa ai tạo dữ liệu kho cho SP này thì mặc định là 0
        
    # 3. Gửi dữ liệu sang HTML
    context = {
        'sp': san_pham,
        'ton_kho': ton_kho,
    }
    return render(request, 'shop_app/detail.html', context)

from django.contrib.auth import authenticate, login, logout

from django.contrib.auth import authenticate, login, logout

def dang_nhap(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        
        user = authenticate(username=u, password=p)
        
        if user is not None:
            # Vẫn giữ lệnh get_or_create để Admin đăng nhập không bị lỗi văng code
            KhachHang.objects.get_or_create(user=user)
            
            # Đăng nhập trực tiếp, bỏ qua mọi bước check OTP
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Sai tài khoản hoặc mật khẩu!")
            
    return render(request, 'shop_app/login.html')


def dang_xuat(request):
    logout(request)
    return redirect('home')


def dang_ky(request):
    if request.method == 'POST':
        ten_dang_nhap = request.POST.get('username')
        email = request.POST.get('email')
        mat_khau = request.POST.get('password')
        xac_nhan_mat_khau = request.POST.get('confirm_password')

        if mat_khau != xac_nhan_mat_khau:
            messages.error(request, "Mật khẩu xác nhận không khớp!")
            return redirect('register')
            
        if User.objects.filter(username=ten_dang_nhap).exists():
            messages.error(request, "Tên đăng nhập đã tồn tại!")
            return redirect('register')

        # 1. Tạo tài khoản User mặc định của Django
        user = User.objects.create_user(username=ten_dang_nhap, email=email, password=mat_khau)
        
        # 2. Tạo hồ sơ Khách hàng đi kèm
        KhachHang.objects.create(user=user)

        # 3. Báo thành công và chuyển thẳng về trang Đăng nhập
        messages.success(request, "Đăng ký thành công! Vui lòng đăng nhập để mua sắm.")
        return redirect('login')

    return render(request, 'shop_app/register.html')

# Bắt buộc phải đăng nhập mới được chạy hàm này
@login_required(login_url='login')
def them_vao_gio(request, sp_id):
    if request.method == 'POST':
        # 1. Lấy thông tin sản phẩm và khách hàng đang đăng nhập
        san_pham = get_object_or_404(SanPham, id=sp_id)
        khach_hang, created = KhachHang.objects.get_or_create(user=request.user)
        so_luong_them = int(request.POST.get('so_luong', 1))

        # 2. Tìm xem khách này đã có "Giỏ hàng" chưa, nếu chưa thì hệ thống tự tạo mới
        don_hang, created = DonHang.objects.get_or_create(
            khach_hang=khach_hang,
            trang_thai="Giỏ hàng",
            defaults={'tong_tien': 0}
        )

        # 3. Kiểm tra xem sản phẩm này đã có trong giỏ chưa
        chi_tiet, item_created = ChiTietDonHang.objects.get_or_create(
            don_hang=don_hang,
            san_pham=san_pham,
            defaults={'so_luong_mua': so_luong_them, 'don_gia': san_pham.gia_ban}
        )

        # 4. Nếu trong giỏ đã có SP này rồi, thì cộng dồn số lượng lên
        if not item_created:
            chi_tiet.so_luong_mua += so_luong_them
            chi_tiet.save()

        # 5. Thông báo thành công
        messages.success(request, f"Đã thêm {san_pham.ten_san_pham} vào giỏ hàng!")
        return redirect('detail', sp_id=sp_id)
        
    return redirect('home')

@login_required(login_url='login')
def xem_gio_hang(request):
    try:
        khach_hang = KhachHang.objects.get(user=request.user)
        # Tìm đơn hàng đang có trạng thái là "Giỏ hàng"
        don_hang = DonHang.objects.get(khach_hang=khach_hang, trang_thai="Giỏ hàng")
        # Lấy tất cả các món đồ nằm trong giỏ hàng đó
        chi_tiet_list = ChiTietDonHang.objects.filter(don_hang=don_hang)
        
        # Tính toán tổng tiền của cả giỏ hàng
        tong_tien = sum(item.don_gia * item.so_luong_mua for item in chi_tiet_list)
        
        # Cập nhật tổng tiền vào Database cho chắc chắn
        don_hang.tong_tien = tong_tien
        don_hang.save()
        
    except (KhachHang.DoesNotExist, DonHang.DoesNotExist):
        # Nếu khách chưa có giỏ hàng nào thì trả về danh sách rỗng
        chi_tiet_list = []
        tong_tien = 0

    context = {
        'chi_tiet_list': chi_tiet_list,
        'tong_tien': tong_tien,
    }
    return render(request, 'shop_app/cart.html', context)

@login_required(login_url='login')
def thanh_toan(request):
    if request.method == 'POST':
        khach_hang = KhachHang.objects.get(user=request.user)
        try:
            # 1. Lấy giỏ hàng hiện tại
            don_hang = DonHang.objects.get(khach_hang=khach_hang, trang_thai="Giỏ hàng")
            chi_tiet_list = ChiTietDonHang.objects.filter(don_hang=don_hang)
            
            if not chi_tiet_list:
                messages.error(request, "Giỏ hàng đang trống!")
                return redirect('cart')

            # 2. Trừ số lượng trong Kho Hàng
            for item in chi_tiet_list:
                kho = KhoHang.objects.get(san_pham=item.san_pham)
                kho.so_luong_ton -= item.so_luong_mua
                kho.save()

            # 3. Chốt đơn: Đổi trạng thái và cập nhật ngày đặt
            don_hang.trang_thai = "Chờ xác nhận"
            don_hang.save()

            messages.success(request, "🎉 Đặt hàng thành công! Mã đơn hàng của bạn là #" + str(don_hang.id))
            return redirect('history') # Chuyển sang trang Lịch sử
            
        except DonHang.DoesNotExist:
            messages.error(request, "Không tìm thấy giỏ hàng để thanh toán.")
            return redirect('cart')
            
    return redirect('cart')

@login_required(login_url='login')
def lich_su_don_hang(request):
    khach_hang, created = KhachHang.objects.get_or_create(user=request.user)
    
    # Lấy các đơn đã đặt (Khác trạng thái 'Giỏ hàng'), sắp xếp đơn mới nhất lên đầu (-ngay_dat)
    danh_sach_don = DonHang.objects.filter(khach_hang=khach_hang).exclude(trang_thai="Giỏ hàng").order_by('-ngay_dat_hang')
    
    return render(request, 'shop_app/history.html', {'danh_sach_don': danh_sach_don})