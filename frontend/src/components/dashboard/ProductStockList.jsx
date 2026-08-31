export default function ProductStockList({ products, loading }) {
  if (loading) {
    return <p className="text-sm text-slate-500">Loading stock…</p>
  }

  if (!products?.length) {
    return (
      <p className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">
        No products yet. Upload a CSV feed to populate stock.
      </p>
    )
  }

  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 px-4 py-3">
        <h3 className="text-sm font-semibold text-slate-900">Product stock</h3>
        <p className="mt-0.5 text-xs text-slate-500">Units available per SKU</p>
      </div>
      <table className="w-full text-left text-sm">
        <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-4 py-2 font-medium">Product</th>
            <th className="px-4 py-2 font-medium">SKU</th>
            <th className="px-4 py-2 font-medium">Category</th>
            <th className="px-4 py-2 font-medium text-right">Price</th>
            <th className="px-4 py-2 font-medium text-right">Stock</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {products.map((p) => (
            <tr key={p.id} className="text-slate-800">
              <td className="px-4 py-2.5 font-medium">{p.title}</td>
              <td className="px-4 py-2.5 font-mono text-xs text-slate-600">{p.sku}</td>
              <td className="px-4 py-2.5 text-slate-600">{p.category || '—'}</td>
              <td className="px-4 py-2.5 text-right font-mono">₹{Number(p.price_inr).toFixed(0)}</td>
              <td className="px-4 py-2.5 text-right">
                <span
                  className={`inline-block min-w-[2rem] font-mono font-semibold ${
                    p.stock_quantity <= 0
                      ? 'text-red-600'
                      : p.stock_quantity < 10
                        ? 'text-amber-600'
                        : 'text-slate-900'
                  }`}
                >
                  {p.stock_quantity}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
