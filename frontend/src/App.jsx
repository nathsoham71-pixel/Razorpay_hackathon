import { useEffect, useState, useCallback } from 'react'
import './App.css'

// In dev, Vite's proxy (vite.config.js) forwards "/api" to your FastAPI
// backend on :8000. In production, set VITE_API_BASE_URL to your deployed
// backend's URL (e.g. your Render URL).
const BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

async function apiRequest(path, options = {}) {
  const res = await fetch(`${BASE_URL}/api${path}`, {
    ...options,
    headers: {
      ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
      ...options.headers,
    },
  })
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}))
    throw new Error(detail.detail || `Request failed (${res.status})`)
  }
  const text = await res.text()
  return text ? JSON.parse(text) : null
}

const api = {
  listProducts: () => apiRequest('/products'),
  createProduct: (formData) => apiRequest('/products', { method: 'POST', body: formData }),
  updateStock: (id, stock) =>
    apiRequest(`/products/${id}/stock`, { method: 'PATCH', body: JSON.stringify({ stock }) }),
  deleteProduct: (id) => apiRequest(`/products/${id}`, { method: 'DELETE' }),
}

function App() {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [formOpen, setFormOpen] = useState(false)

  const loadProducts = useCallback(async () => {
    try {
      setError(null)
      const data = await api.listProducts()
      setProducts(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadProducts()
  }, [loadProducts])

  const handleCreated = (product) => {
    setProducts((prev) => [product, ...prev])
    setFormOpen(false)
  }

  const handleStockChange = async (id, newStock) => {
    setProducts((prev) => prev.map((p) => (p.id === id ? { ...p, stock: newStock } : p)))
    try {
      await api.updateStock(id, newStock)
    } catch (err) {
      setError(err.message)
      loadProducts()
    }
  }

  const handleDelete = async (id) => {
    const prevProducts = products
    setProducts((prev) => prev.filter((p) => p.id !== id))
    try {
      await api.deleteProduct(id)
    } catch (err) {
      setError(err.message)
      setProducts(prevProducts)
    }
  }

  return (
    <div className="min-h-screen bg-[#FAFAF8]">
      <header className="border-b border-[#E4E4E0] bg-[#FAFAF8]/95 backdrop-blur sticky top-0 z-10">
  <div className="mx-auto max-w-5xl px-6 py-5">
    <p className="font-mono text-xs uppercase tracking-widest text-[#6B6D72]">
      Merchant console
    </p>
    <h1 className="text-2xl font-semibold text-[#16181D] mt-0.5" style={{ fontFamily: "'Instrument Sans', sans-serif" }}>
      Your catalog
    </h1>
  </div>
</header>

      <main className="mx-auto max-w-5xl px-6 py-8">
        {error && (
          <div className="mb-6 rounded-md border border-[#B4472B]/30 bg-[#B4472B]/5 px-4 py-3 text-sm text-[#B4472B]">
            {error}
          </div>
        )}

        {loading ? (
          <p className="text-sm text-[#6B6D72]">Loading catalog…</p>
        ) : products.length === 0 ? (
          <EmptyState onAdd={() => setFormOpen(true)} />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {products.map((product) => (
              <ProductCard
                key={product.id}
                product={product}
                onStockChange={handleStockChange}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}
      </main>

      {formOpen && <ProductForm onClose={() => setFormOpen(false)} onCreated={handleCreated} />}
    </div>
  )
}

function ProductCard({ product, onStockChange, onDelete }) {
  const [editingStock, setEditingStock] = useState(false)
  const [draftStock, setDraftStock] = useState(product.stock)

  const commitStock = () => {
    const value = Math.max(0, parseInt(draftStock, 10) || 0)
    onStockChange(product.id, value)
    setEditingStock(false)
  }

  const stepStock = (delta) => {
    onStockChange(product.id, Math.max(0, product.stock + delta))
  }

  const isOut = product.stock === 0
  const isLow = product.stock > 0 && product.stock <= 3

  return (
    <div className="group rounded-lg border border-[#E4E4E0] bg-white overflow-hidden flex flex-col">
      <div className="aspect-[4/3] bg-[#F1F0EC] relative overflow-hidden">
        {product.image_url ? (
          <img src={`${BASE_URL}${product.image_url}`} alt={product.name} className="h-full w-full object-cover" />
        ) : (
          <div className="h-full w-full flex items-center justify-center text-[#6B6D72]">
            <ImagePlaceholderIcon />
          </div>
        )}
        <StockBadge stock={product.stock} isOut={isOut} isLow={isLow} />
      </div>

      <div className="p-4 flex flex-col gap-2 flex-1">
        <h3 className="font-semibold text-[#16181D] leading-snug" style={{ fontFamily: "'Instrument Sans', sans-serif" }}>
          {product.name}
        </h3>
        <p className="text-sm text-[#6B6D72] line-clamp-2 flex-1">
          {product.description || 'No description added.'}
        </p>

        <div className="mt-2 flex items-center justify-between border-t border-[#E4E4E0] pt-3">
          <div className="flex items-center gap-1.5">
            <button
              onClick={() => stepStock(-1)}
              disabled={product.stock === 0}
              className="focus-ring h-7 w-7 rounded-md border border-[#E4E4E0] text-[#16181D] disabled:opacity-30 hover:bg-[#F1F0EC] transition"
              aria-label="Decrease stock"
            >
              −
            </button>

            {editingStock ? (
              <input
                autoFocus
                type="number"
                min="0"
                value={draftStock}
                onChange={(e) => setDraftStock(e.target.value)}
                onBlur={commitStock}
                onKeyDown={(e) => e.key === 'Enter' && commitStock()}
                className="stock-input focus-ring w-14 rounded-md border border-[#E4E4E0] text-center text-sm py-1"
              />
            ) : (
              <button
                onClick={() => {
                  setDraftStock(product.stock)
                  setEditingStock(true)
                }}
                className="w-14 rounded-md text-center text-sm font-mono py-1 hover:bg-[#F1F0EC] transition"
                title="Click to set an exact count"
              >
                {product.stock}
              </button>
            )}

            <button
              onClick={() => stepStock(1)}
              className="focus-ring h-7 w-7 rounded-md border border-[#E4E4E0] text-[#16181D] hover:bg-[#F1F0EC] transition"
              aria-label="Increase stock"
            >
              +
            </button>
          </div>

          <button
            onClick={() => onDelete(product.id)}
            className="focus-ring text-xs text-[#6B6D72] hover:text-[#B4472B] transition opacity-0 group-hover:opacity-100"
          >
            Remove
          </button>
        </div>
      </div>
    </div>
  )
}

function StockBadge({ stock, isOut, isLow }) {
  const label = isOut ? 'Out of stock' : isLow ? `Only ${stock} left` : `${stock} in stock`
  const styles = isOut
    ? 'bg-[#B4472B]/90 text-white'
    : isLow
    ? 'bg-[#B4472B]/10 text-[#B4472B] border border-[#B4472B]/20'
    : 'bg-white/90 text-[#16181D] border border-[#E4E4E0]'

  return (
    <span className={`absolute top-2.5 left-2.5 rounded-full px-2.5 py-1 text-[11px] font-mono font-medium ${styles}`}>
      {label}
    </span>
  )
}

function EmptyState({ onAdd }) {
  return (
    <div className="rounded-lg border border-dashed border-[#E4E4E0] py-20 text-center">
      <p className="text-lg font-semibold text-[#16181D]" style={{ fontFamily: "'Instrument Sans', sans-serif" }}>
        No items listed yet
      </p>
      <p className="mt-1 text-sm text-[#6B6D72]">Add your first product to make it visible in your catalog.</p>
      <button
        onClick={onAdd}
        className="focus-ring mt-5 inline-flex items-center gap-2 rounded-md bg-[#16181D] px-4 py-2.5 text-sm font-medium text-[#FAFAF8] transition hover:bg-[#16181D]/85"
      >
        <PlusIcon />
        Add item
      </button>
    </div>
  )
}

function ProductForm({ onClose, onCreated }) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [stock, setStock] = useState('1')
  const [imageFile, setImageFile] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const handleImageChange = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setImageFile(file)
    setImagePreview(URL.createObjectURL(file))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!name.trim()) {
      setError('Give the product a name.')
      return
    }
    setSubmitting(true)
    setError(null)
    try {
      const formData = new FormData()
      formData.append('name', name.trim())
      formData.append('description', description.trim())
      formData.append('stock', String(Math.max(0, parseInt(stock, 10) || 0)))
      if (imageFile) formData.append('image', imageFile)

      const created = await api.createProduct(formData)
      onCreated(created)
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-20 flex items-center justify-center bg-[#16181D]/40 px-4"
      onMouseDown={(e) => e.target === e.currentTarget && onClose()}
    >
      <div role="dialog" aria-modal="true" aria-labelledby="add-item-title" className="w-full max-w-md rounded-lg bg-white border border-[#E4E4E0] shadow-xl">
        <div className="flex items-center justify-between border-b border-[#E4E4E0] px-5 py-4">
          <h2 id="add-item-title" className="font-semibold text-[#16181D]" style={{ fontFamily: "'Instrument Sans', sans-serif" }}>
            Add item
          </h2>
          <button onClick={onClose} className="focus-ring rounded-md p-1 text-[#6B6D72] hover:text-[#16181D] transition" aria-label="Close">
            <CloseIcon />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="px-5 py-5 flex flex-col gap-4">
          <Field label="Name">
            <input
              autoFocus
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Handwoven cotton kurta"
              className="focus-ring w-full rounded-md border border-[#E4E4E0] px-3 py-2 text-sm"
            />
          </Field>

          <Field label="Description">
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Materials, sizing, care notes — whatever a buyer would want to know"
              rows={3}
              className="focus-ring w-full resize-none rounded-md border border-[#E4E4E0] px-3 py-2 text-sm"
            />
          </Field>

          <Field label="Stock to sell">
            <input
              type="number"
              min="0"
              value={stock}
              onChange={(e) => setStock(e.target.value)}
              className="stock-input focus-ring w-28 rounded-md border border-[#E4E4E0] px-3 py-2 text-sm"
            />
          </Field>

          <Field label="Image">
            <label className="focus-ring flex items-center gap-3 rounded-md border border-dashed border-[#E4E4E0] px-3 py-2.5 text-sm text-[#6B6D72] cursor-pointer hover:border-[#2F6F4E]/50 transition">
              {imagePreview ? (
                <img src={imagePreview} alt="Preview" className="h-10 w-10 rounded object-cover" />
              ) : (
                <span className="h-10 w-10 rounded bg-[#F1F0EC] flex items-center justify-center text-[#6B6D72]">
                  <ImageIcon />
                </span>
              )}
              <span>{imageFile ? imageFile.name : 'Choose a photo'}</span>
              <input type="file" accept="image/*" onChange={handleImageChange} className="hidden" />
            </label>
          </Field>

          {error && <p className="text-sm text-[#B4472B]">{error}</p>}

          <div className="mt-1 flex items-center justify-end gap-2">
            <button type="button" onClick={onClose} className="focus-ring rounded-md px-4 py-2 text-sm text-[#6B6D72] hover:text-[#16181D] transition">
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="focus-ring rounded-md bg-[#2F6F4E] px-4 py-2 text-sm font-medium text-white transition hover:bg-[#245A3E] disabled:opacity-60"
            >
              {submitting ? 'Adding…' : 'Add item'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function Field({ label, children }) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-xs font-medium uppercase tracking-wide text-[#6B6D72]">{label}</span>
      {children}
    </label>
  )
}

function PlusIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path d="M8 3v10M3 8h10" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
    </svg>
  )
}

function CloseIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
      <path d="M4 4l10 10M14 4L4 14" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  )
}

function ImageIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
      <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" strokeWidth="1.4" />
      <circle cx="8.5" cy="8.5" r="1.5" stroke="currentColor" strokeWidth="1.4" />
      <path d="M21 15l-5-5-9 9" stroke="currentColor" strokeWidth="1.4" />
    </svg>
  )
}

function ImagePlaceholderIcon() {
  return (
    <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
      <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" strokeWidth="1.4" />
      <circle cx="8.5" cy="8.5" r="1.5" stroke="currentColor" strokeWidth="1.4" />
      <path d="M21 15l-5-5-9 9" stroke="currentColor" strokeWidth="1.4" />
    </svg>
  )
}

export default App