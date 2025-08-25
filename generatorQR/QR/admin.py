from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import QRCode, QRScan

@admin.register(QRCode)
class QRCodeAdmin(admin.ModelAdmin):
    list_display = [
        'client_name', 'group_name', 'whatsapp_number', 
        'scan_count', 'is_active', 'created_at', 'qr_actions'
    ]
    list_filter = ['is_active', 'created_at', 'updated_at']
    search_fields = ['client_name', 'group_name', 'whatsapp_number']
    readonly_fields = ['id', 'created_at', 'updated_at', 'scan_count', 'qr_preview']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('id', 'client_name', 'group_name', 'description')
        }),
        ('WhatsApp', {
            'fields': ('whatsapp_number', 'whatsapp_message')
        }),
        ('Estado y Estadísticas', {
            'fields': ('is_active', 'scan_count', 'created_at', 'updated_at')
        }),
        ('Vista Previa', {
            'fields': ('qr_preview',),
            'classes': ('collapse',)
        })
    )
    
    def qr_actions(self, obj):
        """Botones de acción para cada QR"""
        view_url = f'/api/qr/{obj.id}/image/'
        download_url = f'/api/qr/{obj.id}/download/'
        redirect_url = f'/qr/{obj.id}/'
        
        return format_html(
            '<a href="{}" target="_blank" class="button">Ver QR</a> '
            '<a href="{}" target="_blank" class="button">Descargar</a> '
            '<a href="{}" target="_blank" class="button">Probar</a>',
            view_url, download_url, redirect_url
        )
    qr_actions.short_description = 'Acciones'
    
    def qr_preview(self, obj):
        """Mostrar preview del QR en el admin"""
        if obj.pk:
            image_url = f'/api/qr/{obj.id}/image/'
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px;" />',
                image_url
            )
        return "Guarda el objeto para ver el QR"
    qr_preview.short_description = 'Vista Previa del QR'
    
    def get_queryset(self, request):
        """Optimizar consultas"""
        return super().get_queryset(request).select_related()

@admin.register(QRScan)
class QRScanAdmin(admin.ModelAdmin):
    list_display = [
        'qr_code', 'scanned_at', 'ip_address', 'user_agent_short'
    ]
    list_filter = ['scanned_at', 'qr_code__client_name']
    search_fields = ['qr_code__client_name', 'qr_code__group_name', 'ip_address']
    readonly_fields = ['qr_code', 'scanned_at', 'ip_address', 'user_agent']
    ordering = ['-scanned_at']
    
    def user_agent_short(self, obj):
        """Mostrar versión corta del user agent"""
        if obj.user_agent:
            return obj.user_agent[:50] + '...' if len(obj.user_agent) > 50 else obj.user_agent
        return '-'
    user_agent_short.short_description = 'Navegador'
    
    def has_add_permission(self, request):
        """No permitir agregar escaneos manualmente"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """No permitir editar escaneos"""
        return False

# Personalizar el admin site
admin.site.site_header = "Generador de QR - Administración"
admin.site.site_title = "QR Admin"
admin.site.index_title = "Panel de Administración"
