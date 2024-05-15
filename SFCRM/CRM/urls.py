from django.urls import path
from . import views

urlpatterns=[
    path("",views.home,name="home"),
    path("user/",views.user,name="user"),
    path("ticket/",views.ticket,name="ticket"),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register_user, name='register'),
    path('addticket/', views.AddTicket, name='addticket'),
    path('editticket/<int:id>', views.EditTicket, name='editticket'),
    path('DeleteTicket/<int:id>', views.DeleteTicket, name='deleteticket'),
]