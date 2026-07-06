import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, Upload, FileUp } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function UploadsPage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto space-y-12 pb-16">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Upload className="w-4 h-4 animate-bounce" />
          Request / File Uploads
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            File Uploads
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia handles multipart file uploads natively via <DocTerm id="reqres.uploadfile">UploadFile</DocTerm> and <DocTerm id="reqres.formdata">FormData</DocTerm> objects, providing automatic disk-spilling and sanitization mechanisms to keep memory usage bounded.
        </p>
      </div>

      {/* UploadFile */}
      <section className="space-y-4">
        <div className="flex items-center gap-3">
          <FileUp className="w-6 h-6 text-aquilia-500" />
          <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>UploadFile</h2>
        </div>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Representing a single uploaded file. It operates in two modes: in-memory (for files smaller than the threshold) and on-disk (temporary files for large payloads).
        </p>

        <h3 className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>API Fields</h3>
        <div className="overflow-x-auto py-2">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400">
                <th className="text-left py-3 px-4 font-semibold">Field</th>
                <th className="text-left py-3 px-4 font-semibold">Type</th>
                <th className="text-left py-3 px-4 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5 text-gray-300' : 'divide-gray-100 text-gray-700'}`}>
              {[
                { f: 'filename', t: 'str', d: 'The sanitized filename uploaded by the client.' },
                { f: 'content_type', t: 'str', d: 'MIME content type of the file (e.g. image/png).' },
                { f: 'size', t: 'int | None', d: 'The size of the file in bytes.' }
              ].map((row, i) => (
                <tr key={i} className="hover:bg-aquilia-500/5 transition-colors">
                  <td className="py-3 px-4"><code className="text-aquilia-500 font-mono text-xs">{row.f}</code></td>
                  <td className="py-3 px-4 font-mono text-xs">{row.t}</td>
                  <td className="py-3 px-4 text-xs">{row.d}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <CodeBlock language="python" filename="upload_file_methods.py">{`# Read file content (in-memory or streamed from disk)
content: bytes = await upload.read()

# Stream chunks (useful for large files to avoid memory overhead)
async for chunk in upload.stream():
    await process(chunk)

# Save to destination path on disk
saved_path = await upload.save("/dest/path/image.png", overwrite=True)`}</CodeBlock>
      </section>

      {/* FormData */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>FormData</h2>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The parsed representation of form fields and files.
        </p>

        <div className="overflow-x-auto py-2">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400">
                <th className="text-left py-3 px-4 font-semibold">Method</th>
                <th className="text-left py-3 px-4 font-semibold">Returns</th>
                <th className="text-left py-3 px-4 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5 text-gray-300' : 'divide-gray-100 text-gray-700'}`}>
              {[
                { m: 'get(name)', t: 'str | UploadFile | None', d: 'Gets first form field or file match.' },
                { m: 'get_field(name)', t: 'str | None', d: 'Gets first value of a text field.' },
                { m: 'get_file(name)', t: 'UploadFile | None', d: 'Gets first UploadFile instance.' },
                { m: 'cleanup()', t: 'async None', d: 'Deletes temporary file handles and clears memory.' }
              ].map((row, i) => (
                <tr key={i} className="hover:bg-aquilia-500/5 transition-colors">
                  <td className="py-3 px-4"><code className="text-aquilia-500 font-mono text-xs">{row.m}</code></td>
                  <td className="py-3 px-4 font-mono text-xs">{row.t}</td>
                  <td className="py-3 px-4 text-xs">{row.d}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Navigation */}
      <div className="flex justify-between items-center mt-16 pt-8 border-t border-gray-200 dark:border-white/10">
        <Link to="/docs/request-response/data-structures" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition-colors">
          <ArrowLeft className="w-4 h-4" />
          <span>Data Structures</span>
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}