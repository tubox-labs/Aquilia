import pytest

from aquilia.admin.permissions import AdminRole
from examples.admin_dashboard_app.modules.adminops.services import AdminOpsService, TicketRecord


def test_admin_dashboard_permissions_and_audit():
    service = AdminOpsService()
    service.create_ticket(TicketRecord("T-100", "user@example.test", "Cannot login"), actor_role=AdminRole.STAFF)
    service.assign_ticket("T-100", "agent@example.test", actor_role=AdminRole.STAFF)

    viewer_dashboard = service.dashboard(actor_role=AdminRole.VIEWER)
    staff_dashboard = service.dashboard(actor_role=AdminRole.STAFF)

    assert viewer_dashboard["tickets_total"] == 1
    assert viewer_dashboard["can_export"] is False
    assert staff_dashboard["can_export"] is True
    assert [e["action"] for e in staff_dashboard["recent_audit"]] == ["ticket.created", "ticket.assigned"]


def test_viewer_cannot_create_ticket():
    service = AdminOpsService()
    with pytest.raises(PermissionError):
        service.create_ticket(TicketRecord("T-101", "user@example.test", "Read-only"), actor_role=AdminRole.VIEWER)
