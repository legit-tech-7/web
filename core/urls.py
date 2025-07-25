from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from myapp.views import dashboard, admin_approve_deposit, admin_approve_withdrawal

urlpatterns = [
    path('admin/', admin.site.urls),

    # Main dashboard
    

    # Your app urls
    path('', include('myapp.urls')),

    # ✅ Approval URLs for custom admin actions
    path('approve-deposit/<int:deposit_id>/', admin_approve_deposit, name='admin_approve_deposit'),
    path('approve-withdrawal/<int:withdrawal_id>/', admin_approve_withdrawal, name='admin_approve_withdrawal'),
]

# Serve media files (proof uploads)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom admin site branding
admin.site.site_header = "Crypto Finance Administration"
admin.site.site_title = "Crypto Finance Admin Portal"
admin.site.index_title = "Welcome to Crypto Finance Admin"
