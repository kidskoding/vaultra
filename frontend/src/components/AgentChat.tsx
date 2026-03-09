import { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { chatWithAgent, getQuickBooksStatus } from '../lib/api';
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
  const [connected, setConnected] = useState<boolean | null>(null);
  const [conversationId, setConversationId] = useState<string | undefined>(initialConvId);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const bid = businessId || getCurrentBusinessId() || '';

  // Scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Check QuickBooks connection on mount
  useEffect(() => {
    if (!bid) {
      setConnected(false);
      return;
    }

    let cancelled = false;

    (async () => {
      try {
        const status: any = await getQuickBooksStatus(bid);
        if (!cancelled) {
          setConnected(Boolean(status?.connected));
        }
      } catch {
        if (!cancelled) {
          setConnected(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [bid]);

  const handleSend = async (msg?: string) => {
    const userMsg = (msg ?? input).trim();
    if (!userMsg || !bid || !connected) return;
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

  // While checking connection
  if (connected === null) {
    return (
      <div className="flex flex-col h-[calc(100vh-13rem)] bg-[#292524] rounded-2xl border border-[#44403c] overflow-hidden">
        <div className="flex-1 flex items-center justify-center text-sm text-[#a8a29e]">
          Checking QuickBooks connection…
        </div>
      </div>
    );
  }

  // If not connected, show gating card instead of chat
  if (!connected) {
    return (
      <div className="flex flex-col h-[calc(100vh-13rem)] bg-[#292524] rounded-2xl border border-[#44403c] overflow-hidden">
        <div className="flex-1 flex items-center justify-center p-6">
          <div className="max-w-xl w-full bg-[#1c1917] border border-[#44403c] rounded-2xl p-6 flex items-center justify-between gap-6">
            <div>
              <p className="text-sm font-medium text-[#ede9e3] mb-1">Connect QuickBooks to chat with your AI advisor</p>
              <p className="text-xs text-[#78716c]">
                The agent needs access to your financial metrics to give accurate, tailored guidance.
              </p>
            </div>
            <a
              href="/dashboard/settings?connect=quickbooks"
              className="inline-flex items-center justify-center px-4 py-2.5 text-sm font-medium rounded-xl bg-[#da7756] text-white hover:bg-[#c96b4d] transition-colors shrink-0"
            >
              Connect QuickBooks
            </a>
          </div>
        </div>
      </div>
    );
  }

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
              className={`max-w-[680px] px-4 py-3 text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-[#da7756] text-white rounded-2xl rounded-br-sm'
                  : 'bg-[#3c3836] text-[#ede9e3] rounded-2xl rounded-bl-sm'
              }`}
            >
              {msg.role === 'assistant' ? (
                <ReactMarkdown
                  components={{
                    p: ({ node, ...props }) => (
                      <p className="mb-1.5 last:mb-0 whitespace-pre-wrap" {...props} />
                    ),
                    strong: ({ node, ...props }) => (
                      <strong className="font-semibold" {...props} />
                    ),
                    ul: ({ node, ...props }) => (
                      <ul className="list-disc list-inside space-y-1 mb-1.5 last:mb-0" {...props} />
                    ),
                    ol: ({ node, ...props }) => (
                      <ol className="list-decimal list-inside space-y-1 mb-1.5 last:mb-0" {...props} />
                    ),
                    li: ({ node, ...props }) => (
                      <li className="whitespace-normal" {...props} />
                    ),
                  }}
                >
                  {msg.content}
                </ReactMarkdown>
              ) : (
                <span className="whitespace-pre-wrap">{msg.content}</span>
              )}
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
