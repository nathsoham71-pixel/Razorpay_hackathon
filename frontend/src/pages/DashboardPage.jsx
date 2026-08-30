import { useCallback, useEffect, useState } from 'react'
import PageContainer from '../components/layout/PageContainer'
import FeedUploadCard from '../components/dashboard/FeedUploadCard'
import MandateSummaryCard from '../components/mandate/MandateSummaryCard'
import { useMerchant } from '../context/MerchantContext'
import { getDashboard } from '../api/demo'

function StatCard({ label, value, mono }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-4 py-3 shadow-sm">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className={`mt-1 text-2xl font-semibold text-slate-900 ${mono ? 'font-mono' : ''}`}>
        {value}
      </p>
    </div>
  )
}

export default function DashboardPage() {
  const { merchantId } = useMerchant()
  const [dashboard, setDashboard] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    if (!merchantId) {
      setDashboard(null)
      return
    }
    setLoading(true)
    setError(null)
    try {
      const data = await getDashboard(merchantId)
      setDashboard(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [merchantId])

  useEffect(() => {
    load()
  }, [load])

  return (
    <PageContainer
      title="Merchant dashboard"
      subtitle="Upload messy CSV feeds and inspect before/after agent-ready translation."
    >
      {error && (
        <p className="mb-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      {merchantId && dashboard && (
        <div className="mb-8 grid gap-4 sm:grid-cols-3">
          <StatCard label="Total products" value={dashboard.product_count} mono />
          <StatCard label="Agent-ready" value={dashboard.agent_ready_count} mono />
          <StatCard
            label="Feed version"
            value={dashboard.latest_feed?.version_number ?? '—'}
            mono
          />
        </div>
      )}

      {dashboard?.active_mandate && (
        <div className="mb-8">
          <MandateSummaryCard mandate={dashboard.active_mandate} />
        </div>
      )}

      <FeedUploadCard merchantId={merchantId} onUploaded={load} />

      {loading && <p className="mt-4 text-sm text-slate-500">Refreshing stats…</p>}
    </PageContainer>
  )
}
