import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Brain, Rocket, Eye, GitBranch, FlaskConical, Package, Zap, Plug } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function CLIMLOpsCommands() {
    const { theme } = useTheme()
    const isDark = theme === 'dark'

    // Styles
    const sectionClass = "mb-16 scroll-mt-24"
    const h2Class = `text-2xl font-bold mb-6 flex items-center gap-3 ${isDark ? 'text-white' : 'text-gray-900'}`
    const h3Class = `text-lg font-semibold mt-8 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`
    const pClass = `mb-4 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`
    const codeClass = "text-xs font-mono bg-black/5 dark:bg-white/10 px-1.5 py-0.5 rounded text-aquilia-600 dark:text-aquilia-400"

    const Table = ({ children }: { children: React.ReactNode }) => (
        <div className={`overflow-hidden border rounded-lg mb-6 ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
            <table className="w-full text-sm text-left">
                <thead className={`text-xs uppercase ${isDark ? 'bg-white/5 text-gray-400' : 'bg-gray-50 text-gray-500'}`}>
                    <tr>
                        <th className="px-4 py-3 font-medium">Option</th>
                        <th className="px-4 py-3 font-medium">Description</th>
                        <th className="px-4 py-3 font-medium w-32">Default</th>
                    </tr>
                </thead>
                <tbody className={`divide-y ${isDark ? 'divide-white/10' : 'divide-gray-200'}`}>
                    {children}
                </tbody>
            </table>
        </div>
    )

    const Row = ({ opt, desc, def }: { opt: string, desc: string, def?: string }) => (
        <tr className={isDark ? 'hover:bg-white/5' : 'hover:bg-gray-50'}>
            <td className="px-4 py-3 font-mono text-aquilia-500">{opt}</td>
            <td className={`px-4 py-3 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>{desc}</td>
            <td className={`px-4 py-3 font-mono text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>{def || '-'}</td>
        </tr>
    )

    return (
        <div className="max-w-4xl mx-auto pb-20">
            {/* Header */}
            <div className="mb-12 border-b border-gray-200 dark:border-white/10 pb-8">
                <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
                    <Brain className="w-4 h-4" />
                    CLI / MLOps
                </div>
                <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
                  <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
                    MLOps Commands
                    <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
                  </span>
                </h1>
                <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                    Full-lifecycle ML operations from the command line: packaging models, serving inference endpoints, tracking lineage, and running A/B experiments.
                </p>
            </div>

            {/* Packaging */}
            <section id="pack" className={sectionClass}>
                <h2 className={h2Class}><Package className="w-6 h-6 text-purple-500" /> Model Packaging — aq pack</h2>

                <h3 className={h3Class}>pack save</h3>
                <p className={pClass}>
                    Bundles model artifacts and metadata into a portable <span className={codeClass}>.aquilia</span> archive.
                </p>
                <CodeBlock language="bash" filename="terminal">
                    aq pack save MODEL_PATH [OPTIONS]
                </CodeBlock>
                <Table>
                    <Row opt="MODEL_PATH" desc="Path to model file (positional, required)" />
                    <Row opt="--name, -n" desc="Model name (required)" />
                    <Row opt="--version, -V" desc="Semantic version string (required)" />
                    <Row opt="--framework, -f" desc="Framework: pytorch, tensorflow, sklearn, onnx, custom" def="custom" />
                    <Row opt="--env-lock" desc="Path to requirements.txt or conda lock file" />
                    <Row opt="--output, -o" desc="Output directory" def="." />
                    <Row opt="--sign-key" desc="HMAC key or path to RSA private key for signing" />
                </Table>
                <CodeBlock language="bash" filename="terminal">{`aq pack save model.pt -n my-model -V v1.0.0 -f pytorch
aq pack save model.onnx -n my-model -V v1.0.0 -f onnx --env-lock requirements.txt`}</CodeBlock>

                <h3 className={h3Class}>pack inspect</h3>
                <p className={pClass}>
                    Display the manifest of an <span className={codeClass}>.aquilia</span> archive as JSON.
                </p>
                <Table>
                    <Row opt="ARCHIVE_PATH" desc="Path to .aquilia archive (positional, required)" />
                </Table>
                <CodeBlock language="bash" filename="terminal">aq pack inspect my-model-v1.0.0.aquilia</CodeBlock>

                <h3 className={h3Class}>pack verify</h3>
                <p className={pClass}>
                    Verify the cryptographic signature of an <span className={codeClass}>.aquilia</span> archive.
                </p>
                <Table>
                    <Row opt="ARCHIVE_PATH" desc="Path to .aquilia archive (positional, required)" />
                    <Row opt="--key" desc="HMAC key or path to RSA public key (required)" />
                </Table>
                <CodeBlock language="bash" filename="terminal">aq pack verify my-model-v1.0.0.aquilia --key mysecret</CodeBlock>

                <h3 className={h3Class}>pack push</h3>
                <p className={pClass}>
                    Push a model pack to a remote registry. Optionally apply additional tags.
                </p>
                <Table>
                    <Row opt="ARCHIVE_PATH" desc="Path to .aquilia archive (positional, required)" />
                    <Row opt="--registry, -r" desc="Registry URL" def="http://localhost:8080" />
                    <Row opt="--tag, -t" desc="Additional tags (repeatable)" />
                </Table>
                <CodeBlock language="bash" filename="terminal">{`aq pack push my-model-v1.0.0.aquilia --registry http://registry.internal
aq pack push my-model-v1.0.0.aquilia -t production -t stable`}</CodeBlock>
            </section>

            {/* Serving */}
            <section id="serve" className={sectionClass}>
                <h2 className={h2Class}><Rocket className="w-6 h-6 text-green-500" /> Model Serving — aq model</h2>

                <h3 className={h3Class}>model serve</h3>
                <p className={pClass}>
                    Starts a high-performance inference server with dynamic batching support.
                </p>
                <CodeBlock language="bash" filename="terminal">
                    aq model serve MODEL_PATH [OPTIONS]
                </CodeBlock>
                <Table>
                    <Row opt="MODEL_PATH" desc="Path to model file (positional, required)" />
                    <Row opt="--runtime, -r" desc="Inference runtime: python, onnx, triton" def="python" />
                    <Row opt="--host" desc="Bind host address" def="0.0.0.0" />
                    <Row opt="--port, -p" desc="Bind port" def="9000" />
                    <Row opt="--batch-size" desc="Max batch size for dynamic batching" def="1" />
                    <Row opt="--batch-latency-ms" desc="Max batch wait time in milliseconds" def="50" />
                </Table>
                <CodeBlock language="bash" filename="terminal">{`aq model serve model.pt --runtime python --port 9000
aq model serve model.onnx --runtime onnx --batch-size 8`}</CodeBlock>

                <h3 className={h3Class}>model health</h3>
                <p className={pClass}>
                    Check model server health by querying the <span className={codeClass}>/health</span> endpoint.
                </p>
                <Table>
                    <Row opt="--url" desc="Server URL" def="http://localhost:9000" />
                </Table>
                <CodeBlock language="bash" filename="terminal">aq model health --url http://localhost:9000</CodeBlock>
            </section>

            {/* Deployment */}
            <section id="deploy" className={sectionClass}>
                <h2 className={h2Class}><Zap className="w-6 h-6 text-yellow-500" /> MLOps Deployment — aq deploy</h2>

                <h3 className={h3Class}>deploy rollout</h3>
                <p className={pClass}>
                    Start a progressive rollout with configurable strategy, step count, and auto-rollback threshold.
                </p>
                <CodeBlock language="bash" filename="terminal">
                    aq deploy rollout MODEL_NAME [OPTIONS]
                </CodeBlock>
                <Table>
                    <Row opt="MODEL_NAME" desc="Model name (positional, required)" />
                    <Row opt="--from-version" desc="Current stable version (required)" />
                    <Row opt="--to-version" desc="Target candidate version (required)" />
                    <Row opt="--strategy" desc="Rollout strategy: canary, blue_green, shadow, rolling" def="canary" />
                    <Row opt="--steps" desc="Number of incremental rollout phases" def="5" />
                    <Row opt="--error-threshold" desc="Auto-rollback error rate threshold" def="0.05" />
                </Table>
                <CodeBlock language="bash" filename="terminal">{`aq deploy rollout my-model --from-version v1 --to-version v2 --strategy canary`}</CodeBlock>

                <h3 className={h3Class}>deploy ci-template</h3>
                <p className={pClass}>
                    Generate CI/CD templates (GitHub Actions workflow + Dockerfile) for model deployment.
                </p>
                <Table>
                    <Row opt="--registry" desc="Container registry URL" def="ghcr.io/my-org/models" />
                    <Row opt="--output, -o" desc="Output directory" def="." />
                </Table>
                <CodeBlock language="bash" filename="terminal">{`aq deploy ci-template --registry ghcr.io/my-org --output .ci/`}</CodeBlock>
            </section>

            {/* Observability */}
            <section id="observe" className={sectionClass}>
                <h2 className={h2Class}><Eye className="w-6 h-6 text-blue-500" /> Observability — aq observe</h2>

                <h3 className={h3Class}>observe drift</h3>
                <p className={pClass}>
                    Detect data drift between reference and current datasets. Compares per-column distributions and flags drifted features.
                </p>
                <CodeBlock language="bash" filename="terminal">
                    aq observe drift REFERENCE_CSV CURRENT_CSV [OPTIONS]
                </CodeBlock>
                <Table>
                    <Row opt="REFERENCE_CSV" desc="Reference dataset CSV (positional, required)" />
                    <Row opt="CURRENT_CSV" desc="Current dataset CSV (positional, required)" />
                    <Row opt="--method" desc="Statistical method: psi, ks_test" def="psi" />
                    <Row opt="--threshold" desc="Drift alert threshold" def="0.2" />
                </Table>
                <CodeBlock language="bash" filename="terminal">{`aq observe drift train.csv prod.csv --method psi --threshold 0.25`}</CodeBlock>

                <h3 className={h3Class}>observe metrics</h3>
                <p className={pClass}>
                    Export current metrics in JSON or Prometheus format.
                </p>
                <Table>
                    <Row opt="--format" desc="Output format: json, prometheus" def="json" />
                </Table>
                <CodeBlock language="bash" filename="terminal">{`aq observe metrics --format prometheus`}</CodeBlock>
            </section>

            {/* Export */}
            <section id="export" className={sectionClass}>
                <h2 className={h2Class}><Zap className="w-6 h-6 text-cyan-500" /> Edge Export — aq export</h2>

                <h3 className={h3Class}>export onnx</h3>
                <p className={pClass}>
                    Export a PyTorch model to ONNX format.
                </p>
                <Table>
                    <Row opt="MODEL_PATH" desc="Path to model file (positional, required)" />
                    <Row opt="--output, -o" desc="Output .onnx path (required)" />
                    <Row opt="--opset" desc="ONNX opset version" def="17" />
                </Table>
                <CodeBlock language="bash" filename="terminal">{`aq export onnx model.pt -o model.onnx --opset 17`}</CodeBlock>

                <h3 className={h3Class}>export edge</h3>
                <p className={pClass}>
                    Export model for edge deployment targets.
                </p>
                <Table>
                    <Row opt="MODEL_PATH" desc="Path to model file (positional, required)" />
                    <Row opt="--target" desc="Target: tflite, coreml, onnx_quantised, tensorrt (required)" />
                    <Row opt="--output, -o" desc="Output file path (required)" />
                </Table>
                <CodeBlock language="bash" filename="terminal">{`aq export edge model.onnx --target tflite -o model.tflite
aq export edge model.onnx --target coreml -o model.mlmodel`}</CodeBlock>
            </section>

            {/* Lineage */}
            <section id="lineage" className={sectionClass}>
                <h2 className={h2Class}><GitBranch className="w-6 h-6 text-orange-500" /> Lineage — aq lineage</h2>

                <h3 className={h3Class}>lineage show</h3>
                <p className={pClass}>
                    Show the full model lineage graph as a tree or JSON.
                </p>
                <Table>
                    <Row opt="--format" desc="Output format: tree, json" def="tree" />
                </Table>
                <CodeBlock language="bash" filename="terminal">{`aq lineage show
aq lineage show --format json`}</CodeBlock>

                <h3 className={h3Class}>lineage ancestors</h3>
                <p className={pClass}>
                    Show all ancestors (transitive parents) of a model.
                </p>
                <Table>
                    <Row opt="MODEL_ID" desc="Model identifier (positional, required)" />
                </Table>
                <CodeBlock language="bash" filename="terminal">aq lineage ancestors fine-tuned-v2</CodeBlock>

                <h3 className={h3Class}>lineage descendants</h3>
                <p className={pClass}>
                    Show all descendants (derived models) of a model.
                </p>
                <Table>
                    <Row opt="MODEL_ID" desc="Model identifier (positional, required)" />
                </Table>
                <CodeBlock language="bash" filename="terminal">aq lineage descendants base-model-v1</CodeBlock>

                <h3 className={h3Class}>lineage path</h3>
                <p className={pClass}>
                    Find the derivation path between two models in the lineage DAG.
                </p>
                <Table>
                    <Row opt="FROM_MODEL" desc="Source model (positional, required)" />
                    <Row opt="TO_MODEL" desc="Target model (positional, required)" />
                </Table>
                <CodeBlock language="bash" filename="terminal">aq lineage path base-v1 prod-v3</CodeBlock>
            </section>

            {/* Experiments */}
            <section id="experiment" className={sectionClass}>
                <h2 className={h2Class}><FlaskConical className="w-6 h-6 text-pink-500" /> Experiments — aq experiment</h2>

                <h3 className={h3Class}>experiment create</h3>
                <p className={pClass}>
                    Create a new A/B experiment with named arms, model versions, and traffic weights.
                </p>
                <CodeBlock language="bash" filename="terminal">
                    aq experiment create EXPERIMENT_ID [OPTIONS]
                </CodeBlock>
                <Table>
                    <Row opt="EXPERIMENT_ID" desc="Unique experiment identifier (positional, required)" />
                    <Row opt="--description, -d" desc="Experiment description" def="''" />
                    <Row opt="--arm, -a" desc="Arm spec: name:version:weight (repeatable)" />
                </Table>
                <CodeBlock language="bash" filename="terminal">{`aq experiment create latency-test -d "Compare v1 vs v2" \\
  -a control:v1:0.5 -a treatment:v2:0.5`}</CodeBlock>

                <h3 className={h3Class}>experiment list</h3>
                <p className={pClass}>
                    List all experiments with status, arm count, and winner.
                </p>
                <CodeBlock language="bash" filename="terminal">aq experiment list</CodeBlock>

                <h3 className={h3Class}>experiment conclude</h3>
                <p className={pClass}>
                    Conclude an experiment and optionally declare a winning arm.
                </p>
                <Table>
                    <Row opt="EXPERIMENT_ID" desc="Experiment identifier (positional, required)" />
                    <Row opt="--winner, -w" desc="Winning arm name" />
                </Table>
                <CodeBlock language="bash" filename="terminal">aq experiment conclude latency-test --winner treatment</CodeBlock>

                <h3 className={h3Class}>experiment summary</h3>
                <p className={pClass}>
                    Show detailed experiment summary with per-arm metrics as JSON.
                </p>
                <Table>
                    <Row opt="EXPERIMENT_ID" desc="Experiment identifier (positional, required)" />
                </Table>
                <CodeBlock language="bash" filename="terminal">aq experiment summary latency-test</CodeBlock>
            </section>

            {/* Plugins */}
            <section id="plugins" className={sectionClass}>
                <h2 className={h2Class}><Plug className="w-6 h-6 text-teal-500" /> Plugins — aq plugin</h2>

                <h3 className={h3Class}>plugin list</h3>
                <p className={pClass}>
                    List all discovered plugins from Python entrypoints with name, version, state, and module path.
                </p>
                <CodeBlock language="bash" filename="terminal">aq plugin list</CodeBlock>

                <h3 className={h3Class}>plugin install</h3>
                <p className={pClass}>
                    Install a plugin from PyPI.
                </p>
                <Table>
                    <Row opt="PACKAGE_NAME" desc="PyPI package name (positional, required)" />
                </Table>
                <CodeBlock language="bash" filename="terminal">aq plugin install aquilia-mlops-drift-monitor</CodeBlock>

                <h3 className={h3Class}>plugin uninstall</h3>
                <p className={pClass}>
                    Uninstall a previously installed plugin.
                </p>
                <Table>
                    <Row opt="PACKAGE_NAME" desc="Package name (positional, required)" />
                </Table>
                <CodeBlock language="bash" filename="terminal">aq plugin uninstall aquilia-mlops-drift-monitor</CodeBlock>

                <h3 className={h3Class}>plugin search</h3>
                <p className={pClass}>
                    Search the plugin marketplace for available plugins.
                </p>
                <Table>
                    <Row opt="QUERY" desc="Search query (positional, required)" />
                    <Row opt="--verified-only" desc="Only show verified plugins" def="false" />
                </Table>
                <CodeBlock language="bash" filename="terminal">{`aq plugin search drift
aq plugin search monitoring --verified-only`}</CodeBlock>
            </section>
        
      <NextSteps />
    </div>
    )
}