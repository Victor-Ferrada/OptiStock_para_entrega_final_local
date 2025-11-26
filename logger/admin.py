from django.contrib import admin
from .models import SystemMessage

@admin.register(SystemMessage)
class SystemMessageAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'app', 'colored_message', 'level', 'user', 'ip_address', 'viewed']
    list_filter = ['app', 'level', 'viewed', 'timestamp']
    search_fields = ['message', 'user__username']
    readonly_fields = ['timestamp', 'ip_address']
    
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def changelist_view(self, request, extra_context=None):
        if not request.GET.get('unread'):
            SystemMessage.objects.filter(viewed=False).update(viewed=True)
        return super().changelist_view(request, extra_context)