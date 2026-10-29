from django.contrib import admin
from django.urls import path
from platform_app import views

urlpatterns = [
    path("admin/", admin.site.urls), path("", views.dashboard, name="dashboard"),
    path("login/", views.login_view, name="login"), path("register/", views.register, name="register"),
    path("logout/", views.logout_view, name="logout"), path("language/", views.language, name="language"),
    path("upload/", views.upload, name="upload"), path("history/", views.history, name="history"),
    path("guide/", views.guide, name="guide"), path("health/", views.health, name="health"),
    path("source/", views.source, name="source"),
    path("work/<uuid:pk>/", views.detail, name="detail"),
    path("work/<uuid:pk>/status/", views.job_status, name="job_status"),
    path("work/<uuid:pk>/preview/", views.preview, name="preview"),
    path("work/<uuid:pk>/download/<str:kind>/", views.download, name="download"),
    path("work/<uuid:pk>/delete/", views.delete_work, name="delete_work"),
]
handler404 = "platform_app.views.not_found"
handler500 = "platform_app.views.server_error"
