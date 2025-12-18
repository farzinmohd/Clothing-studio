from django.urls import path
from .views import admin_dashboard, sales_report_pdf, sales_report_excel

urlpatterns = [
    path('', admin_dashboard, name='admin_dashboard'),
    path('report/pdf/', sales_report_pdf, name='sales_report_pdf'),
    path('report/excel/', sales_report_excel, name='sales_report_excel'),
]
