function KeyValueTable({ data, title }) {
  if (!data || typeof data !== 'object') {
    return <p className="text-xs text-slate-400">No data</p>
  }
  return (
    <div>
      {title && <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</p>}
      <dl className="space-y-1">
        {Object.entries(data).map(([key, value]) => (
          <div key={key} className="flex gap-2 text-xs">
            <dt className="w-28 shrink-0 font-mono text-slate-500">{key}</dt>
            <dd className="font-mono text-slate-800 break-all">
              {typeof value === 'object' ? JSON.stringify(value) : String(value ?? '')}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  )
}

export default function BeforeAfterDiff({ samples }) {
  if (!samples?.length) {
    return (
      <p className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">
        No before/after samples in this upload.
      </p>
    )
  }

  return (
    <div className="space-y-4">
      <h4 className="text-sm font-semibold text-slate-900">Before / After translation</h4>
      {samples.map((sample, idx) => (
        <div
          key={idx}
          className="grid gap-4 rounded-lg border border-slate-200 bg-slate-50/50 p-4 md:grid-cols-2"
        >
          <div className="rounded-md border border-red-100 bg-white p-3 shadow-sm">
            <p className="mb-2 text-xs font-semibold uppercase text-red-600">Raw CSV row</p>
            <KeyValueTable data={sample.raw} />
          </div>
          <div className="rounded-md border border-green-100 bg-white p-3 shadow-sm">
            <p className="mb-2 text-xs font-semibold uppercase text-green-600">ACP / translated</p>
            <KeyValueTable data={sample.translated} />
          </div>
        </div>
      ))}
    </div>
  )
}
