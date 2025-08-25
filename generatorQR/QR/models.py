from django.db import models
from django.urls import reverse
import uuid

class QRCode(models.Model):
    # Identificador único para el QR
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Información del cliente/grupo
    client_name = models.CharField(max_length=200, verbose_name="Nombre del Cliente")
    group_name = models.CharField(max_length=200, verbose_name="Nombre del Grupo")
    
    # Información de WhatsApp
    whatsapp_number = models.CharField(max_length=20, verbose_name="Número de WhatsApp")
    whatsapp_message = models.TextField(
        verbose_name="Mensaje de WhatsApp",
        help_text="Mensaje que se enviará automáticamente al escanear el QR"
    )
    
    # Información adicional
    description = models.TextField(blank=True, null=True, verbose_name="Descripción")
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    
    # Estadísticas
    scan_count = models.PositiveIntegerField(default=0, verbose_name="Número de Escaneos")
    
    class Meta:
        verbose_name = "Código QR"
        verbose_name_plural = "Códigos QR"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.client_name} - {self.group_name}"
    
    def get_whatsapp_url(self):
        """Genera la URL de WhatsApp con el mensaje predeterminado"""
        # Limpiar el número de WhatsApp (remover espacios, guiones, etc.)
        clean_number = ''.join(filter(str.isdigit, self.whatsapp_number))
        
        # Asegurar que el número tenga el código de país (México +52)
        if not clean_number.startswith('52') and len(clean_number) == 10:
            clean_number = '52' + clean_number
        
        # Codificar el mensaje para URL
        import urllib.parse
        encoded_message = urllib.parse.quote(self.whatsapp_message)
        
        return f"https://wa.me/{clean_number}?text={encoded_message}"
    
    def get_redirect_url(self):
        """Obtiene la URL de redirección para este QR"""
        return reverse('qr_redirect', kwargs={'qr_id': str(self.id)})
    
    def increment_scan_count(self):
        """Incrementa el contador de escaneos"""
        self.scan_count += 1
        self.save(update_fields=['scan_count'])

class QRScan(models.Model):
    """Modelo para registrar cada escaneo del QR"""
    qr_code = models.ForeignKey(QRCode, on_delete=models.CASCADE, related_name='scans')
    scanned_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Escaneo de QR"
        verbose_name_plural = "Escaneos de QR"
        ordering = ['-scanned_at']
    
    def __str__(self):
        return f"Escaneo de {self.qr_code} - {self.scanned_at}"
