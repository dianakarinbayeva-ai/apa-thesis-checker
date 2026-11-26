from django.contrib import admin
from django.urls import path
from platform_app import views
from platform_app import curator
from platform_app import review_viewer

urlpatterns = [
    path("admin/", admin.site.urls), path("", views.dashboard, name="dashboard"),
    path("login/", views.login_view, name="login"), path("register/", views.register, name="register"),
    path("logout/", views.logout_view, name="logout"), path("language/", views.language, name="language"),
    path("join-group/", views.join_group, name="join_group"),
    path("curator/", curator.dashboard, name="curator_dashboard"),
    path("curator/group/<int:pk>/", curator.group_detail, name="curator_group"),
    path("curator/work/<uuid:pk>/", views.detail, {"curator_view": True}, name="curator_detail"),
    path("curator/work/<uuid:pk>/status/", views.job_status, {"curator_view": True}, name="curator_job_status"),
    path("curator/work/<uuid:pk>/preview/", views.preview, {"curator_view": True}, name="curator_preview"),
    path("curator/work/<uuid:pk>/viewer/", review_viewer.viewer, {"curator_view": True}, name="curator_viewer"),
    path("curator/work/<uuid:pk>/page-image/", review_viewer.page_image, {"curator_view": True}, name="curator_page_image"),
    path("curator/work/<uuid:pk>/download/<str:kind>/", views.download, {"curator_view": True}, name="curator_download"),
    path("upload/", views.upload, name="upload"), path("history/", views.history, name="history"),
    path("guide/", views.guide, name="guide"), path("health/", views.health, name="health"),
    path("source/", views.source, name="source"),
    path("work/<uuid:pk>/", views.detail, name="detail"),
    path("work/<uuid:pk>/status/", views.job_status, name="job_status"),
    path("work/<uuid:pk>/preview/", views.preview, name="preview"),
    path("work/<uuid:pk>/viewer/", review_viewer.viewer, name="viewer"),
    path("work/<uuid:pk>/page-image/", review_viewer.page_image, name="page_image"),
    path("work/<uuid:pk>/download/<str:kind>/", views.download, name="download"),
    path("work/<uuid:pk>/delete/", views.delete_work, name="delete_work"),
]
handler404 = "platform_app.views.not_found"
handler500 = "platform_app.views.server_error"
