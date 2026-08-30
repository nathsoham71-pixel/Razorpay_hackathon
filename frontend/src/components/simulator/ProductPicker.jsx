export default function ProductPicker({ products, selected, quantity, onSelect, onQuantityChange }) {
  if (!products?.length) {
    return (
      <p className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">
        No agent-ready products. Upload a feed on the Dashboard first.
      </p>
    )
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-900">Select base product</h3>
      <div className="mt-3 space-y-2">
        {products.map((p) => (
          <label
            key={p.id}
            className={`flex cursor-pointer items-center gap-3 rounded-md border px-3 py-2 transition ${
              selected === p.id
                ? 'border-indigo-500 bg-indigo-50'
                : 'border-slate-200 hover:border-slate-300'
            }`}
          >
            <input
              type="radio"
              name="product"
              checked={selected === p.id}
              onChange={() => onSelect(p.id)}
              className="text-indigo-600"
            />
            <div className="flex-1">
              <p className="text-sm font-medium text-slate-900">{p.title}</p>
              <p className="font-mono text-xs text-slate-500">
                {p.sku} · ₹{p.price_inr} · {p.category} · stock {p.stock_quantity}
              </p>
            </div>
          </label>
        ))}
      </div>
      <label className="mt-4 block text-sm text-slate-600">
        Quantity
        <input
          type="number"
          min="1"
          value={quantity}
          onChange={(e) => onQuantityChange(Number(e.target.value) || 1)}
          className="ml-2 w-20 rounded-md border border-slate-200 px-2 py-1 font-mono text-sm"
        />
      </label>
    </div>
  )
}
