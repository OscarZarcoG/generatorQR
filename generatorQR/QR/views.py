from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
import qrcode
import io
import base64
from PIL import Image
from .models import QRCode, QRScan
from .serializers import (
    QRCodeSerializer, QRCodeCreateSerializer, 
    QRScanSerializer, QRCodeStatsSerializer
)

class QRCodeViewSet(viewsets.ModelViewSet):
    """ViewSet para manejar códigos QR"""
    queryset = QRCode.objects.all()
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return QRCodeCreateSerializer
        elif self.action == 'stats':
            return QRCodeStatsSerializer
        return QRCodeSerializer
    
    def create(self, request, *args, **kwargs):
        """Crear un nuevo código QR"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Crear el código QR
        qr_code = serializer.save()
        
        # Retornar la información completa del QR creado
        response_serializer = QRCodeSerializer(qr_code, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def image(self, request, pk=None):
        """Generar y retornar la imagen del código QR"""
        qr_code = self.get_object()
        
        # Generar la URL de redirección
        redirect_url = request.build_absolute_uri(f'/qr/{qr_code.id}/')
        
        # Crear el código QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(redirect_url)
        qr.make(fit=True)
        
        # Crear la imagen
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir a bytes
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Retornar la imagen
        response = HttpResponse(img_buffer.getvalue(), content_type='image/png')
        response['Content-Disposition'] = f'inline; filename="qr_{qr_code.client_name}_{qr_code.group_name}.png"'
        return response
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Descargar la imagen del código QR"""
        qr_code = self.get_object()
        
        # Generar la URL de redirección
        redirect_url = request.build_absolute_uri(f'/qr/{qr_code.id}/')
        
        # Crear el código QR con mayor calidad para descarga
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=15,
            border=4,
        )
        qr.add_data(redirect_url)
        qr.make(fit=True)
        
        # Crear la imagen
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir a bytes
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Retornar como descarga
        response = HttpResponse(img_buffer.getvalue(), content_type='image/png')
        filename = f"QR_{qr_code.client_name}_{qr_code.group_name}.png".replace(' ', '_')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Obtener estadísticas del código QR"""
        qr_code = self.get_object()
        serializer = QRCodeStatsSerializer(qr_code)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Listar solo códigos QR activos"""
        active_qrs = self.queryset.filter(is_active=True)
        serializer = self.get_serializer(active_qrs, many=True)
        return Response(serializer.data)

def qr_redirect_view(request, qr_id):
    """Vista para redirigir al WhatsApp cuando se escanea el QR"""
    try:
        qr_code = get_object_or_404(QRCode, id=qr_id, is_active=True)
        
        # Registrar el escaneo
        QRScan.objects.create(
            qr_code=qr_code,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Incrementar contador
        qr_code.increment_scan_count()
        
        # Redirigir a WhatsApp
        whatsapp_url = qr_code.get_whatsapp_url()
        return redirect(whatsapp_url)
        
    except QRCode.DoesNotExist:
        return render(request, 'qr_error.html', {
            'error': 'Código QR no encontrado o inactivo'
        })

def get_client_ip(request):
    """Obtener la IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def home_view(request):
    """Vista principal con interfaz web"""
    return render(request, 'home.html')

def qr_generator_view(request):
    """Vista del generador de QR"""
    return render(request, 'qr_generator.html')

@method_decorator(csrf_exempt, name='dispatch')
class QRPreviewView(View):
    """Vista para previsualizar QR sin guardarlo"""
    
    def post(self, request):
        import json
        
        try:
            data = json.loads(request.body)
            
            # Validar datos requeridos
            required_fields = ['client_name', 'group_name', 'whatsapp_number', 'whatsapp_message']
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({'error': f'Campo {field} es requerido'}, status=400)
            
            # Crear URL temporal para el preview
            preview_url = f"https://wa.me/{data['whatsapp_number']}?text={data['whatsapp_message']}"
            
            # Generar QR temporal
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=8,
                border=4,
            )
            qr.add_data(preview_url)
            qr.make(fit=True)
            
            # Crear imagen
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convertir a base64
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            
            return JsonResponse({
                'success': True,
                'qr_image': f'data:image/png;base64,{img_base64}',
                'preview_url': preview_url
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
