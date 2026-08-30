export default function ValidationErrorList({ errors }) {
  if (!errors?.length) return null

  return (
    <div className="rounded-lg border-2 border-red-200 bg-red-50 p-4">
      <h4 className="text-sm font-semibold text-red-800">Validation errors ({errors.length} shown)</h4>
      <ul className="mt-2 space-y-1">
        {errors.map((err, i) => (
          <li key={i} className="font-mono text-xs text-red-700">
            Row {err.row}: [{err.field}] {err.issue}
          </li>
        ))}
      </ul>
    </div>
  )
}
