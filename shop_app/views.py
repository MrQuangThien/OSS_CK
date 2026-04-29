from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User # Đây chính là dòng bị thiếu
from django.contrib import messages
from django.core.mail import send_mail
from .models import SanPham, LoaiHang, KhoHang, KhachHang, DonHang, ChiTietDonHang, PhieuNhap, ChiTietPhieuNhap, HinhAnhSanPham, GioHang, NhanVien
import os, json
from django.db import transaction
from django.db.models import Sum, Q
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.urls import reverse 
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from .forms import SanPhamForm, LoaiHangForm, KhoHangForm, KhachHangForm, NhanVienForm

def trang_chu(request):
    danh_sach_loai = LoaiHang.objects.all()
    
    # BẮT 3 LOẠI HÀNH ĐỘNG CỦA KHÁCH HÀNG:
    tu_khoa = request.GET.get('keyword')   # Bấm tìm kiếm
    ma_loai = request.GET.get('maloai')    # Bấm danh mục bên trái
    bo_loc = request.GET.get('filter')     # Bấm nút "Xem tất cả"
    
    context = {'list_loai_hang': danh_sach_loai, 'tu_khoa': tu_khoa}
    
    # ĐIỀU HƯỚNG GIAO DIỆN SANG DẠNG LƯỚI (GRID):
    if tu_khoa:
        context['list_san_pham'] = SanPham.objects.filter(ten_san_pham__icontains=tu_khoa)
        context['tieu_de'] = f'KẾT QUẢ TÌM KIẾM: "{tu_khoa}"'
        
    elif ma_loai:
        context['list_san_pham'] = SanPham.objects.filter(loai_hang_id=ma_loai)
        context['tieu_de'] = 'SẢN PHẨM THEO DANH MỤC'
        
    elif bo_loc == 'new':
        context['list_san_pham'] = SanPham.objects.filter(la_san_pham_moi=True).order_by('-id')
        context['tieu_de'] = 'TẤT CẢ SẢN PHẨM MỚI'
        
    elif bo_loc == 'hot':
        context['list_san_pham'] = SanPham.objects.filter(la_san_pham_noi_bat=True).order_by('-id')
        context['tieu_de'] = 'TẤT CẢ SẢN PHẨM NỔI BẬT'
        
    # ĐIỀU HƯỚNG GIAO DIỆN SANG DẠNG LƯỚT NGANG (CAROUSEL):
    else:
        context['list_sp_moi'] = SanPham.objects.filter(la_san_pham_moi=True).order_by('-id')[:10]
        context['list_sp_noi_bat'] = SanPham.objects.filter(la_san_pham_noi_bat=True).order_by('-id')[:10]

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
        san_pham = get_object_or_404(SanPham, id=sp_id)
        khach_hang, created = KhachHang.objects.get_or_create(user=request.user)
        so_luong_them = int(request.POST.get('so_luong', 1))

        # ==========================================
        # LUỒNG 1: NẾU KHÁCH BẤM "MUA NGAY"
        # ==========================================
        if 'mua_ngay' in request.POST:
            # Xóa rác đơn cũ
            DonHang.objects.filter(khach_hang=khach_hang, trang_thai="Đang mua ngay").delete()
            
            # Tạo đơn tạm
            don_tam = DonHang.objects.create(
                khach_hang=khach_hang,
                trang_thai="Đang mua ngay",
                tong_tien=san_pham.gia_ban * so_luong_them
            )
            ChiTietDonHang.objects.create(
                don_hang=don_tam,
                san_pham=san_pham,
                so_luong_mua=so_luong_them,
                don_gia=san_pham.gia_ban
            )
            
            # CÁCH CHUẨN NHẤT: Truyền trực tiếp ID lên URL để tránh rớt Session
            url_thanh_toan = reverse('checkout') 
            return HttpResponseRedirect(f"{url_thanh_toan}?mua_ngay_id={don_tam.id}")

        # ==========================================
        # LUỒNG 2: NẾU BẤM "THÊM VÀO GIỎ" BÌNH THƯỜNG
        # ==========================================
        don_hang, created = DonHang.objects.get_or_create(
            khach_hang=khach_hang,
            trang_thai="Giỏ hàng",
            defaults={'tong_tien': 0}
        )

        chi_tiet, item_created = ChiTietDonHang.objects.get_or_create(
            don_hang=don_hang,
            san_pham=san_pham,
            defaults={'so_luong_mua': so_luong_them, 'don_gia': san_pham.gia_ban}
        )

        if not item_created:
            chi_tiet.so_luong_mua += so_luong_them
            chi_tiet.save()

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
    # Lấy hoặc tạo khách hàng
    khach_hang, _ = KhachHang.objects.get_or_create(user=request.user)
    
    # 1. BẮT ID: Ưu tiên lấy từ form ẩn (POST) trước, nếu không có thì lấy trên URL (GET)
    mua_ngay_id = request.POST.get('mua_ngay_id') or request.GET.get('mua_ngay_id')
    
    try:
        # 2. XÁC ĐỊNH LUỒNG THANH TOÁN
        if mua_ngay_id:
            # Đang thanh toán "Mua Ngay" (Chỉ 1 món)
            don_hang = DonHang.objects.get(id=mua_ngay_id, trang_thai="Đang mua ngay", khach_hang=khach_hang)
        else:
            # Đang thanh toán "Giỏ hàng" (Nhiều món)
            don_hang = DonHang.objects.get(khach_hang=khach_hang, trang_thai="Giỏ hàng")
            
        chi_tiet_list = ChiTietDonHang.objects.filter(don_hang=don_hang)
        
        if not chi_tiet_list.exists():
            messages.error(request, "Giỏ hàng của bạn đang trống!")
            return redirect('cart')

        # Tính tổng tiền
        tong_tien = sum(item.don_gia * item.so_luong_mua for item in chi_tiet_list)

        # 3. XỬ LÝ KHI KHÁCH BẤM "XÁC NHẬN ĐẶT HÀNG" (POST)
        if request.method == 'POST':
            # CẬP NHẬT THÔNG TIN GIAO HÀNG VÀO DATABASE
            khach_hang.ho_ten = request.POST.get('ho_ten', khach_hang.ho_ten)
            khach_hang.so_dien_thoai = request.POST.get('so_dien_thoai', khach_hang.so_dien_thoai)
            khach_hang.dia_chi = request.POST.get('dia_chi', khach_hang.dia_chi)
            khach_hang.save()

            # TRỪ KHO HÀNG
            for item in chi_tiet_list:
                kho = KhoHang.objects.get(san_pham=item.san_pham)
                kho.so_luong_ton -= item.so_luong_mua
                kho.save()

            # CHỐT ĐƠN
            don_hang.trang_thai = "Chờ xác nhận"
            don_hang.tong_tien = tong_tien
            don_hang.save()

            messages.success(request, f"🎉 Đặt hàng thành công! Mã đơn hàng của bạn là #{don_hang.id}")
            return redirect('history') 
            
        # 4. HIỂN THỊ GIAO DIỆN (GET)
        don_hang.tong_tien = tong_tien
        don_hang.save()
        
        context = {
            'don_hang': don_hang,
            'chi_tiet_list': chi_tiet_list,
            'khach_hang': khach_hang,
            'tong_tien': tong_tien,
            'mua_ngay_id': mua_ngay_id # QUAN TRỌNG: Gửi ID này sang HTML
        }
        return render(request, 'shop_app/checkout.html', context)

    except DonHang.DoesNotExist:
        messages.error(request, "Không tìm thấy dữ liệu để thanh toán.")
        return redirect('cart')

