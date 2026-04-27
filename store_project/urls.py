"""
URL configuration for store_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from shop_app import views # Kéo file views.py vừa viết vào đây
from django.conf import settings # Dòng import settings bị thiếu
from django.conf.urls.static import static # Dòng import cấu hình static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.trang_chu, name='home'), # Đường dẫn rỗng (Trang chủ) sẽ gọi hàm trang_chu

    path('chi-tiet/<int:sp_id>/', views.chi_tiet_sp, name='detail'),
    path('dang-nhap/', views.dang_nhap, name='login'),
    path('dang-ky/', views.dang_ky, name='register'),

    path('dang-xuat/', views.dang_xuat, name='logout'),

    path('them-vao-gio/<int:sp_id>/', views.them_vao_gio, name='add_to_cart'),
    path('gio-hang/', views.xem_gio_hang, name='cart'),
    path('thanh-toan/', views.thanh_toan, name='checkout'),
    path('lich-su/', views.lich_su_don_hang, name='history'),
    # URL DÀNH CHO ADMIN
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/kho-hang/', views.admin_kho_hang, name='admin_inventory'),
    path('admin-panel/kho-hang/cap-nhat/<int:kho_id>/', views.admin_cap_nhat_kho, name='admin_update_inventory'),
    path('admin-panel/kho-hang/nhap-loat/', views.admin_nhap_hang_loat, name='admin_import_bulk'),
    path('admin-panel/kho-hang/lich-su/', views.admin_lich_su_nhap, name='admin_import_history'),

    path('admin-panel/loai-hang/', views.admin_loai_hang, name='admin_categories'),
    path('admin-panel/loai-hang/them/', views.admin_them_loai, name='admin_add_category'),
    path('admin-panel/loai-hang/xoa/<int:loai_id>/', views.admin_xoa_loai, name='admin_delete_category'),

    
path('admin-panel/don-hang/', views.admin_quan_ly_don_hang, name='admin_orders'),
path('admin-panel/don-hang/<int:don_id>/', views.admin_chi_tiet_don_hang, name='admin_order_detail'),
path('admin-panel/san-pham/', views.admin_san_pham, name='admin_products'),
path('admin-panel/san-pham/them/', views.admin_them_san_pham, name='admin_add_product'),
path('admin-panel/san-pham/sua/<int:sp_id>/', views.admin_sua_san_pham, name='admin_edit_product'),
path('admin-panel/san-pham/xoa/<int:sp_id>/', views.admin_xoa_san_pham, name='admin_delete_product'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)