from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User # Đây chính là dòng bị thiếu
from django.contrib import messages
from django.core.mail import send_mail
from .models import SanPham, LoaiHang, KhoHang, KhachHang, DonHang, ChiTietDonHang, PhieuNhap, ChiTietPhieuNhap
import os
from django.db.models import Sum
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from django.shortcuts import get_object_or_404
# from .forms import SanPhamForm, LoaiHangForm, KhoHangForm

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

@staff_member_required(login_url='login')
def admin_dashboard(request):
    # 1. THỐNG KÊ 4 THẺ (CARDS) TRÊN CÙNG
    # Tính tổng doanh thu (Chỉ cộng tiền các đơn đã 'Hoàn thành')
    doanh_thu_qs = DonHang.objects.filter(trang_thai='Hoàn thành').aggregate(Sum('tong_tien'))
    tong_doanh_thu = doanh_thu_qs['tong_tien__sum'] or 0
    
    # Đếm tổng số đơn hàng
    tong_don_hang = DonHang.objects.exclude(trang_thai='Giỏ hàng').count()
    
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
    don_hang_moi = DonHang.objects.exclude(trang_thai='Giỏ hàng').order_by('-ngay_dat_hang')[:5]

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
    
@staff_member_required(login_url='login')
def admin_kho_hang(request):
    # Lấy toàn bộ kho hàng, dùng select_related để truy vấn nhanh tên sản phẩm
    list_kho = KhoHang.objects.select_related('san_pham').all().order_by('so_luong_ton')
    
    return render(request, 'shop_app/admin_panel/inventory_list.html', {'list_kho': list_kho})

# CẬP NHẬT SỐ LƯỢNG ĐƠN LẺ (CÓ TỰ ĐỘNG LƯU LỊCH SỬ)
@staff_member_required(login_url='login')
def admin_cap_nhat_kho(request, kho_id):
    kho = get_object_or_404(KhoHang, id=kho_id)
    # 1. Lưu lại số lượng cũ trước khi thay đổi để tính chênh lệch
    so_luong_cu = kho.so_luong_ton 

    if request.method == 'POST':
        form = KhoHangForm(request.POST, instance=kho)
        if form.is_valid():
            # 2. Lưu số lượng mới vào Database
            kho_updated = form.save()
            
            # 3. Tính toán xem là Nhập thêm hay Xuất đi
            chenh_lech = kho_updated.so_luong_ton - so_luong_cu
            
            # 4. Nếu có sự thay đổi về số lượng -> Tự động tạo Phiếu ghi nhận lịch sử
            if chenh_lech != 0:
                hanh_dong = "Nhập thêm" if chenh_lech > 0 else "Xuất giảm/Hao hụt"
                phieu = PhieuNhap.objects.create(
                    nguoi_nhap=request.user, 
                    ghi_chu=f"Hệ thống tự động: {hanh_dong} {abs(chenh_lech)} chiếc"
                )
                ChiTietPhieuNhap.objects.create(
                    phieu_nhap=phieu, 
                    san_pham=kho.san_pham, 
                    so_luong_nhap=chenh_lech # Lưu số âm nếu là xuất kho
                )

            messages.success(request, f"📦 Đã điều chỉnh tồn kho cho '{kho.san_pham.ten_san_pham}' thành công!")
            return redirect('admin_inventory')
    else:
        form = KhoHangForm(instance=kho)
        
    context = {'form': form, 'kho': kho, 'title': 'Cập Nhật Kho Hàng'}
    return render(request, 'shop_app/admin_panel/inventory_form.html', context)

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

from django.contrib.admin.views.decorators import staff_member_required

# Chỉ tài khoản có cờ "is_staff=True" (tài khoản Admin/Nhân viên) mới vào được
@staff_member_required(login_url='login')
def admin_quan_ly_don_hang(request):
    # Lấy tất cả đơn hàng trừ những đơn đang là "Giỏ hàng" (chưa thanh toán)
    # Sắp xếp đơn mới nhất (id giảm dần) lên đầu
    danh_sach_don = DonHang.objects.exclude(trang_thai="Giỏ hàng").order_by('-id')
    
    context = {
        'danh_sach_don': danh_sach_don
    }
    return render(request, 'shop_app/admin_panel/order_list.html', context)

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
        # Chú ý có request.FILES vì form có upload ảnh
        form = SanPhamForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
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
            messages.success(request, "✅ Đã cập nhật sản phẩm thành công!")
            return redirect('admin_products')
    else:
        # Load dữ liệu cũ của sản phẩm vào form
        form = SanPhamForm(instance=sp)
        
    return render(request, 'shop_app/admin_panel/product_form.html', {'form': form, 'title': 'Cập Nhật Sản Phẩm'})

@staff_member_required(login_url='login')
def admin_xoa_san_pham(request, sp_id):
    sp = get_object_or_404(SanPham, id=sp_id)
    ten_sp = sp.ten_san_pham
    sp.delete()
    messages.success(request, f"🗑️ Đã xóa sản phẩm '{ten_sp}' khỏi hệ thống!")
    return redirect('admin_products')