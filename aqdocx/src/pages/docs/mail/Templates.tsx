import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Code } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function MailTemplates() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-600'
  const borderMuted = isDark ? 'border-white/5' : 'border-gray-100'

  return (
    <div className="max-w-4xl mx-auto px-4 py-2">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Code className="w-4 h-4" />
          Mail / Templates
        </div>
        <h1 className={`text-4xl font-extrabold tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="gradient-text font-mono">Aquilia Template Syntax (ATS)</span>
        </h1>
        <p className={`text-lg leading-relaxed ${textMuted}`}>
          AquilaMail templates utilize the Aquilia Template Syntax (ATS). ATS provides a simple expression engine designed to prevent code-injection vulnerabilities inside email bodies.
        </p>
      </div>

      {/* Extended Template Syntax Example */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          ATS Syntax Reference & Complete Example
        </h2>
        <p className={`text-sm mb-6 ${textMuted}`}>
          The following example compiles user profiles, loops through purchases, formats localized currency, and structures blocks inside a single transaction receipt template:
        </p>
        <CodeBlock
          language="html"
          filename="mail_templates/order_receipt.aqt"
          highlightLines={[1, 4, 8, 12, 16, 21]}
        >{`[[% extends "layouts/base.aqt" %]]

[[% block body %]]
  <!-- 1. Dotted variable resolutions with title casing -->
  <h2>Hi, << order.customer.profile.name | title >>!</h2>
  
  <!-- 2. Global variable bindings and formatting filters -->
  <p>Thank you for shopping at << brand_name | upper >>. Your order #<< order.number >> has cleared.</p>
  
  <!-- 3. Loop iteration over transaction collections -->
  <h3>Your Ordered Items:</h3>
  <ul>
    [[% for item in order.items %]]
      <li><< item.title >> (Qty: << item.qty >>) - << item.subtotal | format_currency("USD") >></li>
    [[% endfor %]]
  </ul>

  <!-- 4. Control-flow conditional blocks -->
  [[% if order.discount_amount > 0 %]]
    <p style="color: #22c55e;">Promo applied: -<< order.discount_amount | format_currency("USD") >></p>
  [[% else %]]
    <p style="color: #999;">No promotional codes applied.</p>
  [[% endif %]]
[[% endblock %]]`}</CodeBlock>
      </section>

      {/* Syntax Details */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          ATS Syntax Rules
        </h2>
        <div className="space-y-8">
          {[
            {
              syntax: '<< expr >>',
              desc: 'Expression interpolation. Safely resolves dotted attributes or dictionary keys. If a variable resolves to None or raises AttributeError, it fails gracefully and prints an empty string.',
              code: `<!-- Context: {"user": {"profile": {"first_name": "asha"}}} -->
<p>Hello, << user.profile.first_name >>!</p>
<!-- Result: <p>Hello, asha!</p> -->`
            },
            {
              syntax: '<< expr | filter >>',
              desc: 'Applies formatting filters to variables. Filters can accept parameters. Standard whitelisted filters include uppercase, title, date formats, and localized currency symbols.',
              code: `<!-- Context: {"product": {"price": 99.95, "title": "aquilia book"}} -->
<p>Product: << product.title | title >> - << product.price | format_currency("EUR") >></p>
<!-- Result: <p>Product: Aquilia Book - €99.95</p> -->`
            },
            {
              syntax: '[[% if condition %]] ... [[% endif %]]',
              desc: 'Control-flow conditional branches for displaying content contextually based on truthy/falsy evaluation.',
              code: `<!-- Context: {"user": {"is_vip": True}} -->
[[% if user.is_vip %]]
  <p>Thank you for being a VIP member!</p>
[[% endif %]]`
            },
            {
              syntax: '[[% for item in list %]] ... [[% endfor %]]',
              desc: 'Loop iteration blocks for lists, matrices, or collections.',
              code: `<!-- Context: {"features": ["Caching", "DI", "Sockets"]} -->
<ul>
  [[% for feature in features %]]
    <li>Feature: << feature >></li>
  [[% endfor %]]
</ul>`
            },
            {
              syntax: '[[% block name %]] ... [[% endblock %]]',
              desc: 'Declares layout inheritance blocks. Enables base templates to define regions that extending child templates override.',
              code: `<!-- base.aqt -->
<div class="main-body">
  [[% block main %]][[% endblock %]]
</div>

<!-- welcome.aqt -->
[[% extends "base.aqt" %]]
[[% block main %]]
  <p>Overridden template content body.</p>
[[% endblock %]]`
            }
          ].map((item, i) => (
            <div key={i} className="py-4 border-b border-white/5 last:border-0">
              <h3 className={`font-semibold text-sm mb-2 ${isDark ? 'text-white' : 'text-gray-900'} font-mono`}>
                {item.syntax}
              </h3>
              <p className={`text-sm mb-3 ${textMuted}`}>{item.desc}</p>
              <CodeBlock language="html">{item.code}</CodeBlock>
            </div>
          ))}
        </div>
      </section>

      {/* TemplateMessage Usage */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Using TemplateMessage
        </h2>
        <p className={`text-sm mb-6 ${textMuted}`}>
          Instantiate a <DocTerm id="mail.TemplateMessage">TemplateMessage</DocTerm> class with the template file path and context payload. Subject lines can also contain inline ATS expressions:
        </p>
        <CodeBlock
          language="python"
          filename="send_template.py"
          highlightLines={[4, 5, 6, 7]}
        >{`from aquilia.mail import TemplateMessage

msg = TemplateMessage(
    template="order_receipt.aqt",
    context={
        "order": {
            "number": "TX-104",
            "customer": {"profile": {"name": "asha"}},
            "total": 129.99,
            "discount_amount": 15.00,
            "items": [
                {"title": "Aquilia Server License", "qty": 1, "subtotal": 129.99}
            ]
        },
        "brand_name": "Aquilia Inc"
    },
    subject="Your Receipt for << order.number >> from << brand_name >>!",
    to=["asha@example.com"]
)

# Template renders at envelope compile time. HTML and text alternative are generated.
await msg.asend()`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${borderMuted}`}>
        <Link to="/docs/mail/providers" className={`flex items-center gap-2 text-sm ${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`}>
          <ArrowLeft className="w-4 h-4" /> Providers
        </Link>
        <Link to="/docs/getting-started/developer-guide" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400">
          Developer Guide <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps
        items={[
          { text: 'Developer Integration Guide', link: '/docs/getting-started/developer-guide' },
          { text: 'Storage Subsystem Overview', link: '/docs/storage' },
          { text: 'CLI and Macro Tools', link: '/docs/cli' },
        ]}
      />
    </div>
  )
}