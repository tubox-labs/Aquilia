import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Clock, Layout, Box, Plug } from 'lucide-react'

export function TasksController() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Clock className="w-4 h-4" />
          Tasks / Controller Guide
        </div>
        <h1 className={`text-4xl mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono">
            Controller Integration
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          How to use background tasks in Aquilia controllers with dependency injection, error handling, and best practices.
        </p>
      </div>

      {/* Setup */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Setup: TaskManager in Manifest
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Register the TaskManager in your app manifest for DI integration:
        </p>

        <CodeBlock language="python">{`# modules/core/manifest.py
from aquilia import AppManifest
from aquilia.tasks import TaskManager

manifest = AppManifest(
    name="core",
    services=[
        TaskManager,  # Register for DI
    ],
    # ... other config
)`}</CodeBlock>

        <p className={`mt-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Or configure with custom settings:
        </p>

        <CodeBlock language="python">{`# modules/core/manifest.py
from aquilia import AppManifest
from aquilia.tasks import TaskManager

def create_task_manager() -> TaskManager:
    return TaskManager(
        num_workers=8,
        queues=["default", "emails", "notifications"],
        poll_interval=0.5,
    )

manifest = AppManifest(
    name="core",
    factories=[
        (TaskManager, create_task_manager),
    ],
)`}</CodeBlock>
      </section>

      {/* Defining Tasks */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Defining Tasks
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Define tasks in a dedicated module that gets imported on app startup:
        </p>

        <CodeBlock language="python">{`# modules/notifications/tasks.py
from aquilia.tasks import task, Priority

@task(queue="notifications", priority=Priority.HIGH)
async def send_push_notification(
    user_id: int,
    title: str,
    body: str,
    data: dict | None = None,
) -> bool:
    """Send a push notification to a user."""
    from modules.notifications.services import PushService
    
    service = PushService()
    return await service.send(user_id, title, body, data)


@task(queue="emails", max_retries=5)
async def send_email(
    to: str,
    subject: str,
    template: str,
    context: dict,
) -> dict:
    """Send an email using a template."""
    from modules.mail.services import MailService
    
    service = MailService()
    result = await service.send_template(to, subject, template, context)
    return {"message_id": result.message_id, "sent": True}


@task(queue="analytics", priority=Priority.LOW)
async def track_event(
    user_id: int,
    event_name: str,
    properties: dict,
) -> None:
    """Track an analytics event."""
    from modules.analytics.services import AnalyticsService
    
    service = AnalyticsService()
    await service.track(user_id, event_name, properties)`}</CodeBlock>

        <div className={`mt-4 p-4 rounded-xl border ${isDark ? 'bg-amber-500/10 border-amber-500/30' : 'bg-amber-50 border-amber-200'}`}>
          <p className={`text-sm ${isDark ? 'text-amber-300' : 'text-amber-800'}`}>
            <strong>Important:</strong> Tasks must be imported before workers start. Add the import to your manifest or app initialization.
          </p>
        </div>
      </section>

      {/* Using in Controllers */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Using Tasks in Controllers
        </h2>

        <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
          Basic Usage
        </h3>
        <CodeBlock language="python">{`# modules/users/controllers.py
from aquilia import Controller, POST, RequestCtx, Response
from modules.notifications.tasks import send_push_notification, send_email

class UsersController(Controller):
    prefix = "/users"
    tags = ["users"]
    
    @POST("/")
    async def create_user(self, ctx: RequestCtx) -> Response:
        data = await ctx.json()
        
        # Create user in database
        user = await self.user_service.create(data)
        
        # Send welcome email in background
        await send_email.delay(
            to=user.email,
            subject="Welcome to Our App!",
            template="welcome",
            context={"name": user.name},
        )
        
        # Track signup event
        await track_event.delay(
            user_id=user.id,
            event_name="user.signup",
            properties={"source": data.get("source", "web")},
        )
        
        return Response.json({"id": user.id, "email": user.email}, status=201)`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
          With TaskManager Injection
        </h3>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          For more control, inject the TaskManager directly:
        </p>
        <CodeBlock language="python">{`from aquilia import Controller, POST, RequestCtx, Response
from aquilia.tasks import TaskManager
from modules.notifications.tasks import send_push_notification

class NotificationsController(Controller):
    prefix = "/notifications"
    tags = ["notifications"]
    
    def __init__(self, task_manager: TaskManager):
        self.task_manager = task_manager
    
    @POST("/broadcast")
    async def broadcast(self, ctx: RequestCtx) -> Response:
        data = await ctx.json()
        user_ids = data["user_ids"]
        message = data["message"]
        
        job_ids = []
        for user_id in user_ids:
            job_id = await self.task_manager.enqueue(
                send_push_notification,
                user_id=user_id,
                title="Announcement",
                body=message,
            )
            job_ids.append(job_id)
        
        return Response.json({
            "status": "queued",
            "job_count": len(job_ids),
            "job_ids": job_ids,
        })`}</CodeBlock>
      </section>

      {/* Error Handling */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Error Handling
        </h2>

        <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
          Handling Enqueue Errors
        </h3>
        <CodeBlock language="python">{`from aquilia import Controller, POST, RequestCtx, Response
from aquilia.tasks.faults import TaskNotBoundFault, TaskEnqueueFault
from modules.notifications.tasks import send_email

class EmailController(Controller):
    prefix = "/email"
    
    @POST("/send")
    async def send(self, ctx: RequestCtx) -> Response:
        data = await ctx.json()
        
        try:
            job_id = await send_email.delay(
                to=data["to"],
                subject=data["subject"],
                template=data["template"],
                context=data.get("context", {}),
            )
            return Response.json({"job_id": job_id, "status": "queued"})
            
        except TaskNotBoundFault:
            # TaskManager not started — fallback to sync
            await send_email(
                to=data["to"],
                subject=data["subject"],
                template=data["template"],
                context=data.get("context", {}),
            )
            return Response.json({"status": "sent_sync"})
            
        except TaskEnqueueFault as e:
            # Failed to enqueue — log and return error
            ctx.logger.error(f"Failed to enqueue email: {e.message}")
            return Response.json(
                {"error": "Failed to queue email"},
                status=500,
            )`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
          Checking Job Status
        </h3>
        <CodeBlock language="python">{`from aquilia import Controller, GET, RequestCtx, Response
from aquilia.tasks import TaskManager, JobState

class JobsController(Controller):
    prefix = "/jobs"
    
    def __init__(self, task_manager: TaskManager):
        self.task_manager = task_manager
    
    @GET("/{job_id}")
    async def get_status(self, ctx: RequestCtx, job_id: str) -> Response:
        job = await self.task_manager.get_job(job_id)
        
        if job is None:
            return Response.json({"error": "Job not found"}, status=404)
        
        response = {
            "id": job.id,
            "state": job.state.value,
            "created_at": job.created_at.isoformat(),
        }
        
        if job.state == JobState.COMPLETED:
            response["result"] = job.result.value
            response["duration_ms"] = job.result.duration_ms
        elif job.state in (JobState.FAILED, JobState.DEAD):
            response["error"] = job.result.error
            response["retry_count"] = job.retry_count
        
        return Response.json(response)`}</CodeBlock>
      </section>

      {/* Real-World Example */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Real-World Example: Order Processing
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          A complete example showing order creation with multiple background tasks:
        </p>

        <CodeBlock language="python">{`# modules/orders/tasks.py
from aquilia.tasks import task, Priority

@task(queue="orders", priority=Priority.HIGH, max_retries=5)
async def process_payment(order_id: int, payment_method: str, amount: float) -> dict:
    """Process payment for an order."""
    from modules.payments.services import PaymentService
    
    service = PaymentService()
    result = await service.charge(order_id, payment_method, amount)
    return {"transaction_id": result.transaction_id, "status": result.status}


@task(queue="inventory", priority=Priority.HIGH)
async def reserve_inventory(order_id: int, items: list[dict]) -> bool:
    """Reserve inventory for order items."""
    from modules.inventory.services import InventoryService
    
    service = InventoryService()
    return await service.reserve(order_id, items)


@task(queue="notifications")
async def send_order_confirmation(order_id: int, email: str) -> bool:
    """Send order confirmation email."""
    from modules.orders.services import OrderService
    from modules.mail.services import MailService
    
    order = await OrderService().get(order_id)
    await MailService().send_template(
        to=email,
        subject=f"Order #{order_id} Confirmed",
        template="order_confirmation",
        context={"order": order.to_dict()},
    )
    return True


@task(queue="analytics", priority=Priority.LOW)
async def track_purchase(order_id: int, user_id: int, total: float) -> None:
    """Track purchase analytics."""
    from modules.analytics.services import AnalyticsService
    
    await AnalyticsService().track(user_id, "order.completed", {
        "order_id": order_id,
        "total": total,
    })`}</CodeBlock>

        <CodeBlock language="python">{`# modules/orders/controllers.py
from aquilia import Controller, POST, RequestCtx, Response
from aquilia.tasks import TaskManager
from modules.orders.tasks import (
    process_payment,
    reserve_inventory,
    send_order_confirmation,
    track_purchase,
)

class OrdersController(Controller):
    prefix = "/orders"
    tags = ["orders"]
    
    def __init__(self, task_manager: TaskManager, order_service: OrderService):
        self.task_manager = task_manager
        self.order_service = order_service
    
    @POST("/")
    async def create_order(self, ctx: RequestCtx) -> Response:
        user = ctx.user
        data = await ctx.json()
        
        # Create order record (sync — needed for job references)
        order = await self.order_service.create(
            user_id=user.id,
            items=data["items"],
            shipping_address=data["shipping_address"],
        )
        
        # Process payment in background (high priority)
        payment_job = await process_payment.delay(
            order_id=order.id,
            payment_method=data["payment_method"],
            amount=order.total,
        )
        
        # Reserve inventory in background (high priority)
        inventory_job = await reserve_inventory.delay(
            order_id=order.id,
            items=data["items"],
        )
        
        # Send confirmation email (normal priority)
        email_job = await send_order_confirmation.delay(
            order_id=order.id,
            email=user.email,
        )
        
        # Track analytics (low priority)
        await track_purchase.delay(
            order_id=order.id,
            user_id=user.id,
            total=order.total,
        )
        
        return Response.json({
            "order_id": order.id,
            "status": "processing",
            "jobs": {
                "payment": payment_job,
                "inventory": inventory_job,
                "confirmation": email_job,
            },
        }, status=201)`}</CodeBlock>
      </section>

      {/* Testing */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Testing Controllers with Tasks
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Use direct calls to test task functions without the queue:
        </p>

        <CodeBlock language="python">{`# tests/test_orders.py
import pytest
from unittest.mock import AsyncMock, patch

from modules.orders.controllers import OrdersController
from modules.orders.tasks import process_payment

@pytest.fixture
def mock_task_manager():
    manager = AsyncMock()
    manager.enqueue.return_value = "test-job-id"
    return manager


class TestOrdersController:
    async def test_create_order_enqueues_tasks(self, mock_task_manager, mock_order_service):
        controller = OrdersController(mock_task_manager, mock_order_service)
        
        # Mock request context
        ctx = create_mock_ctx(user_id=1, json_data={
            "items": [{"sku": "ABC", "qty": 2}],
            "shipping_address": {"...": "..."},
            "payment_method": "stripe",
        })
        
        response = await controller.create_order(ctx)
        
        assert response.status_code == 201
        # Verify tasks were enqueued
        assert mock_task_manager.enqueue.call_count >= 3


class TestPaymentTask:
    async def test_process_payment_success(self):
        """Test task function directly (bypasses queue)."""
        with patch("modules.payments.services.PaymentService") as MockService:
            MockService.return_value.charge = AsyncMock(return_value=MockResult(
                transaction_id="txn_123",
                status="completed",
            ))
            
            result = await process_payment(
                order_id=1,
                payment_method="stripe",
                amount=99.99,
            )
            
            assert result["transaction_id"] == "txn_123"
            assert result["status"] == "completed"`}</CodeBlock>
      </section>

      {/* Best Practices */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Best Practices
        </h2>

        <div className="grid grid-cols-1 gap-4">
          {[
            {
              icon: <Layout className="w-5 h-5 text-aquilia-400" />,
              title: 'Separate Tasks from Controllers',
              desc: 'Define tasks in dedicated modules (tasks.py). Controllers should only call .delay() — not define tasks.',
            },
            {
              icon: <Plug className="w-5 h-5 text-blue-400" />,
              title: 'Use Dependency Injection',
              desc: 'Inject TaskManager for advanced control. Use .delay() for simple fire-and-forget cases.',
            },
            {
              icon: <Box className="w-5 h-5 text-amber-400" />,
              title: 'Keep Task Arguments Serializable',
              desc: 'Pass IDs, not objects. Tasks should fetch fresh data from the database to avoid stale state.',
            },
            {
              icon: <Clock className="w-5 h-5 text-purple-400" />,
              title: 'Return Job IDs to Clients',
              desc: 'Return job IDs in API responses so clients can poll for status or implement webhooks.',
            },
          ].map((item, i) => (
            <div key={i} className={`p-5 rounded-xl border ${isDark ? 'bg-[#111] border-white/10' : 'bg-white border-gray-200'}`}>
              <div className="flex items-center gap-3 mb-3">
                {item.icon}
                <h3 className={`font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>{item.title}</h3>
              </div>
              <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Next Steps */}
    </div>
  )
}
