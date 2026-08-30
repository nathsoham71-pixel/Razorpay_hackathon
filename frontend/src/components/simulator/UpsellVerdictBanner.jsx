const REASON_LABELS = {
  exceeds_spend_limit: "This item exceeds the agent's spending limit.",
  category_not_allowed: "This category isn't covered by the current mandate.",
  locked_field_violation: "This would change a field the agent isn't allowed to touch.",
  no_active_mandate: 'No active spending mandate is configured for this merchant.',
}

export default function UpsellVerdictBanner({ verdict }) {
  if (!verdict?.upsell_status || verdict.upsell_status === 'none_proposed') return null

  if (verdict.upsell_status === 'approved') {
    const item = verdict.new_item || {}
    return (
      <div
        role="status"
        className="mt-3 rounded-lg border-2 border-green-600 bg-green-50 px-4 py-3 shadow-sm"
      >
        <p className="flex items-center gap-2 text-sm font-bold text-green-800">
          <span className="text-lg">✓</span>
          Upsell approved — added {item.title || item.sku} for ₹
          {item.unit_price_inr ?? '?'}. New total: ₹{verdict.new_total_inr}
        </p>
      </div>
    )
  }

  if (verdict.upsell_status === 'rejected') {
    const reason =
      REASON_LABELS[verdict.rejection_reason] || verdict.rejection_reason || 'Blocked by mandate.'
    return (
      <div
        role="alert"
        className="mt-3 rounded-lg border-2 border-amber-600 bg-amber-50 px-4 py-3 shadow-sm"
      >
        <p className="flex items-center gap-2 text-sm font-bold text-amber-900">
          <span className="text-lg">✗</span>
          Upsell blocked by mandate — {reason}
        </p>
        {verdict.max_allowed_inr != null && (
          <p className="mt-1 font-mono text-xs text-amber-800">Limit: ₹{verdict.max_allowed_inr}</p>
        )}
      </div>
    )
  }

  return null
}
