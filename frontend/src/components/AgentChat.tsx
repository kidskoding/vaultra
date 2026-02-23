import { useEffect, useRef, useState } from 'react';
import { chatWithAgent } from '../lib/api';
import { getCurrentBusinessId } from '../lib/auth';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface Props {
  businessId?: string;
  conversationId?: string;
}

const SUGGESTED_PROMPTS = [
  "What's my current funding readiness score?",
  'How can I improve my chargeback ratio?',
  'What metrics matter most to investors?',
];

export default function AgentChat({ businessId, conversationId: initialConvId }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>(initialConvId);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const bid = businessId || getCurrentBusinessId() || '';

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (msg?: string) => {
    const userMsg = (msg ?? input).trim();
    if (!userMsg || !bid) return;
    setInput('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
    setMessages((prev) => [...prev, { role: 'user', content: userMsg }]);
    setLoading(true);
    try {
      const data: any = await chatWithAgent(bid, userMsg, conversationId);
      setConversationId(data.conversation_id);
      setMessages((prev) => [...prev, { role: 'assistant', content: data.response }]);
    } catch {
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 160)}px`;
  };

  return (
    <div className="flex flex-col h-[calc(100vh-13rem)] bg-[#292524] rounded-2xl border border-[#44403c] overflow-hidden">

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-5">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-7 pb-10">
            <div className="w-14 h-14 rounded-2xl bg-[#da7756]/10 border border-[#da7756]/20 flex items-center justify-center">
              <svg className="w-7 h-7 text-[#da7756]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <div className="text-center space-y-1">
              <p className="text-[#ede9e3] font-semibold">Your AI funding advisor</p>
              <p className="text-[#78716c] text-sm">Ask anything about your metrics, score, or funding strategy.</p>
            </div>
            <div className="flex flex-col gap-2 w-full max-w-sm">
              {SUGGESTED_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => handleSend(prompt)}
                  className="text-sm px-4 py-2.5 rounded-xl border border-[#44403c] text-[#a8a29e] hover:border-[#da7756]/40 hover:text-[#ede9e3] hover:bg-[#3c3836] transition-all text-left"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {msg.role === 'assistant' && (
              <div className="w-7 h-7 rounded-lg bg-[#da7756]/10 border border-[#da7756]/20 flex items-center justify-center shrink-0 mt-1">
                <svg className="w-3.5 h-3.5 text-[#da7756]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
            )}
            <div
              className={`max-w-[78%] px-4 py-3 text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-[#da7756] text-white rounded-2xl rounded-br-sm'
                  : 'bg-[#3c3836] text-[#ede9e3] rounded-2xl rounded-bl-sm'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex gap-3 justify-start">
            <div className="w-7 h-7 rounded-lg bg-[#da7756]/10 border border-[#da7756]/20 flex items-center justify-center shrink-0">
              <svg className="w-3.5 h-3.5 text-[#da7756]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div className="bg-[#3c3836] px-4 py-4 rounded-2xl rounded-bl-sm flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 bg-[#a8a29e] rounded-full animate-bounce [animation-delay:-0.3s]"></span>
              <span className="w-1.5 h-1.5 bg-[#a8a29e] rounded-full animate-bounce [animation-delay:-0.15s]"></span>
              <span className="w-1.5 h-1.5 bg-[#a8a29e] rounded-full animate-bounce"></span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-[#44403c] p-4 space-y-2">
        <div className="flex gap-3 items-end">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your funding readiness..."
            rows={1}
            className="flex-1 resize-none border border-[#44403c] rounded-xl px-4 py-3 text-sm bg-[#1c1917] text-[#ede9e3] placeholder-[#57534e] focus:outline-none focus:ring-2 focus:ring-[#da7756]/20 focus:border-[#da7756]/50 transition-colors leading-relaxed"
          />
          <button
            onClick={() => handleSend()}
            disabled={loading || !input.trim()}
            className="p-3 bg-[#da7756] text-white rounded-xl hover:bg-[#c96b4d] disabled:opacity-40 disabled:cursor-not-allowed transition-all shrink-0"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
        <p className="text-xs text-[#57534e] pl-1">Enter to send &middot; Shift+Enter for new line</p>
      </div>
    </div>
  );
}
