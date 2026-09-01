import { createContext, useContext, useEffect, useState } from 'react'

const MerchantContext = createContext(null)

const STORAGE_KEY = 'demo_merchant_id'
const DEFAULT_MERCHANT_ID = import.meta.env.VITE_DEFAULT_MERCHANT_ID || ''

export function MerchantProvider({ children }) {
  const [merchantId, setMerchantIdState] = useState(
    () => DEFAULT_MERCHANT_ID || localStorage.getItem(STORAGE_KEY) || ''
  )

  const setMerchantId = (id) => {
    setMerchantIdState(id)
    if (id) localStorage.setItem(STORAGE_KEY, id)
    else localStorage.removeItem(STORAGE_KEY)
  }

  return (
    <MerchantContext.Provider value={{ merchantId, setMerchantId }}>
      {children}
    </MerchantContext.Provider>
  )
}

export function useMerchant() {
  const ctx = useContext(MerchantContext)
  if (!ctx) throw new Error('useMerchant must be used within MerchantProvider')
  return ctx
}

export function MerchantSelector() {
  const { merchantId, setMerchantId } = useMerchant()
  const [draft, setDraft] = useState(merchantId)
  const [creating, setCreating] = useState(false)

  useEffect(() => setDraft(merchantId), [merchantId])

  const save = () => setMerchantId(draft.trim())

  const createDemo = async () => {
    setCreating(true)
    try {
      const { createMerchant } = await import('../api/demo')
      const m = await createMerchant('Demo Store', `demo-${Date.now()}@example.com`)
      setMerchantId(m.id)
      setDraft(m.id)
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 shadow-sm">
      <span className="text-xs font-medium uppercase tracking-wide text-slate-500">Merchant ID</span>
      <input
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        placeholder="Paste UUID or create new"
        className="min-w-[280px] flex-1 rounded-md border border-slate-200 px-2 py-1 font-mono text-xs text-slate-800 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
      />
      <button
        type="button"
        onClick={save}
        className="rounded-md bg-slate-800 px-3 py-1 text-xs font-medium text-white hover:bg-slate-700"
      >
        Set
      </button>
      <button
        type="button"
        onClick={createDemo}
        disabled={creating}
        className="rounded-md border border-slate-200 px-3 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
      >
        {creating ? 'Creating…' : 'New merchant'}
      </button>
    </div>
  )
}
