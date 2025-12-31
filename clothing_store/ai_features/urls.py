from django.urls import path
from .views import ai_home, ai_result, predict_size_api, visual_search

urlpatterns = [
    path("", ai_home, name="ai_home"),
    path("result/", ai_result, name="ai_result"),
    path("predict-size/", predict_size_api, name="predict_size_api"),
    path("visual-search/", visual_search, name="visual_search"),
]
