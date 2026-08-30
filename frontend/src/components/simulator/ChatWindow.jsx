import { useState } from 'react'
import UpsellVerdictBanner from './UpsellVerdictBanner'

export default function ChatWindow({ messages, onSend, sending }) {
  const [input, setInput] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!input.trim() || sending) return
    onSend(input.trim())
    setInput('')
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 px-4 py-3">
        <h3 className="text-sm font-semibold text-slate-900">Merchant agent chat (upsell demo)</h3>
        <p className="text-xs text-slate-500">GPT proposes · Python mandate engine approves or rejects</p>
      </div>
      <div className="flex max-h-96 flex-col gap-3 overflow-y-auto p-4">
        {messages.length === 0 && (
          <p className="text-center text-sm text-slate-400">
            Ask for accessory suggestions — try an expensive item to trigger a rejection.
          </p>
        )}
        {messages.map((msg, i) => (
          <div key={i}>
            <div
              className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                msg.role === 'user'
                  ? 'ml-auto bg-slate-800 text-white'
                  : 'mr-auto border border-slate-200 bg-slate-50 text-slate-800'
              }`}
            >
              {msg.content}
            </div>
            {msg.verdict && <UpsellVerdictBanner verdict={msg.verdict} />}
          </div>
        ))}
      </div>
      <form onSubmit={handleSubmit} className="flex gap-2 border-t border-slate-200 p-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="e.g. Can you add a desk lamp to my order?"
          className="flex-1 rounded-md border border-slate-200 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
          disabled={sending}
        />
        <button
          type="submit"
          disabled={sending || !input.trim()}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {sending ? '…' : 'Send'}
        </button>
      </form>
    </div>
  )
}
