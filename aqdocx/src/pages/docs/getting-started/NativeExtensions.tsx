import { Link } from 'react-router-dom'
import { Binary, CheckCircle, AlertTriangle, ArrowRight } from 'lucide-react'
import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { NextSteps } from '../../../components/NextSteps'

export function NativeExtensionsPage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const text = isDark ? 'text-gray-400' : 'text-gray-600'
  const heading = isDark ? 'text-white' : 'text-gray-900'
  const panel = isDark ? 'border-white/10 bg-white/[0.03]' : 'border-gray-200 bg-gray-50'

  return (
    <div className="max-w-4xl mx-auto pb-20">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Binary className="w-4 h-4" />
          Getting Started / Native Extensions
        </div>
        <h1 className={`text-4xl font-bold font-mono ${heading}`}>Native Extensions</h1>
        <p className={`text-lg leading-relaxed mt-4 ${text}`}>
          Aquilia ships three optional C/C++ acceleration modules: <code>_core</code>,{' '}
          <code>_dataengine</code>, and <code>_json</code>. Binary wheels enable them automatically;
          source installs fall back to equivalent Python implementations when a compiler is unavailable.
        </p>
      </div>

      <section className="mb-14">
        <h2 className={`text-2xl font-bold mb-5 ${heading}`}>Runtime Contract</h2>
        <div className="grid md:grid-cols-3 gap-4">
          {[
            ['_core', 'Router and request-context acceleration'],
            ['_dataengine', 'ORM and Contract field-plan acceleration'],
            ['_json', 'yyjson-backed serialization'],
          ].map(([name, description]) => (
            <div key={name} className={`border rounded-lg p-4 ${panel}`}>
              <code className="text-aquilia-500 font-bold">{name}</code>
              <p className={`text-sm mt-2 ${text}`}>{description}</p>
            </div>
          ))}
        </div>
        <p className={`mt-5 ${text}`}>
          The Python fallback is a compatibility path, not a reduced API edition. Application behavior
          must remain the same, but CPU-bound routing, hydration, and JSON workloads can be slower.
          Native availability must never be used as a feature flag for application logic.
        </p>
      </section>

      <section className="mb-14">
        <h2 className={`text-2xl font-bold mb-5 ${heading}`}>Install and Verify</h2>
        <p className={`mb-4 ${text}`}>
          Prefer a published wheel. Aquilia v1.4.0b5 publishes CPython 3.10 through 3.14 wheels for
          Windows AMD64, Linux x86_64/aarch64, and macOS x86_64/arm64.
        </p>
        <CodeBlock language="bash" code={`python -m pip install --upgrade "aquilia==1.4.0b5"
python -c "from aquilia._core_loader import NATIVE; from aquilia._dataengine_loader import DATAENGINE_NATIVE; from aquilia.json import native as JSON_NATIVE; print(NATIVE, DATAENGINE_NATIVE, JSON_NATIVE)"`} />
        <div className={`mt-5 border rounded-lg p-5 ${panel}`}>
          <div className="flex items-start gap-3">
            <CheckCircle className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" />
            <p className={`text-sm ${text}`}>
              A release wheel should print <code>True True True</code>. A compiler-free source install
              may print <code>False False False</code>; that is an intentional, functional fallback.
            </p>
          </div>
        </div>
      </section>

      <section className="mb-14">
        <h2 className={`text-2xl font-bold mb-5 ${heading}`}>What Changed in v1.4.0b5</h2>
        <div className="space-y-5">
          <div>
            <h3 className={`font-bold ${heading}`}>Windows wheels use the stable Visual Studio 2022 ABI</h3>
            <p className={`mt-1 ${text}`}>
              Earlier beta wheels could be built by a preview MSVC toolchain and import successfully on
              the CI runner while failing on an ordinary Windows installation with “The specified module
              could not be found.” b5 pins the Windows wheel builder to Visual Studio 17 2022 and links the
              MSVC runtime statically into all three extension targets.
            </p>
          </div>
          <div>
            <h3 className={`font-bold ${heading}`}>Compiler probing happens before language enablement</h3>
            <p className={`mt-1 ${text}`}>
              The root CMake project now starts with <code>LANGUAGES NONE</code>, probes C and C++, and
              enables them only when both compilers exist. With <code>AQUILIA_ENGINE_OPTIONAL=ON</code>,
              a missing toolchain returns a pure-Python package instead of aborting at <code>project()</code>.
            </p>
          </div>
          <div>
            <h3 className={`font-bold ${heading}`}>Release builds are strict</h3>
            <p className={`mt-1 ${text}`}>
              End-user source installs remain optional, but release-wheel CI passes
              <code>-DAQUILIA_ENGINE_OPTIONAL=OFF</code>. A missing extension fails the build, and the wheel
              is imported from outside the checkout so local source files cannot hide packaging defects.
            </p>
          </div>
        </div>
      </section>

      <section className="mb-14">
        <h2 className={`text-2xl font-bold mb-5 ${heading}`}>Source Builds</h2>
        <CodeBlock language="bash" code={`# Native build: requires CMake 3.21+ and a C++20 compiler
python -m pip install --no-binary aquilia "aquilia==1.4.0b5"

# Strict local verification: fail instead of falling back
CMAKE_ARGS="-DAQUILIA_ENGINE_OPTIONAL=OFF" python -m pip install .`} />
        <p className={`mt-4 ${text}`}>
          On Windows, install Visual Studio Build Tools with the “Desktop development with C++” workload.
          Users who only need the framework API do not need a compiler; the build backend supplies Ninja
          so CMake can complete the compiler-free fallback configuration.
        </p>
      </section>

      <section className="mb-14">
        <h2 className={`text-2xl font-bold mb-5 ${heading}`}>Troubleshooting Windows DLL Errors</h2>
        <div className={`border rounded-lg p-5 ${panel}`}>
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
            <div>
              <p className={`font-semibold ${heading}`}>
                <code>DLL load failed ... The specified module could not be found</code>
              </p>
              <ol className={`list-decimal ml-5 mt-3 space-y-2 text-sm ${text}`}>
                <li>Confirm <code>python -m pip show aquilia</code> reports v1.4.0b5 or newer.</li>
                <li>Reinstall without cache so pip cannot reuse an affected beta wheel.</li>
                <li>Run the diagnostic command below and include its output in bug reports.</li>
                <li>Do not copy <code>.pyd</code> files between Python versions or architectures.</li>
              </ol>
            </div>
          </div>
        </div>
        <CodeBlock language="bash" code={`python -m pip install --force-reinstall --no-cache-dir "aquilia==1.4.0b5"
python -c "from aquilia._core_loader import engine_info; from aquilia._dataengine_loader import dataengine_info; from aquilia.json import backend; print(engine_info()); print(dataengine_info()); print(backend())"`} />
      </section>

      <section className={`mb-12 border rounded-lg p-5 ${panel}`}>
        <h2 className={`text-lg font-bold mb-2 ${heading}`}>Compatibility and Migration</h2>
        <p className={text}>
          There is no application API migration. Environment variables and{' '}
          <Link className="text-aquilia-500 hover:underline" to="/docs/config/pyconfig">AquilaConfig.Accelerator</Link>{' '}
          retain their existing runtime meaning. The CMake option controls build strictness; it does not
          enable or disable an already-installed extension at runtime.
        </p>
        <Link to="/releases/1.4.0b5/migration.md" className="inline-flex items-center gap-1 mt-4 text-aquilia-500 font-semibold text-sm">
          Read the v1.4.0b5 migration guide <ArrowRight className="w-4 h-4" />
        </Link>
      </section>

      <NextSteps />
    </div>
  )
}
