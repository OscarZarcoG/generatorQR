// Configuración global
const API_BASE_URL = '/api';

// Utilidades
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

// Función para mostrar notificaciones
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
        type === 'success' ? 'bg-green-500' :
        type === 'error' ? 'bg-red-500' :
        type === 'warning' ? 'bg-yellow-500' :
        'bg-blue-500'
    } text-white`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// Función para formatear números de teléfono
function formatPhoneNumber(phone) {
    // Remover todos los caracteres no numéricos excepto el +
    let cleaned = phone.replace(/[^\d+]/g, '');
    
    // Si no empieza con +, agregar +52 para México
    if (!cleaned.startsWith('+')) {
        if (cleaned.length === 10) {
            cleaned = '+52' + cleaned;
        } else if (cleaned.length === 12 && cleaned.startsWith('52')) {
            cleaned = '+' + cleaned;
        } else {
            cleaned = '+' + cleaned;
        }
    }
    
    return cleaned;
}

// Función para validar número de WhatsApp
function validateWhatsAppNumber(phone) {
    const formatted = formatPhoneNumber(phone);
    // Validar que tenga al menos 10 dígitos después del código de país
    return /^\+\d{10,15}$/.test(formatted);
}

// Cargar QRs recientes en la página de inicio
function loadRecentQRs() {
    const container = document.getElementById('recent-qrs');
    if (!container) return;
    
    fetch(`${API_BASE_URL}/qr/`)
        .then(response => response.json())
        .then(data => {
            if (data.results && data.results.length > 0) {
                container.innerHTML = data.results.slice(0, 6).map(qr => `
                    <div class="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
                        <div class="flex items-center justify-between mb-4">
                            <h3 class="font-semibold text-gray-800">${qr.client_name}</h3>
                            <span class="text-xs px-2 py-1 rounded-full ${
                                qr.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                            }">
                                ${qr.is_active ? 'Activo' : 'Inactivo'}
                            </span>
                        </div>
                        <p class="text-sm text-gray-600 mb-2">${qr.group_name}</p>
                        <p class="text-xs text-gray-500 mb-4">${qr.whatsapp_number}</p>
                        <div class="flex items-center justify-between text-xs text-gray-500">
                            <span><i class="fas fa-eye mr-1"></i>${qr.scan_count} escaneos</span>
                            <span>${new Date(qr.created_at).toLocaleDateString()}</span>
                        </div>
                        <div class="mt-4 flex gap-2">
                            <a href="/api/qr/${qr.id}/image/" target="_blank" 
                               class="text-xs bg-secondary text-white px-3 py-1 rounded hover:bg-secondary-light">
                                Ver QR
                            </a>
                            <a href="/api/qr/${qr.id}/download/" 
                               class="text-xs bg-primary text-white px-3 py-1 rounded hover:bg-primary-dark">
                                Descargar
                            </a>
                        </div>
                    </div>
                `).join('');
            } else {
                container.innerHTML = `
                    <div class="col-span-full text-center py-12">
                        <i class="fas fa-qrcode text-4xl text-gray-300 mb-4"></i>
                        <p class="text-gray-500">No hay códigos QR creados aún</p>
                        <a href="/generator/" class="inline-block mt-4 bg-primary text-white px-6 py-2 rounded-lg hover:bg-primary-dark">
                            Crear mi primer QR
                        </a>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error loading recent QRs:', error);
            container.innerHTML = `
                <div class="col-span-full text-center py-12">
                    <p class="text-red-500">Error al cargar los códigos QR</p>
                </div>
            `;
        });
}

