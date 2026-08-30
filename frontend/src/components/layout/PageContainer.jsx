export default function PageContainer({ title, subtitle, children }) {
  return (
    <main className="mx-auto max-w-6xl px-6 py-8">
      {(title || subtitle) && (
        <div className="mb-8">
          {title && <h2 className="text-2xl font-semibold tracking-tight text-slate-900">{title}</h2>}
          {subtitle && <p className="mt-1 text-sm text-slate-500">{subtitle}</p>}
        </div>
      )}
      {children}
    </main>
  )
}
