import { useState } from 'react'
import ValidationErrorList from './ValidationErrorList'
import BeforeAfterDiff from './BeforeAfterDiff'

export default function FeedUploadCard({ merchantId, onUploaded }) {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  const handleUpload = async () => {
    if (!file || !merchantId) return
    setLoading(true)
    setError(null)
    try {
      const { uploadFeed } = await import('../../api/demo')
      const data = await uploadFeed(merchantId, file)
      setResult(data)
      onUploaded?.(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (!merchantId) {
    return (
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
        Set a merchant ID in the header to upload a feed.
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <h3 className="text-base font-semibold text-slate-900">Upload product feed (CSV)</h3>
      <p className="mt-1 text-sm text-slate-500">
        Uses Phase 1 route — same translator the MCP catalog tools read.
      </p>
      <div className="mt-4 flex flex-wrap items-center gap-3">
        <input
          type="file"
          accept=".csv"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="text-sm text-slate-600 file:mr-3 file:rounded-md file:border-0 file:bg-slate-100 file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-slate-700 hover:file:bg-slate-200"
        />
        <button
          type="button"
          onClick={handleUpload}
          disabled={!file || loading}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50"
        >
          {loading ? 'Uploading…' : 'Upload & translate'}
        </button>
      </div>
      {error && (
        <p className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}
      {result && (
        <div className="mt-6 space-y-4">
          <BeforeAfterDiff samples={result.before_after_report?.samples || []} />
          <ValidationErrorList errors={result.before_after_report?.validation_errors_preview || []} />
        </div>
      )}
    </div>
  )
}
