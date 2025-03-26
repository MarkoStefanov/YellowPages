from django.urls import include, path
from . import views

LOGOUT_REDIRECT_URL = 'login/'

urlpatterns = [
    path('edit_profile/', views.ProfileEditView.as_view(), name='profile-edit'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('history/', views.HistoryView.as_view(), name='history'),

]