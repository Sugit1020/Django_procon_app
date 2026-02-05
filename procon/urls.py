from django.urls import path, include
from . import views
urlpatterns = [
    path('', views.problem_list, name='problem_list'),
    path('problem/<int:pk>/', views.problem_detail, name='problem_detail'),
    
    # 標準の include よりも先に、自分で作ったログアウトを登録する
    path('accounts/logout/', views.manual_logout, name='logout'), 
    
    path('accounts/', include('django.contrib.auth.urls')),
    path('signup/', views.SignUpView.as_view(), name='signup'),
]