@login_required(login_url='login')
def lich_su_don_hang(request):
    khach_hang = get_object_or_404(KhachHang, user=request.user)
    
    # Sửa '.order_status' thành '.order_by'
    ds_don_hang = DonHang.objects.filter(khach_hang=khach_hang).exclude(trang_thai="Giỏ hàng").order_by('-id')

    context = {
        'ds_don_hang': ds_don_hang,
    }
    return render(request, 'shop_app/history.html', context)

from django.contrib.admin.views.decorators import staff_member_required

# Chỉ tài khoản có cờ "is_staff=True" (tài khoản Admin/Nhân viên) mới vào được
@staff_member_required(login_url='login')
def admin_quan_ly_don_hang(request):
    # 1. Bắt các thông số từ Bộ Lọc gửi lên
    tu_khoa = request.GET.get('keyword', '')
    tu_ngay = request.GET.get('tu_ngay', '')
    den_ngay = request.GET.get('den_ngay', '')
    sap_xep = request.GET.get('sap_xep', 'moi_nhat') # Mặc định là đơn mới nhất

    # ĐÃ SỬA Ở ĐÂY: Loại trừ cả "Giỏ hàng" và "Đang mua ngay"
    danh_sach_don = DonHang.objects.exclude(trang_thai__in=["Giỏ hàng", "Đang mua ngay"])

    # 2. XỬ LÝ LỌC THEO NGÀY
    # Dùng __date__gte (Lớn hơn hoặc bằng ngày bắt đầu)
    if tu_ngay:
        danh_sach_don = danh_sach_don.filter(ngay_dat_hang__date__gte=tu_ngay)
    # Dùng __date__lte (Nhỏ hơn hoặc bằng ngày kết thúc)
    if den_ngay:
        danh_sach_don = danh_sach_don.filter(ngay_dat_hang__date__lte=den_ngay)

    # 3. XỬ LÝ TÌM KIẾM TỪ KHÓA
    if tu_khoa:
        danh_sach_don = danh_sach_don.filter(
            Q(id__icontains=tu_khoa) | 
            Q(khach_hang__ho_ten__icontains=tu_khoa) |
            Q(khach_hang__so_dien_thoai__icontains=tu_khoa) |
            Q(khach_hang__user__username__icontains=tu_khoa)
        )

    # 4. XỬ LÝ SẮP XẾP ĐỂ ƯU TIÊN ĐƠN
    if sap_xep == 'cu_nhat':
        danh_sach_don = danh_sach_don.order_by('id') # Đẩy đơn cũ (ID nhỏ) lên đầu
    else:
        danh_sach_don = danh_sach_don.order_by('-id') # Đẩy đơn mới (ID lớn) lên đầu

    # 5. XỬ LÝ PHÂN TRANG
    paginator = Paginator(danh_sach_don, 10) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'danh_sach_don': page_obj, 
        'tu_khoa': tu_khoa,
        'tu_ngay': tu_ngay,
        'den_ngay': den_ngay,
        'sap_xep': sap_xep,
    }
    return render(request, 'shop_app/admin_panel/order_list.html', context)

