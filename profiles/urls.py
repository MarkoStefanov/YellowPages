from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

LOGOUT_REDIRECT_URL = 'login/'

urlpatterns = [
    path('edit_profile/', views.ProfileEditView.as_view(), name='profile-edit'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('history/', views.HistoryView.as_view(), name='history'),
    path('send-verification-code/', views.send_verification_code, name='send_verification_code'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)