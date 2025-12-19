from django.urls import path
from .views import ai_home, ai_result

urlpatterns = [
    path("", ai_home, name="ai_home"),
    path("result/", ai_result, name="ai_result"),
]
