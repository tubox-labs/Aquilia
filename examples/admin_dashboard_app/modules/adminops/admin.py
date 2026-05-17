from aquilia.admin import ModelAdmin, register

from .models import SupportTicket


@register(SupportTicket)
class SupportTicketAdmin(ModelAdmin):
    list_display = ["key", "customer_email", "subject", "priority", "assigned_to", "resolved"]
    list_filter = ["priority", "resolved"]
    search_fields = ["key", "customer_email", "subject"]
    ordering = ["resolved", "-created_at"]
    readonly_fields = ["key", "created_at", "updated_at"]
    export_formats = ["csv", "json"]
