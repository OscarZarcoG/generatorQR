from rest_framework import serializers
from .models import QRCode, QRScan

class QRCodeSerializer(serializers.ModelSerializer):
    whatsapp_url = serializers.ReadOnlyField(source='get_whatsapp_url')
    redirect_url = serializers.ReadOnlyField(source='get_redirect_url')
    qr_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = QRCode
        fields = [
            'id', 'client_name', 'group_name', 'whatsapp_number', 
            'whatsapp_message', 'description', 'created_at', 'updated_at', 
            'is_active', 'scan_count', 'whatsapp_url', 'redirect_url', 'qr_image_url'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'scan_count']
    
    def get_qr_image_url(self, obj):
        """Genera la URL para obtener la imagen del QR"""
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/api/qr/{obj.id}/image/')
        return f'/api/qr/{obj.id}/image/'
    
    def validate_whatsapp_number(self, value):
        """Valida el formato del número de WhatsApp"""
        # Remover espacios, guiones y otros caracteres
        clean_number = ''.join(filter(str.isdigit, value))
        
        # Validar longitud (10 dígitos para México o 12 con código de país)
        if len(clean_number) not in [10, 12]:
            raise serializers.ValidationError(
                "El número debe tener 10 dígitos (sin código de país) o 12 dígitos (con código de país +52)"
            )
        
        return value

class QRCodeCreateSerializer(serializers.ModelSerializer):
    """Serializer específico para crear códigos QR con validaciones adicionales"""
    
    class Meta:
        model = QRCode
        fields = [
            'client_name', 'group_name', 'whatsapp_number', 
            'whatsapp_message', 'description'
        ]
    
    def validate_whatsapp_message(self, value):
        """Valida que el mensaje no esté vacío"""
        if not value.strip():
            raise serializers.ValidationError("El mensaje de WhatsApp no puede estar vacío")
        return value
    
    def validate_whatsapp_number(self, value):
        """Valida el formato del número de WhatsApp"""
        clean_number = ''.join(filter(str.isdigit, value))
        
        if len(clean_number) not in [10, 12]:
            raise serializers.ValidationError(
                "El número debe tener 10 dígitos (sin código de país) o 12 dígitos (con código de país +52)"
            )
        
        return value

class QRScanSerializer(serializers.ModelSerializer):
    """Serializer para los escaneos de QR"""
    
    class Meta:
        model = QRScan
        fields = ['id', 'qr_code', 'scanned_at', 'ip_address', 'user_agent']
        read_only_fields = ['id', 'scanned_at']

class QRCodeStatsSerializer(serializers.ModelSerializer):
    """Serializer para estadísticas de códigos QR"""
    total_scans = serializers.IntegerField(source='scan_count')
    recent_scans = serializers.SerializerMethodField()
    
    class Meta:
        model = QRCode
        fields = [
            'id', 'client_name', 'group_name', 'created_at', 
            'total_scans', 'recent_scans', 'is_active'
        ]
    
    def get_recent_scans(self, obj):
        """Obtiene los escaneos recientes (últimos 7 días)"""
        from django.utils import timezone
        from datetime import timedelta
        
        seven_days_ago = timezone.now() - timedelta(days=7)
        return obj.scans.filter(scanned_at__gte=seven_days_ago).count()