import { useState, useRef, useEffect } from 'react';
import { ask, getShipments } from '../api';
import type { OptimizationResult, Shipment } from '../types';

interface AssistantProps {
  result: OptimizationResult | null;
  selectedShipment: Shipment | null;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

const STARTER_QUESTIONS = [
  'Why was this route recommended?',
  'What is the cheapest alternative?',
  'How does risk affect the selection?',
  'Which routes are Pareto-dominant?',
  'What if I prioritize transit time?',
];

export default function Assistant({ result, selectedShipment }: AssistantProps) {
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [selectedId, setSelectedId] = useState<string>('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getShipments().then((s) => {
      setShipments(s);
      const id = selectedShipment?.shipment_id ?? s[0]?.shipment_id;
      if (id) setSelectedId(id);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (question?: string) => {
    const q = question ?? input.trim();
    if (!q || loading) return;

    const userMsg: Message = { role: 'user', content: q };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const answer = await ask(q, selectedId || undefined, { cost: 0.4, time: 0.3, risk: 0.3 });
      setMessages((prev) => [...prev, { role: 'assistant', content: answer }]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `Error: ${err.message ?? 'Something went wrong'}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <div className="mb-6 flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#F1F5F9]">AI Assistant</h1>
          <p className="text-sm text-[#93A4B8] mt-1">
            Ask questions grounded in actual optimization results.
          </p>
        </div>
        <select
          className="input-field w-auto"
          value={selectedId}
          onChange={(e) => setSelectedId(e.target.value)}
        >
          {shipments.map((s) => (
            <option key={s.shipment_id} value={s.shipment_id}>
              {s.shipment_id} — {s.origin} → {s.destination}
            </option>
          ))}
        </select>
      </div>

      {/* Chat window */}
      <div className="card p-0 overflow-hidden flex flex-col" style={{ height: '60vh' }}>
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-10">
              <div className="w-12 h-12 rounded-xl bg-[#21D4C2]/10 border border-[#21D4C2]/20 flex items-center justify-center mx-auto mb-3">
                <svg width="22" height="22" fill="none" viewBox="0 0 24 24">
                  <path d="M12 2L9.5 9H2l5.5 4.5L5.5 21 12 16l6.5 5-2-7.5L22 9h-7.5L12 2Z" stroke="#21D4C2" strokeWidth="1.5" strokeLinecap="round"/>
                </svg>
              </div>
              <p className="text-sm text-[#93A4B8] mb-4">
                Ask me anything about route optimization results
              </p>
              <div className="flex flex-wrap gap-2 justify-center">
                {STARTER_QUESTIONS.map((q) => (
                  <button
                    key={q}
                    onClick={() => sendMessage(q)}
                    className="px-3 py-1.5 rounded-full bg-[#14263B] border border-[#22344A] hover:border-[#21D4C2]/40 text-xs text-[#93A4B8] hover:text-[#21D4C2] transition-all"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-[#21D4C2] text-[#07111F] font-medium'
                    : 'bg-[#14263B] border border-[#22344A] text-[#93A4B8]'
                }`}
              >
                {msg.role === 'assistant' && (
                  <div className="flex items-center gap-1.5 mb-2">
                    <div className="w-4 h-4 rounded bg-[#21D4C2]/20 flex items-center justify-center">
                      <svg width="10" height="10" fill="none" viewBox="0 0 24 24">
                        <path d="M12 2L9.5 9H2l5.5 4.5L5.5 21 12 16l6.5 5-2-7.5L22 9h-7.5L12 2Z" stroke="#21D4C2" strokeWidth="2"/>
                      </svg>
                    </div>
                    <span className="text-[10px] font-semibold text-[#21D4C2]">RouteWise AI</span>
                  </div>
                )}
                {msg.content}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-[#14263B] border border-[#22344A] rounded-2xl px-4 py-3 flex items-center gap-2">
                {[0, 1, 2].map((i) => (
                  <div
                    key={i}
                    className="w-1.5 h-1.5 rounded-full bg-[#21D4C2] animate-bounce"
                    style={{ animationDelay: `${i * 0.15}s` }}
                  />
                ))}
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="border-t border-[#22344A] p-4">
          <div className="flex items-end gap-3">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKey}
              rows={2}
              placeholder="Ask about cost, time, risk, route selection…"
              className="flex-1 bg-[#0A1626] border border-[#22344A] rounded-xl px-4 py-2.5 text-sm text-[#F1F5F9] placeholder:text-[#4A5568] focus:outline-none focus:border-[#21D4C2] resize-none leading-relaxed transition-all"
            />
            <button
              onClick={() => sendMessage()}
              disabled={!input.trim() || loading}
              className="p-3 rounded-xl bg-[#21D4C2] hover:bg-[#1bbfad] disabled:opacity-40 disabled:cursor-not-allowed text-[#07111F] transition-all"
            >
              <svg width="18" height="18" fill="none" viewBox="0 0 24 24">
                <path d="M22 2L11 13M22 2L15 22l-4-9-9-4 20-7Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
