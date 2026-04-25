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
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)