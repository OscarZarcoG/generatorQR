from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router para la API REST
router = DefaultRouter()
router.register(r'qr', views.QRCodeViewSet)

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    
    # Vista de redirección del QR (la URL que estará en el código QR)
    path('qr/<uuid:qr_id>/', views.qr_redirect_view, name='qr_redirect'),
    
    # Vistas web
    path('', views.home_view, name='home'),
    path('generator/', views.qr_generator_view, name='qr_generator'),
    
    # Vista para preview de QR
    path('api/qr-preview/', views.QRPreviewView.as_view(), name='qr_preview'),
]