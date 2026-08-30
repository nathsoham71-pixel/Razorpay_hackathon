import { useState } from 'react'
import MandateSummaryCard from './MandateSummaryCard'
import { upsertMandate } from '../../api/demo'

const DEFAULT_LOCKED = ['shipping_address', 'billing_address']

export default function MandateForm({ merchantId, initialMandate, onSaved }) {
  const [maxAmount, setMaxAmount] = useState(
    initialMandate?.max_upsell_amount_inr ?? 500
  )
  const [categories, setCategories] = useState(
    initialMandate?.allowed_categories ?? ['electronics', 'accessories']
  )
  const [categoryInput, setCategoryInput] = useState('')
  const [lockedFields, setLockedFields] = useState(() => {
    const base = new Set([...DEFAULT_LOCKED, ...(initialMandate?.locked_fields || [])])
    return [...base]
  })
  const [customLocked, setCustomLocked] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [saved, setSaved] = useState(initialMandate)

  const addCategory = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      const val = categoryInput.trim().toLowerCase()
      if (val && !categories.includes(val)) setCategories([...categories, val])
      setCategoryInput('')
    }
  }

  const removeCategory = (cat) => setCategories(categories.filter((c) => c !== cat))

  const toggleLocked = (field) => {
    setLockedFields((prev) =>
      prev.includes(field) ? prev.filter((f) => f !== field) : [...prev, field]
    )
  }

  const addCustomLocked = () => {
    const val = customLocked.trim()
    if (val && !lockedFields.includes(val)) setLockedFields([...lockedFields, val])
    setCustomLocked('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!merchantId) return
    setSaving(true)
    setError(null)
    try {
      const data = await upsertMandate(merchantId, {
        max_upsell_amount_inr: Number(maxAmount),
        allowed_categories: categories,
        locked_fields: lockedFields,
      })
      setSaved(data)
      onSaved?.(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  if (!merchantId) {
    return (
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
        Set a merchant ID to configure mandates.
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <form
        onSubmit={handleSubmit}
        className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm"
      >
        <h3 className="text-base font-semibold text-slate-900">Agent spending mandate</h3>
        <p className="mt-1 text-sm text-slate-500">
          Deterministic rules enforced after GPT proposes an upsell — not by the model itself.
        </p>

        <label className="mt-6 block">
          <span className="text-xs font-medium uppercase text-slate-500">Max upsell amount (INR)</span>
          <input
            type="number"
            min="0"
            step="1"
            value={maxAmount}
            onChange={(e) => setMaxAmount(e.target.value)}
            className="mt-1 w-full max-w-xs rounded-md border border-slate-200 px-3 py-2 font-mono text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </label>

        <div className="mt-6">
          <span className="text-xs font-medium uppercase text-slate-500">Allowed categories</span>
          <div className="mt-2 flex flex-wrap gap-2">
            {categories.map((cat) => (
              <span
                key={cat}
                className="inline-flex items-center gap-1 rounded-full bg-indigo-50 px-3 py-1 font-mono text-xs text-indigo-800"
              >
                {cat}
                <button type="button" onClick={() => removeCategory(cat)} className="text-indigo-400 hover:text-indigo-700">
                  ×
                </button>
              </span>
            ))}
          </div>
          <input
            value={categoryInput}
            onChange={(e) => setCategoryInput(e.target.value)}
            onKeyDown={addCategory}
            placeholder="Type category + Enter"
            className="mt-2 w-full max-w-md rounded-md border border-slate-200 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
          />
        </div>

        <div className="mt-6">
          <span className="text-xs font-medium uppercase text-slate-500">Locked fields</span>
          <div className="mt-2 space-y-2">
            {DEFAULT_LOCKED.map((field) => (
              <label key={field} className="flex items-center gap-2 text-sm text-slate-700">
                <input
                  type="checkbox"
                  checked={lockedFields.includes(field)}
                  onChange={() => toggleLocked(field)}
                  className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                />
                <span className="font-mono text-xs">{field}</span>
              </label>
            ))}
            {lockedFields
              .filter((f) => !DEFAULT_LOCKED.includes(f))
              .map((field) => (
                <label key={field} className="flex items-center gap-2 text-sm text-slate-700">
                  <input
                    type="checkbox"
                    checked
                    onChange={() => toggleLocked(field)}
                    className="rounded border-slate-300 text-indigo-600"
                  />
                  <span className="font-mono text-xs">{field}</span>
                </label>
              ))}
          </div>
          <div className="mt-2 flex gap-2">
            <input
              value={customLocked}
              onChange={(e) => setCustomLocked(e.target.value)}
              placeholder="Custom field name"
              className="rounded-md border border-slate-200 px-3 py-1.5 text-sm"
            />
            <button
              type="button"
              onClick={addCustomLocked}
              className="rounded-md border border-slate-200 px-3 py-1.5 text-xs font-medium hover:bg-slate-50"
            >
              Add
            </button>
          </div>
        </div>

        {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={saving}
          className="mt-6 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {saving ? 'Saving…' : 'Save mandate'}
        </button>
      </form>

      {saved && <MandateSummaryCard mandate={saved} />}
    </div>
  )
}
