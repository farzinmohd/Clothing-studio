from django.contrib import admin
from .models import UserProductInteraction, FAQ

admin.site.register(UserProductInteraction)

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'created_at')
    search_fields = ('question', 'answer')
    list_filter = ('category',)
