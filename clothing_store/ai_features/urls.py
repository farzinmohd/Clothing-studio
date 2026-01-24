from django.urls import path
from . import views

urlpatterns = [
    path("", views.ai_home, name="ai_home"),
    path("result/", views.ai_result, name="ai_result"),
    path("predict-size/", views.predict_size_api, name="predict_size_api"),
    path('visual-search/', views.visual_search, name='visual_search'),
    path('chatbot-response/', views.chatbot_response, name='chatbot_response'),
]
