import { useEffect, useCallback } from 'react'

/**
 * Razorpay Checkout.js — TEST MODE ONLY.
 * Use test card: 4111 1111 1111 1111, any future expiry, any CVV.
 * @see https://razorpay.com/docs/payments/payment-gateway/web-integration/standard/
 */
export default function RazorpayCheckoutButton({
  orderId,
  razorpayOrderId,
  razorpayKeyId,
  amountInr,
  onSuccess,
  onError,
  disabled,
}) {
  useEffect(() => {
    if (document.getElementById('razorpay-checkout-js')) return
    const script = document.createElement('script')
    script.id = 'razorpay-checkout-js'
    script.src = 'https://checkout.razorpay.com/v1/checkout.js'
    script.async = true
    document.body.appendChild(script)
  }, [])

  const openCheckout = useCallback(() => {
    if (!window.Razorpay || !razorpayKeyId || !razorpayOrderId) {
      onError?.('Razorpay not loaded or missing order details')
      return
    }

    const options = {
      key: razorpayKeyId,
      amount: Math.round(amountInr * 100),
      currency: 'INR',
      name: 'Merchant Agent Platform',
      description: 'Test mode purchase',
      order_id: razorpayOrderId,
      handler(response) {
        onSuccess?.({
          razorpay_payment_id: response.razorpay_payment_id,
          razorpay_order_id: response.razorpay_order_id,
          razorpay_signature: response.razorpay_signature,
        })
      },
      modal: {
        ondismiss() {
          onError?.('Payment cancelled')
        },
      },
      theme: { color: '#4f46e5' },
    }

    const rzp = new window.Razorpay(options)
    rzp.on('payment.failed', (resp) => {
      onError?.(resp.error?.description || 'Payment failed')
    })
    rzp.open()
  }, [razorpayKeyId, razorpayOrderId, amountInr, onSuccess, onError])

  if (!orderId) return null

  return (
    <button
      type="button"
      onClick={openCheckout}
      disabled={disabled || !razorpayKeyId}
      className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-slate-800 disabled:opacity-50"
    >
      Pay with Razorpay (test mode)
    </button>
  )
}
