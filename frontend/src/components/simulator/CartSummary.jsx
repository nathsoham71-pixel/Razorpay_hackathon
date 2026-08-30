export default function CartSummary({ product, quantity, totalInr, orderId }) {
  if (!product) return null

  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 font-mono text-sm shadow-sm">
      <p className="text-xs uppercase tracking-wide text-slate-500">Cart</p>
      <p className="mt-1 text-slate-900">
        {quantity}× {product.title} — ₹{Number(product.price_inr) * quantity}
      </p>
      {totalInr != null && (
        <p className="mt-2 font-semibold text-indigo-700">Order total: ₹{totalInr}</p>
      )}
      {orderId && (
        <p className="mt-1 truncate text-xs text-slate-500">Order: {orderId}</p>
      )}
    </div>
  )
}
