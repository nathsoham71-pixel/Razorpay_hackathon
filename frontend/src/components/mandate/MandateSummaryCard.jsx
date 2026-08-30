export default function MandateSummaryCard({ mandate }) {
  if (!mandate) return null

  const cats = (mandate.allowed_categories || []).join(', ') || 'none'
  const locked = (mandate.locked_fields || []).join(', ') || 'none'

  return (
    <div className="rounded-lg border-2 border-indigo-200 bg-indigo-50/50 p-5 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">Active mandate</p>
      <p className="mt-2 text-sm text-slate-800">
        Agents may add up to{' '}
        <span className="font-mono font-semibold text-indigo-700">
          ₹{mandate.max_upsell_amount_inr}
        </span>{' '}
        in <span className="font-mono">[{cats}]</span>.
      </p>
      <p className="mt-1 text-sm text-slate-600">
        Cannot modify: <span className="font-mono text-slate-800">{locked}</span>
      </p>
    </div>
  )
}