# CHỈ DÀNH CHO ADMIN / NHÂN VIÊN
@staff_member_required(login_url='login')
def admin_san_pham(request):
    # Lấy toàn bộ sản phẩm, sắp xếp sản phẩm mới thêm lên đầu tiên
    danh_sach_sp = SanPham.objects.all().order_by('-id')
    
    context = {
        'danh_sach_sp': danh_sach_sp
    }
    return render(request, 'shop_app/admin_panel/product_list.html', context)

@staff_member_required(login_url='login')
def admin_them_san_pham(request):
    if request.method == 'POST':
        form = SanPhamForm(request.POST, request.FILES)
        if form.is_valid():
            # Lưu sản phẩm chính vào biến sp_moi
            sp_moi = form.save()
            
            # XỬ LÝ UPLOAD NHIỀU ẢNH PHỤ
            images = request.FILES.getlist('hinh_anh_phu')
            for img in images:
                HinhAnhSanPham.objects.create(san_pham=sp_moi, hinh_anh=img)
                
            messages.success(request, "🎉 Đã thêm sản phẩm mới thành công!")
            return redirect('admin_products')
    else:
        form = SanPhamForm()
        
    return render(request, 'shop_app/admin_panel/product_form.html', {'form': form, 'title': 'Thêm Sản Phẩm Mới'})

@staff_member_required(login_url='login')
def admin_sua_san_pham(request, sp_id):
    sp = get_object_or_404(SanPham, id=sp_id)
    if request.method == 'POST':
        form = SanPhamForm(request.POST, request.FILES, instance=sp)
        if form.is_valid():
            form.save()
            
            # XỬ LÝ UPLOAD THÊM ẢNH PHỤ VÀO BỘ SƯU TẬP
            images = request.FILES.getlist('hinh_anh_phu')
            for img in images:
                HinhAnhSanPham.objects.create(san_pham=sp, hinh_anh=img)
                
            messages.success(request, "✅ Đã cập nhật sản phẩm thành công!")
            return redirect('admin_products')
    else:
        form = SanPhamForm(instance=sp)
        
    return render(request, 'shop_app/admin_panel/product_form.html', {'form': form, 'title': 'Cập Nhật Sản Phẩm'})

@staff_member_required(login_url='login')
def admin_xoa_san_pham(request, sp_id):
    sp = get_object_or_404(SanPham, id=sp_id)
    ten_sp = sp.ten_san_pham
    sp.delete()
    messages.success(request, f"🗑️ Đã xóa sản phẩm '{ten_sp}' khỏi hệ thống!")
    return redirect('admin_products')

