import { useCallback, useEffect, useState } from 'react'
import PageContainer from '../components/layout/PageContainer'
import MandateForm from '../components/mandate/MandateForm'
import { useMerchant } from '../context/MerchantContext'
import { getDashboard } from '../api/demo'

export default function MandatePage() {
  const { merchantId } = useMerchant()
  const [mandate, setMandate] = useState(null)

  const load = useCallback(async () => {
    if (!merchantId) return
    try {
      const data = await getDashboard(merchantId)
      setMandate(data.active_mandate)
    } catch {
      setMandate(null)
    }
  }, [merchantId])

  useEffect(() => {
    load()
  }, [load])

  return (
    <PageContainer
      title="Mandate configuration"
      subtitle="Set deterministic spending bounds — enforced by Python after GPT proposes upsells."
    >
      <MandateForm merchantId={merchantId} initialMandate={mandate} onSaved={setMandate} />
    </PageContainer>
  )
}
