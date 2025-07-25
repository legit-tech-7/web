from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('reset_password/<str:token>/', views.reset_password_confirm, name='reset_password_confirm'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('deposit_history/', views.deposit_history, name='deposit_history'),
    path('withdrawal_history/', views.withdrawal_history, name='withdrawal_history'),
    path('earnings_history/', views.earnings_history, name='earnings_history'),
    
    # Transactions
    path('deposit/', views.create_deposit, name='create_deposit'),
    path('withdraw/', views.create_withdrawal, name='create_withdrawal'),
    
    # Admin
    path('staff/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
path('approve-deposit/<int:deposit_id>/', views.admin_approve_deposit, name='approve_deposit'),
path('approve-withdrawal/<int:withdrawal_id>/', views.admin_approve_withdrawal, name='approve_withdrawal'),
    # AJAX
    path('toggle-balance/', views.toggle_balance_visibility, name='toggle_balance'),

    path('', views.index, name= 'index'),
    path('about/', views.about, name= 'about')

]