@staff_member_required(login_url='login')
def admin_chi_tiet_don_hang(request, don_id):
    # Lấy thông tin đơn hàng và các sản phẩm bên trong
    don_hang = get_object_or_404(DonHang, id=don_id)
    chi_tiet_list = ChiTietDonHang.objects.filter(don_hang=don_hang)

    # Nếu Admin bấm nút Cập nhật trạng thái
    if request.method == 'POST':
        trang_thai_moi = request.POST.get('trang_thai')
        don_hang.trang_thai = trang_thai_moi
        don_hang.save()
        messages.success(request, f"✅ Đã cập nhật đơn hàng #{don_id} thành '{trang_thai_moi}'!")
        return redirect('admin_order_detail', don_id=don_id)

    context = {
        'don_hang': don_hang,
        'chi_tiet_list': chi_tiet_list,
    }
    return render(request, 'shop_app/admin_panel/order_detail.html', context)

# DANH SÁCH LOẠI HÀNG
@staff_member_required(login_url='login')
def admin_loai_hang(request):
    list_loai = LoaiHang.objects.all().order_by('-id')
    return render(request, 'shop_app/admin_panel/category_list.html', {'list_loai': list_loai})

# THÊM LOẠI HÀNG
@staff_member_required(login_url='login')
def admin_them_loai(request):
    if request.method == 'POST':
        form = LoaiHangForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "🎉 Đã thêm loại hàng mới!")
            return redirect('admin_categories')
    else:
        form = LoaiHangForm()
    return render(request, 'shop_app/admin_panel/category_form.html', {'form': form, 'title': 'Thêm Loại Hàng'})

# XÓA LOẠI HÀNG (Lưu ý: Xóa loại hàng có thể ảnh hưởng đến sản phẩm thuộc loại đó)
@staff_member_required(login_url='login')
def admin_xoa_loai(request, loai_id):
    loai = get_object_or_404(LoaiHang, id=loai_id)
    # Kiểm tra xem có sản phẩm nào đang thuộc loại này không
    if SanPham.objects.filter(loai_hang=loai).exists():
        messages.error(request, f"❌ Không thể xóa! Hiện đang có sản phẩm thuộc loại '{loai.ten_loai}'.")
    else:
        loai.delete()
        messages.success(request, "🗑️ Đã xóa loại hàng thành công.")
    return redirect('admin_categories')

@staff_member_required(login_url='login')
def admin_kho_hang(request):
    # Lấy toàn bộ kho hàng, dùng select_related để truy vấn nhanh tên sản phẩm
    list_kho = KhoHang.objects.select_related('san_pham').all().order_by('so_luong_ton')
    
    return render(request, 'shop_app/admin_panel/inventory_list.html', {'list_kho': list_kho})

# CẬP NHẬT SỐ LƯỢNG ĐƠN LẺ (CÓ TỰ ĐỘNG LƯU LỊCH SỬ)
# CẬP NHẬT SỐ LƯỢNG KHO (CỘNG/TRỪ TRỰC TIẾP)
@staff_member_required(login_url='login')
def admin_cap_nhat_kho(request, kho_id):
    kho = get_object_or_404(KhoHang, id=kho_id)
    
    if request.method == 'POST':
        # Lấy con số nhập/xuất từ form (dùng request.POST.get vì ta viết form HTML tự do)
        thay_doi = int(request.POST.get('so_luong_thay_doi', 0))
        
        if thay_doi != 0:
            # Chặn lỗi nếu nhân viên xuất âm quá số lượng đang có
            if kho.so_luong_ton + thay_doi < 0:
                messages.error(request, f"❌ Lỗi: Bạn muốn xuất {abs(thay_doi)} chiếc nhưng kho chỉ còn {kho.so_luong_ton} chiếc!")
                return redirect('admin_update_inventory', kho_id=kho.id)

            # 1. Cộng/trừ thẳng vào kho
            kho.so_luong_ton += thay_doi
            kho.save()
            
            # 2. Tự động tạo Phiếu nhập lịch sử
            hanh_dong = "Nhập thêm" if thay_doi > 0 else "Xuất giảm"
            phieu = PhieuNhap.objects.create(
                nguoi_nhap=request.user, 
                ghi_chu=f"Điều chỉnh nhanh: {hanh_dong} {abs(thay_doi)} chiếc"
            )
            ChiTietPhieuNhap.objects.create(
                phieu_nhap=phieu, 
                san_pham=kho.san_pham, 
                so_luong_nhap=thay_doi 
            )
            
            messages.success(request, f"📦 Đã {hanh_dong.lower()} {abs(thay_doi)} chiếc cho '{kho.san_pham.ten_san_pham}'!")
        else:
            messages.warning(request, "⚠️ Bạn nhập số 0 nên kho không có sự thay đổi nào.")
            
        return redirect('admin_inventory')

    return render(request, 'shop_app/admin_panel/inventory_form.html', {'kho': kho, 'title': 'Nhập / Xuất Nhanh'})

