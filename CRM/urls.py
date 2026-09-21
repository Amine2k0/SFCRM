from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("register/", views.register_user, name="register"),
    path("ticket/", views.ticket, name="ticket"),
    path("addticket/", views.AddTicket, name="addticket"),
    path("editticket/<int:id>", views.EditTicket, name="editticket"),
    path("deleteticket/<int:id>", views.DeleteTicket, name="deleteticket"),
    path("user/", views.user, name="user"),
]
