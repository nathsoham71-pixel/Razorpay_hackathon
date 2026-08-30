import { useCallback, useEffect, useState } from 'react'
import PageContainer from '../components/layout/PageContainer'
import ProductPicker from '../components/simulator/ProductPicker'
import CartSummary from '../components/simulator/CartSummary'
import ChatWindow from '../components/simulator/ChatWindow'
import RazorpayCheckoutButton from '../components/simulator/RazorpayCheckoutButton'
import { useMerchant } from '../context/MerchantContext'
import {
  confirmPurchase,
  listProducts,
  simulatePurchase,
  simulateUpsellChat,
} from '../api/demo'

export default function SimulatorPage() {
  const { merchantId } = useMerchant()
  const [products, setProducts] = useState([])
  const [selectedId, setSelectedId] = useState('')
  const [quantity, setQuantity] = useState(1)
  const [order, setOrder] = useState(null)
  const [messages, setMessages] = useState([])
  const [history, setHistory] = useState([])
  const [chatSending, setChatSending] = useState(false)
  const [purchaseLoading, setPurchaseLoading] = useState(false)
  const [paymentStatus, setPaymentStatus] = useState(null)
  const [error, setError] = useState(null)

  const selectedProduct = products.find((p) => p.id === selectedId)

  const loadProducts = useCallback(async () => {
    if (!merchantId) return
    try {
      const data = await listProducts(merchantId, true)
      setProducts(data)
      if (data.length && !selectedId) setSelectedId(data[0].id)
    } catch (err) {
      setError(err.message)
    }
  }, [merchantId, selectedId])

  useEffect(() => {
    loadProducts()
  }, [loadProducts])

  const startPurchase = async () => {
    if (!merchantId || !selectedId) return
    setPurchaseLoading(true)
    setError(null)
    setPaymentStatus(null)
    try {
      const result = await simulatePurchase(merchantId, [
        { product_id: selectedId, quantity },
      ])
      setOrder(result)
      setMessages([])
      setHistory([])
    } catch (err) {
      setError(err.message)
    } finally {
      setPurchaseLoading(false)
    }
  }

  const handleChat = async (buyerMessage) => {
    if (!order?.order_id) return
    setChatSending(true)
    setError(null)

    const userMsg = { role: 'user', content: buyerMessage }
    setMessages((prev) => [...prev, userMsg])

    try {
      const result = await simulateUpsellChat(order.order_id, buyerMessage, history)
      const agentMsg = {
        role: 'assistant',
        content: result.reply_text,
        verdict: result.upsell_status !== 'none_proposed' ? result : null,
      }
      setMessages((prev) => [...prev, agentMsg])

      const newHistory = [
        ...history,
        { role: 'user', content: buyerMessage },
        { role: 'assistant', content: result.reply_text },
      ]
      setHistory(newHistory)

      if (result.upsell_status === 'approved') {
        setOrder((prev) => ({
          ...prev,
          amount_inr: result.new_total_inr,
          razorpay_order_id: result.razorpay_order_id || prev.razorpay_order_id,
        }))
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setChatSending(false)
    }
  }

  const handlePaymentSuccess = async (payment) => {
    try {
      const result = await confirmPurchase(
        order.order_id,
        payment.razorpay_payment_id,
        payment.razorpay_signature
      )
      setPaymentStatus(`Payment confirmed — status: ${result.status}`)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <PageContainer
      title="Buyer agent simulator"
      subtitle="Simulate a bounded client agent: purchase, chat for upsells, watch mandate enforcement live."
    >
      {!merchantId && (
        <p className="mb-4 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          Set a merchant ID in the header. Upload a feed and configure a mandate first.
        </p>
      )}

      {error && (
        <p className="mb-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          <ProductPicker
            products={products}
            selected={selectedId}
            quantity={quantity}
            onSelect={setSelectedId}
            onQuantityChange={setQuantity}
          />
          <CartSummary
            product={selectedProduct}
            quantity={quantity}
            totalInr={order?.amount_inr}
            orderId={order?.order_id}
          />
          {!order && (
            <button
              type="button"
              onClick={startPurchase}
              disabled={!selectedId || purchaseLoading || !merchantId}
              className="w-full rounded-md bg-indigo-600 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50"
            >
              {purchaseLoading ? 'Creating order…' : 'Start purchase'}
            </button>
          )}
          {order && (
            <div className="flex flex-wrap items-center gap-3 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
              <RazorpayCheckoutButton
                orderId={order.order_id}
                razorpayOrderId={order.razorpay_order_id}
                razorpayKeyId={order.razorpay_key_id}
                amountInr={order.amount_inr}
                onSuccess={handlePaymentSuccess}
                onError={(msg) => setError(msg)}
              />
              {paymentStatus && (
                <span className="text-sm font-medium text-green-700">{paymentStatus}</span>
              )}
            </div>
          )}
        </div>

        <div>
          {order ? (
            <ChatWindow messages={messages} onSend={handleChat} sending={chatSending} />
          ) : (
            <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-sm text-slate-500">
              Start a purchase to enable upsell chat (available while order status is{' '}
              <span className="font-mono">created</span> — before or after payment).
            </div>
          )}
        </div>
      </div>
    </PageContainer>
  )
}