@staff_member_required(login_url='login')
def admin_nhap_hang_loat(request):
    if request.method == 'POST':
        # Lấy danh sách ID sản phẩm và số lượng tương ứng từ form gửi lên
        san_pham_ids = request.POST.getlist('san_pham_id[]')
        so_luongs = request.POST.getlist('so_luong[]')
        ghi_chu = request.POST.get('ghi_chu', '')

        if san_pham_ids and so_luongs:
            # Tạo 1 Phiếu nhập mới
            phieu = PhieuNhap.objects.create(nguoi_nhap=request.user, ghi_chu=ghi_chu)
            
            # Chạy vòng lặp để ghép cặp (Sản phẩm - Số lượng)
            for sp_id, sl in zip(san_pham_ids, so_luongs):
                if sl and int(sl) > 0:
                    sp = SanPham.objects.get(id=sp_id)
                    # 1. Lưu vào Chi tiết phiếu nhập (Lịch sử)
                    ChiTietPhieuNhap.objects.create(phieu_nhap=phieu, san_pham=sp, so_luong_nhap=int(sl))
                    
                    # 2. Cộng dồn vào Kho hàng hiện tại
                    kho, created = KhoHang.objects.get_or_create(san_pham=sp)
                    kho.so_luong_ton += int(sl)
                    kho.save()
                    
            messages.success(request, f"📦 Đã nhập lô hàng mới (Phiếu #{phieu.id}) thành công!")
            return redirect('admin_import_history') # Nhập xong chuyển qua trang Lịch sử

    # Lấy danh sách sản phẩm để hiển thị trong ô Dropdown
    danh_sach_sp = SanPham.objects.all()
    return render(request, 'shop_app/admin_panel/import_bulk.html', {'danh_sach_sp': danh_sach_sp})


# 2. HÀM HIỂN THỊ LỊCH SỬ NHẬP
@staff_member_required(login_url='login')
def admin_lich_su_nhap(request):
    list_phieu = PhieuNhap.objects.all().order_by('-ngay_nhap')
    return render(request, 'shop_app/admin_panel/import_history.html', {'list_phieu': list_phieu})

@staff_member_required(login_url='login')
def admin_dashboard(request):
    # 1. THỐNG KÊ 4 THẺ (CARDS) TRÊN CÙNG
    # Tính tổng doanh thu (Chỉ cộng tiền các đơn đã 'Hoàn thành')
    doanh_thu_qs = DonHang.objects.filter(trang_thai='Hoàn thành').aggregate(Sum('tong_tien'))
    tong_doanh_thu = doanh_thu_qs['tong_tien__sum'] or 0
    
    # Đếm tổng số đơn hàng
    tong_don_hang = DonHang.objects.exclude(trang_thai__in=['Giỏ hàng', 'Đang mua ngay']).count()
    
    # Đếm tổng khách hàng
    tong_khach_hang = KhachHang.objects.count()
    
    # Đếm số lượng sản phẩm sắp hết hàng (Tồn kho < 5)
    sp_sap_het = KhoHang.objects.filter(so_luong_ton__lt=5).count()

    # 2. DỮ LIỆU CHO BIỂU ĐỒ (Tỉ lệ trạng thái đơn hàng)
    don_cho_xac_nhan = DonHang.objects.filter(trang_thai='Chờ xác nhận').count()
    don_dang_giao = DonHang.objects.filter(trang_thai='Đang giao hàng').count()
    don_hoan_thanh = DonHang.objects.filter(trang_thai='Hoàn thành').count()
    don_da_huy = DonHang.objects.filter(trang_thai='Đã hủy').count()

    # 3. DANH SÁCH 5 ĐƠN HÀNG MỚI NHẤT
    don_hang_moi = DonHang.objects.exclude(trang_thai__in=['Giỏ hàng', 'Đang mua ngay']).order_by('-ngay_dat_hang')[:5]
    context = {
        'tong_doanh_thu': tong_doanh_thu,
        'tong_don_hang': tong_don_hang,
        'tong_khach_hang': tong_khach_hang,
        'sp_sap_het': sp_sap_het,
        # Trả mảng dữ liệu biểu đồ ra HTML
        'chart_data': [don_cho_xac_nhan, don_dang_giao, don_hoan_thanh, don_da_huy],
        'don_hang_moi': don_hang_moi
    }
    return render(request, 'shop_app/admin_panel/dashboard.html', context)

