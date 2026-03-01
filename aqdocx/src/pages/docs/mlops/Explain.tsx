import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Brain } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function MLOpsExplain() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Brain className="w-4 h-4" />
          MLOps / Explainability & Privacy
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Explainability & Privacy
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Make model predictions interpretable with SHAP and LIME explainers, and protect user
          privacy with PII redaction, differential privacy noise, and input sanitization pipelines.
        </p>
      </div>

      {/* ExplainMethod Enum */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Explanation Methods</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-6">
          {[
            { method: 'SHAP_KERNEL', desc: 'Model-agnostic SHAP via kernel method' },
            { method: 'SHAP_TREE', desc: 'Optimized for tree-based models (XGBoost, LightGBM)' },
            { method: 'SHAP_DEEP', desc: 'Deep learning models via DeepExplainer' },
            { method: 'LIME_TABULAR', desc: 'LIME for tabular data' },
            { method: 'LIME_TEXT', desc: 'LIME for text classification' },
            { method: 'CUSTOM', desc: 'User-defined explanation method' },
          ].map((m, i) => (
            <div key={i} className={boxClass}>
              <code className="text-aquilia-500 text-sm font-mono block mb-1">{m.method}</code>
              <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{m.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* SHAPExplainer */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>SHAPExplainer</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Wraps the SHAP library to compute Shapley values for feature attribution. Auto-selects
          the appropriate SHAP method based on the model type.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops.explain.hooks import SHAPExplainer, ExplainMethod

# Kernel SHAP (model-agnostic)
explainer = SHAPExplainer(
    method=ExplainMethod.SHAP_KERNEL,
    background_data=X_train[:100],  # Background dataset for SHAP
)

# Explain a prediction
explanation = explainer.explain(
    model=model,
    inputs=X_test[0],
)
# Explanation(
#   method=ExplainMethod.SHAP_KERNEL,
#   feature_attributions=[
#     FeatureAttribution(feature="age", value=0.35, importance=0.28),
#     FeatureAttribution(feature="income", value=-0.12, importance=0.15),
#     FeatureAttribution(feature="credit_score", value=0.52, importance=0.41),
#   ],
#   base_value=0.5,
#   prediction=0.87,
# )

# Top-K most important features
top_features = explanation.top_k(3)
# [FeatureAttribution(feature="credit_score", ...), ...]

# Tree SHAP (for XGBoost, LightGBM, Random Forest)
tree_explainer = SHAPExplainer(
    method=ExplainMethod.SHAP_TREE,
    background_data=X_train,
)

# Deep SHAP (for PyTorch / TensorFlow models)
deep_explainer = SHAPExplainer(
    method=ExplainMethod.SHAP_DEEP,
    background_data=X_train[:50],
)`} />
      </section>

      {/* LIMEExplainer */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>LIMEExplainer</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Local Interpretable Model-agnostic Explanations. Creates a local linear approximation
          around a prediction to identify contributing features.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops.explain.hooks import LIMEExplainer, ExplainMethod

# Tabular LIME
tabular_explainer = LIMEExplainer(
    method=ExplainMethod.LIME_TABULAR,
    feature_names=["age", "income", "credit_score", "debt_ratio"],
    class_names=["rejected", "approved"],
    num_samples=5000,  # Perturbation samples
)

explanation = tabular_explainer.explain(
    model=model,
    inputs=X_test[0],
)
# Same Explanation dataclass as SHAP

# Text LIME
text_explainer = LIMEExplainer(
    method=ExplainMethod.LIME_TEXT,
    class_names=["negative", "positive"],
    num_samples=1000,
)

explanation = text_explainer.explain(
    model=sentiment_model,
    inputs="This product is absolutely fantastic!",
)
# FeatureAttribution(feature="fantastic", value=0.85, importance=0.62)
# FeatureAttribution(feature="absolutely", value=0.35, importance=0.25)`} />
      </section>

      {/* Factory */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Factory Function</h2>
        <CodeBlock language="python" code={`from aquilia.mlops.explain.hooks import create_explainer, ExplainMethod

# Auto-creates the right explainer
explainer = create_explainer(
    method=ExplainMethod.SHAP_TREE,
    background_data=X_train,
    feature_names=feature_names,
)

# Returns SHAPExplainer for SHAP_* methods
# Returns LIMEExplainer for LIME_* methods`} />
      </section>

      {/* PII Redaction */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>PII Redaction</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Automatically detect and redact personally identifiable information from model inputs
          before inference or logging.
        </p>

        <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>PII Types Detected</h3>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
          {['EMAIL', 'PHONE', 'SSN', 'CREDIT_CARD', 'IP_ADDRESS'].map((pii) => (
            <div key={pii} className={`p-3 rounded-lg text-center ${isDark ? 'bg-white/5' : 'bg-gray-50'}`}>
              <code className="text-aquilia-500 text-xs font-mono">{pii}</code>
            </div>
          ))}
        </div>

        <CodeBlock language="python" code={`from aquilia.mlops.explain.privacy import PIIRedactor, PIIKind

redactor = PIIRedactor(
    hash_replacement=True,  # Replace with SHA-256 hash (False = "[REDACTED]")
)

# Redact PII from text
clean_text = redactor.redact(
    "Contact john@example.com or call 555-123-4567. SSN: 123-45-6789"
)
# "Contact [SHA256:a1b2c3...] or call [SHA256:d4e5f6...]. SSN: [SHA256:g7h8i9...]"

# Or with hash_replacement=False:
# "Contact [REDACTED] or call [REDACTED]. SSN: [REDACTED]"

# Check which PII types were found
findings = redactor.detect(text)
# [
#   PIIFinding(kind=PIIKind.EMAIL, start=8, end=24, value="john@example.com"),
#   PIIFinding(kind=PIIKind.PHONE, start=33, end=45, value="555-123-4567"),
#   PIIFinding(kind=PIIKind.SSN, start=52, end=63, value="123-45-6789"),
# ]

# Regex patterns used:
# EMAIL:       r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}'
# PHONE:       r'\\b\\d{3}[-.]?\\d{3}[-.]?\\d{4}\\b'
# SSN:         r'\\b\\d{3}-\\d{2}-\\d{4}\\b'
# CREDIT_CARD: r'\\b\\d{4}[- ]?\\d{4}[- ]?\\d{4}[- ]?\\d{4}\\b'
# IP_ADDRESS:  r'\\b\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\b'`} />
      </section>

      {/* Differential Privacy */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Differential Privacy</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Add calibrated Laplacian noise to model outputs for ε-differential privacy guarantees.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops.explain.privacy import LaplaceNoise

noise = LaplaceNoise(
    epsilon=1.0,       # Privacy budget (lower = more private)
    sensitivity=1.0,   # Query sensitivity (max change from one record)
)

# Add noise to a numeric output
private_count = noise.add_noise(original_count)
# Adds Laplace(0, sensitivity/epsilon) noise

# Add noise to a vector
private_embeddings = noise.add_noise_vector(embeddings)
# Adds independent noise to each dimension

# Privacy guarantee:
# For any two neighboring datasets D and D' (differing by one record):
# P(M(D) ∈ S) ≤ e^ε × P(M(D') ∈ S)
# With epsilon=1.0: ratio bounded by e ≈ 2.718`} />
      </section>

      {/* InputSanitiser */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Input Sanitiser</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Composable transform pipeline for sanitizing model inputs before inference.
          PII redaction is included by default.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops.explain.privacy import InputSanitiser, PIIRedactor

sanitiser = InputSanitiser()

# Default transforms:
# 1. PII redaction (always applied)

# Add custom transforms
sanitiser.add_transform(lambda x: x.lower())           # Lowercase
sanitiser.add_transform(lambda x: x.strip())            # Trim whitespace
sanitiser.add_transform(lambda x: x[:10000])            # Truncate to 10K chars

# Apply all transforms in order
clean_input = sanitiser.sanitize(raw_input)
# 1. PII redaction → 2. lowercase → 3. strip → 4. truncate

# Use with inference pipeline
@preprocess
async def preprocess(request):
    request.inputs["text"] = sanitiser.sanitize(request.inputs["text"])
    return request`} />
      </section>

      <NextSteps
        items={[
          { text: 'Deployment', link: '/docs/mlops/deployment' },
          { text: 'Security', link: '/docs/mlops/security' },
          { text: 'Observability', link: '/docs/mlops/observability' },
          { text: 'MLOps Tutorial', link: '/docs/mlops/tutorial' },
        ]}
      />
    </div>
  )
}
