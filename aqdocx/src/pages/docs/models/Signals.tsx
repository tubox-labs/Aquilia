import { useTheme } from '../../../context/ThemeContext';
import { CodeBlock } from '../../../components/CodeBlock';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { NextSteps } from '../../../components/NextSteps';

export function ModelsSignals() {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-2 text-sm mb-4">
          <Link to="/docs" className={isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}>Docs</Link>
          <span className={isDark ? 'text-gray-500' : 'text-gray-400'}>/</span>
          <Link to="/docs/models/overview" className={isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}>Models</Link>
          <span className={isDark ? 'text-gray-500' : 'text-gray-400'}>/</span>
          <span className={isDark ? 'text-gray-300' : 'text-gray-600'}>Signals</span>
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Model Signals
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-xl ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Hook into the model lifecycle at every stage using pre-save, post-save, pre-delete, post-delete, pre-init, post-init, and class_prepared signals.
        </p>
      </div>

      {/* Signals */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Model Lifecycle Signals</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Aquilia's signals system allows decoupled applications to get notified when actions occur elsewhere. Hook into the model lifecycle at every stage:
        </p>
        <CodeBlock language="python">
{`from aquilia.models.signals import (
    pre_save, post_save, pre_delete, post_delete,
    pre_init, post_init, class_prepared,
    m2m_changed, receiver,
)

@receiver(pre_save, sender=User)
async def hash_password(sender, instance, **kwargs):
    if instance._state.get("password_changed"):
        instance.password = hash_fn(instance.password)

@receiver(post_save, sender=User)
async def send_notification(sender, instance, created, **kwargs):
    if created:
        await send_welcome_email(instance.email)

@receiver(pre_delete, sender=User)
async def check_can_delete(sender, instance, **kwargs):
    if instance.is_superuser:
        raise PermissionError("Cannot delete superuser")

@receiver(class_prepared)
async def on_model_registered(sender, **kwargs):
    print(f"Model registered: {sender.__name__}")

# Signal.connect() / Signal.disconnect() for manual management
from aquilia.models.signals import Signal

custom_signal = Signal()
custom_signal.connect(my_handler, sender=MyModel)
await custom_signal.send(sender=MyModel, instance=obj)
custom_signal.disconnect(my_handler, sender=MyModel)`}
        </CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex justify-between items-center pt-8 mt-8 border-t ${isDark ? 'border-gray-700' : 'border-gray-200'}`}>
        <Link
          to="/docs/models/migrations"
          className={`flex items-center gap-2 text-sm font-medium ${isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}`}
        >
          <ArrowLeft className="w-4 h-4" /> Migrations
        </Link>
        <Link
          to="/docs/models/transactions"
          className={`flex items-center gap-2 text-sm font-medium ${isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}`}
        >
          Transactions <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  );
}