# 1. HÀM CẬP NHẬT SỐ LƯỢNG (DÙNG AJAX)
@login_required(login_url='login')
def update_cart(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        action = request.POST.get('action')
        
        # Lấy sản phẩm trong giỏ
        cart_item = get_object_or_404(ChiTietDonHang, id=item_id, don_hang__khach_hang__user=request.user)
        
        if action == 'add':
            cart_item.so_luong_mua += 1
        elif action == 'remove' and cart_item.so_luong_mua > 1:
            cart_item.so_luong_mua -= 1
            
        cart_item.save()
        
        # Tính toán lại các con số để gửi về giao diện
        don_hang = cart_item.don_hang
        chi_tiet_list = ChiTietDonHang.objects.filter(don_hang=don_hang)
        tong_tien_moi = sum(item.don_gia * item.so_luong_mua for item in chi_tiet_list)
        
        # Lưu tổng tiền mới vào đơn hàng
        don_hang.tong_tien = tong_tien_moi
        don_hang.save()
        
        return JsonResponse({
    'success': True,
    'new_qty': cart_item.so_luong_mua,
    # Định dạng dấu phẩy ở đây
    'item_total': f"{cart_item.don_gia * cart_item.so_luong_mua:,.0f} đ",
    'cart_total': f"{tong_tien_moi:,.0f} đ"
})

# 2. HÀM XÓA SẢN PHẨM KHỎI GIỎ
@login_required(login_url='login')
def xoa_item_gio_hang(request, item_id):
    cart_item = get_object_or_404(ChiTietDonHang, id=item_id, don_hang__khach_hang__user=request.user)
    cart_item.delete()
    messages.success(request, "🗑️ Đã xóa sản phẩm khỏi giỏ hàng.")
    return redirect('cart')

def tat_ca_san_pham(request):
    # 1. Lấy toàn bộ danh mục và sản phẩm mặc định
    danh_sach_loai = LoaiHang.objects.all()
    san_phams = SanPham.objects.all()

    # 2. Bắt các thông số từ Bộ Lọc gửi lên
    ma_loai = request.GET.get('category')
    tu_khoa = request.GET.get('keyword')
    gia_tu = request.GET.get('min_price')
    gia_den = request.GET.get('max_price')
    sap_xep = request.GET.get('sort')

    # 3. THỰC HIỆN LỌC DỮ LIỆU
    if ma_loai:
        san_phams = san_phams.filter(loai_hang_id=ma_loai)
        
    if tu_khoa:
        san_phams = san_phams.filter(ten_san_pham__icontains=tu_khoa)
        
    if gia_tu:
        san_phams = san_phams.filter(gia_ban__gte=gia_tu) # gte = Lớn hơn hoặc bằng
        
    if gia_den:
        san_phams = san_phams.filter(gia_ban__lte=gia_den) # lte = Nhỏ hơn hoặc bằng

    # 4. THỰC HIỆN SẮP XẾP
    if sap_xep == 'price_asc':
        san_phams = san_phams.order_by('gia_ban') # Giá thấp đến cao
    elif sap_xep == 'price_desc':
        san_phams = san_phams.order_by('-gia_ban') # Giá cao xuống thấp
    else:
        san_phams = san_phams.order_by('-id') # Mặc định: Sản phẩm mới nhất

    context = {
        'list_loai_hang': danh_sach_loai,
        'list_san_pham': san_phams,
    }
    return render(request, 'shop_app/all_products.html', context)

@login_required(login_url='login')
def thong_tin_tai_khoan(request):
    # Lấy hồ sơ khách hàng của người đang đăng nhập
    khach_hang, created = KhachHang.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = KhachHangForm(request.POST, instance=khach_hang)
        if form.is_valid():
            form.save()
            messages.success(request, "🎉 Đã cập nhật thông tin cá nhân thành công!")
            return redirect('account')
    else:
        form = KhachHangForm(instance=khach_hang)
    
    return render(request, 'shop_app/account.html', {'form': form})



@login_required(login_url='login')
def chi_tiet_don_hang(request, don_hang_id):
    # Lấy đơn hàng của khách hàng hiện tại
    don_hang = get_object_or_404(DonHang, id=don_hang_id, khach_hang__user=request.user)
    # Lấy danh sách sản phẩm trong đơn đó
    chi_tiet_list = ChiTietDonHang.objects.filter(don_hang=don_hang)
    
    context = {
        'don_hang': don_hang,
        'chi_tiet_list': chi_tiet_list,
    }
    return render(request, 'shop_app/order_detail.html', context)

@staff_member_required(login_url='login')
def admin_tao_don_hang(request):
    if request.method == 'POST':
        try:
            # 1. Nhận dữ liệu từ giao diện POS gửi lên
            data = json.loads(request.body)
            ho_ten = data.get('ho_ten', 'Khách Lẻ')
            sdt = data.get('sdt', '')
            dia_chi = data.get('dia_chi', '') # BỔ SUNG ĐỊA CHỈ
            ghi_chu = data.get('ghi_chu', '')
            items = data.get('items', [])

            if not items:
                return JsonResponse({'success': False, 'message': 'Giỏ hàng đang trống!'})

            with transaction.atomic():
                # 2. Xử lý Khách Hàng
                username_khach = sdt if sdt else f'khachle_{request.user.id}'
                user_khach, _ = User.objects.get_or_create(username=username_khach, defaults={'first_name': ho_ten})
                
                # Cập nhật Khách Hàng kèm Địa Chỉ
                khach_hang, created = KhachHang.objects.get_or_create(user=user_khach)
                khach_hang.ho_ten = ho_ten
                if sdt: khach_hang.so_dien_thoai = sdt
                if dia_chi: khach_hang.dia_chi = dia_chi
                khach_hang.save()

                # 3. Tạo Đơn Hàng
                don_hang = DonHang.objects.create(
                    khach_hang=khach_hang,
                    trang_thai='Hoàn thành', 
                    nhan_vien_tao=request.user,
                    ghi_chu=ghi_chu,
                    tong_tien=0
                )

                # 4. Lưu Chi tiết & Trừ Kho (Giữ nguyên như cũ)
                tong_tien = 0
                for item in items:
                    san_pham = SanPham.objects.get(id=item['id'])
                    so_luong = int(item['qty'])
                    don_gia = san_pham.gia_ban

                    ChiTietDonHang.objects.create(don_hang=don_hang, san_pham=san_pham, so_luong_mua=so_luong, don_gia=don_gia)
                    tong_tien += don_gia * so_luong

                    kho = KhoHang.objects.get(san_pham=san_pham)
                    kho.so_luong_ton -= so_luong
                    kho.save()

                don_hang.tong_tien = tong_tien
                don_hang.save()

            return JsonResponse({'success': True, 'don_hang_id': don_hang.id})

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    # NẾU LÀ GET: Hiển thị giao diện POS kèm danh sách sản phẩm
    danh_sach_sp = SanPham.objects.filter(khohang__so_luong_ton__gt=0).distinct().order_by('-id')
    danh_sach_loai = LoaiHang.objects.all() # 👈 THÊM DÒNG NÀY ĐỂ LẤY DANH MỤC
    
    context = {
        'danh_sach_sp': danh_sach_sp,
        'danh_sach_loai': danh_sach_loai # 👈 TRUYỀN SANG HTML
    }
    return render(request, 'shop_app/admin_panel/pos.html', context)

@staff_member_required(login_url='login')
@staff_member_required(login_url='login')
def admin_employees(request):
    
    # === BẮT ĐẦU ĐOẠN CODE THÊM MỚI TỰ ĐỘNG ĐỒNG BỘ ===
    # Tìm những tài khoản có quyền Staff/Superuser NHƯNG chưa có hồ sơ NhanVien
    admin_users = User.objects.filter(is_staff=True, nhanvien__isnull=True)
    for u in admin_users:
        # Tự động cấp cho họ chức vụ mặc định để hiện lên danh sách
        NhanVien.objects.create(user=u, chuc_vu="Quản trị viên cấp cao")
    # === KẾT THÚC ĐOẠN CODE THÊM MỚI ===

    # Lấy danh sách nhân viên để hiển thị ra HTML (Giữ nguyên như cũ)
    list_nhan_vien = NhanVien.objects.select_related('user').all()
    return render(request, 'shop_app/admin_panel/admin_employee_list.html', {'list_nhan_vien': list_nhan_vien})

# 2. THÊM NHÂN VIÊN MỚI
@staff_member_required(login_url='login')
def admin_employee_add(request):
    form = NhanVienForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        cd = form.cleaned_data
        # Kiểm tra trùng tên đăng nhập
        if User.objects.filter(username=cd['username']).exists():
            messages.error(request, "Tên đăng nhập này đã tồn tại!")
        else:
            # Tạo User mới (Đặt quyền is_staff = True để vào được trang Admin)
            user = User.objects.create_user(
                username=cd['username'],
                password=cd['password'],
                first_name=cd['first_name'],
                email=cd['email'],
                is_staff=True 
            )
            # Liên kết User đó với bảng NhanVien
            NhanVien.objects.create(user=user, chuc_vu=cd['chuc_vu'])
            messages.success(request, "Đã thêm nhân viên mới thành công!")
            return redirect('admin_employees')

    return render(request, 'shop_app/admin_panel/admin_employee_form.html', {'form': form, 'title': 'Thêm Nhân Viên Mới'})

# 3. SỬA THÔNG TIN NHÂN VIÊN
@staff_member_required(login_url='login')
def admin_employee_edit(request, emp_id):
    nhan_vien = get_object_or_404(NhanVien, id=emp_id)
    user = nhan_vien.user

    # Đổ dữ liệu cũ vào Form
    initial_data = {
        'username': user.username,
        'first_name': user.first_name,
        'email': user.email,
        'chuc_vu': nhan_vien.chuc_vu
    }
    
    form = NhanVienForm(request.POST or None, initial=initial_data)
    
    if request.method == 'POST' and form.is_valid():
        cd = form.cleaned_data
        
        # Cập nhật thông tin User
        user.first_name = cd['first_name']
        user.email = cd['email']
        # Đổi mật khẩu nếu có nhập
        if cd['password']:
            user.set_password(cd['password'])
        user.save()

        # Cập nhật Chức vụ
        nhan_vien.chuc_vu = cd['chuc_vu']
        nhan_vien.save()

        messages.success(request, "Đã cập nhật thông tin nhân viên!")
        return redirect('admin_employees')

    return render(request, 'shop_app/admin_panel/admin_employee_form.html', {'form': form, 'title': f'Sửa thông tin: {user.username}'})

# 4. TẠM DỪNG / KHÔI PHỤC HOẠT ĐỘNG
@staff_member_required(login_url='login')
def admin_suspend_employee(request, emp_id):
    nhan_vien = get_object_or_404(NhanVien, id=emp_id)
    user = nhan_vien.user
    
    if user.is_active:
        user.is_active = False # Khóa tài khoản
        messages.warning(request, f"Đã ĐÌNH CHỈ hoạt động của nhân viên {user.first_name}.")
    else:
        user.is_active = True  # Mở khóa
        messages.success(request, f"Đã KHÔI PHỤC hoạt động cho nhân viên {user.first_name}.")
        
    user.save()
    return redirect('admin_employees')

@staff_member_required(login_url='login')
def admin_customers(request):
    # Lấy từ khóa tìm kiếm trên thanh URL (nếu có)
    tu_khoa = request.GET.get('keyword', '')
    
    # Lấy danh sách khách hàng và gộp luôn bảng User để web chạy nhanh hơn
    danh_sach_kh = KhachHang.objects.select_related('user').all().order_by('-user__date_joined')
    
    # Xử lý tìm kiếm thông minh
    if tu_khoa:
        danh_sach_kh = danh_sach_kh.filter(
            Q(ho_ten__icontains=tu_khoa) | 
            Q(so_dien_thoai__icontains=tu_khoa) | 
            Q(user__username__icontains=tu_khoa) |
            Q(user__email__icontains=tu_khoa)
        )
        
    context = {
        'danh_sach_kh': danh_sach_kh,
        'tu_khoa': tu_khoa
    }
    return render(request, 'shop_app/admin_panel/admin_customer_list.html', context)