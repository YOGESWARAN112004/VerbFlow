from django.urls import path
from . import views
from django.contrib.auth import views as auth_view
from django.contrib.auth.views import logout_then_login


urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('login/', auth_view.LoginView.as_view(template_name='users/login.html'), name="login"),
    path('logout/', logout_then_login, name='logout'),
    path('speech-feedback/', views.speech_feedback_view, name='speech_feedback'),
    path('selector/', views.selector_view, name='selector'),
    path('debate/', views.debate_view, name='debate'),
    path('debate_txt/', views.debate_txt, name='debate_txt'),  # URL pattern for processing audio
    path('process/', views.process_audio, name='process_audio'),  # URL pattern for processing audio
    path('user-sessions/',views.user_session_list, name='user_session_list'),
]