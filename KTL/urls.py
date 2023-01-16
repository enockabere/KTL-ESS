from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls')),
    path('', include('HR.urls')),
    path('', include('Finance.urls')),
    path('', include('Procurement.urls')),
    path('', include('Approvals.urls')),
    path('', include('accounts.urls')),
    path('', include('advance.urls')),
    path('', include('appraisal.urls')),
]