// Funcionalidad del generador de QR
function initQRGenerator() {
    const form = document.getElementById('qr-form');
    const previewBtn = document.getElementById('preview-btn');
    const createBtn = document.getElementById('create-btn');
    const previewSection = document.getElementById('qr-preview-section');
    const actionsSection = document.getElementById('qr-actions');
    const phoneInput = document.getElementById('whatsapp_number');
    const messageInput = document.getElementById('whatsapp_message');
    const groupNameInput = document.getElementById('group_name');
    
    if (!form) return;
    
    // Auto-formatear número de teléfono
    if (phoneInput) {
        phoneInput.addEventListener('blur', function() {
            if (this.value) {
                this.value = formatPhoneNumber(this.value);
            }
        });
    }
    
    // Auto-completar mensaje cuando cambie el nombre del grupo
    if (groupNameInput && messageInput) {
        groupNameInput.addEventListener('input', function() {
            if (this.value && !messageInput.value) {
                messageInput.value = `Hola, necesito información sobre el grupo "${this.value}"`;
            }
        });
    }
    
    // Preview del QR
    if (previewBtn) {
        previewBtn.addEventListener('click', function(e) {
            e.preventDefault();
            generatePreview();
        });
    }
    
    // Crear QR
    if (createBtn) {
        createBtn.addEventListener('click', function(e) {
            e.preventDefault();
            createQR();
        });
    }
    
    function generatePreview() {
        const formData = new FormData(form);
        
        // Validar campos requeridos
        if (!formData.get('whatsapp_number') || !formData.get('whatsapp_message')) {
            showNotification('Por favor completa el número de WhatsApp y el mensaje', 'error');
            return;
        }
        
        // Validar número de WhatsApp
        if (!validateWhatsAppNumber(formData.get('whatsapp_number'))) {
            showNotification('Por favor ingresa un número de WhatsApp válido', 'error');
            return;
        }
        
        previewBtn.disabled = true;
        previewBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Generando...';
        
        fetch(`${API_BASE_URL}/qr/preview/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.qr_image_url) {
                document.getElementById('qr-preview-img').src = data.qr_image_url;
                document.getElementById('preview-whatsapp-url').href = data.whatsapp_url;
                previewSection.classList.remove('hidden');
                showNotification('Vista previa generada correctamente', 'success');
            } else {
                throw new Error(data.error || 'Error generando preview');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Error al generar la vista previa: ' + error.message, 'error');
        })
        .finally(() => {
            previewBtn.disabled = false;
            previewBtn.innerHTML = '<i class="fas fa-eye mr-2"></i>Vista Previa';
        });
    }
    
    function createQR() {
        const formData = new FormData(form);
        
        // Validar campos requeridos
        if (!formData.get('client_name') || !formData.get('whatsapp_number') || !formData.get('whatsapp_message')) {
            showNotification('Por favor completa todos los campos requeridos', 'error');
            return;
        }
        
        // Validar número de WhatsApp
        if (!validateWhatsAppNumber(formData.get('whatsapp_number'))) {
            showNotification('Por favor ingresa un número de WhatsApp válido', 'error');
            return;
        }
        
        createBtn.disabled = true;
        createBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Creando...';
        
        fetch(`${API_BASE_URL}/qr/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.id) {
                // Actualizar la vista con el QR creado
                document.getElementById('qr-preview-img').src = data.qr_image_url;
                document.getElementById('final-download-btn').href = `/api/qr/${data.id}/download/`;
                document.getElementById('final-whatsapp-btn').href = data.whatsapp_url;
                document.getElementById('qr-stats').innerHTML = `
                    <p><strong>ID:</strong> ${data.id}</p>
                    <p><strong>Creado:</strong> ${new Date(data.created_at).toLocaleString()}</p>
                    <p><strong>Escaneos:</strong> ${data.scan_count}</p>
                `;
                
                previewSection.classList.remove('hidden');
                actionsSection.classList.remove('hidden');
                
                // Mostrar modal de éxito
                showSuccessModal(data);
                
                showNotification('¡Código QR creado exitosamente!', 'success');
            } else {
                throw new Error(data.error || 'Error creando QR');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Error al crear el código QR: ' + error.message, 'error');
        })
        .finally(() => {
            createBtn.disabled = false;
            createBtn.innerHTML = '<i class="fas fa-plus mr-2"></i>Crear QR';
        });
    }
    
    function showSuccessModal(qrData) {
        const modal = document.getElementById('success-modal');
        if (modal) {
            document.getElementById('modal-qr-id').textContent = qrData.id;
            document.getElementById('modal-client-name').textContent = qrData.client_name;
            document.getElementById('modal-download-btn').href = `/api/qr/${qrData.id}/download/`;
            document.getElementById('modal-whatsapp-btn').href = qrData.whatsapp_url;
            
            modal.classList.remove('hidden');
        }
    }
}

// Cerrar modal
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
    }
}

// Copiar al portapapeles
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Copiado al portapapeles', 'success');
    }).catch(() => {
        showNotification('Error al copiar', 'error');
    });
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Cargar QRs recientes en la página de inicio
    loadRecentQRs();
    
    // Inicializar generador de QR
    initQRGenerator();
    
    // Cerrar modales al hacer clic fuera
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal-overlay')) {
            e.target.classList.add('hidden');
        }
    });
});