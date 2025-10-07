"""scribeArabic URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
#from . import views
from . import tag_views
from django.contrib.auth import views as auth_views

urlpatterns = [
    
    path('startannotate/', tag_views.login_view, name='login_view'),    
    path('show_directory/', tag_views.show_directory, name='show_directory'),
    path('upload', tag_views.upload_file, name='upload_file'),    
    path('tagImage', tag_views.tag_image, name='tag_image'), 
    path('starttagging', tag_views.tag_home, name='tag_home'),  
    path('tag/<str:user_name>/', tag_views.tag, name='tag'), 
    path('qa', tag_views.check_tags, name='check_tags'), 
    path('manual/', tag_views.manual_view, name='manual'),
    # login/auth related
    path('login/', tag_views.login_view, name='login'),
    path('accounts/password_change/', auth_views.PasswordChangeView.as_view(template_name='accounts/password_change.html'), name='password_change'),
    path('accounts/password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='accounts/password_change_done.html'), name='password_change_done'),

    # Password reset (no login required)
    path('accounts/password_reset/', auth_views.PasswordResetView.as_view(template_name='accounts/password_reset.html'), name='password_reset'),
    path('accounts/password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'), name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'), name='password_reset_confirm'),
    path('accounts/reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'), name='password_reset_complete')
]



