from django.urls import include, path

urlpatterns = [
    path("api/", include("feedback.urls")),
    path("api/", include("corporate_broadcast.urls")),
]
