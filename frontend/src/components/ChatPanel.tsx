"use client";

import { Send, Trash2, Scale, Sparkles, StopCircle } from "lucide-react";
import {
  KeyboardEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import { _historyToApi, askChat, health, streamChat } from "@/lib/api";
import type { ChatMessage, Session } from "@/lib/types";
import { cn } from "@/lib/utils";
import MessageBubble from "./MessageBubble";

const SUGGESTED_QUESTIONS = [
  "Tôi ký hợp đồng xác định thời hạn 24 tháng, khi hết hạn có được ký tiếp không?",
  "Người lao động đơn phương nghỉ việc thì phải báo trước bao nhiêu ngày?",
  "Thời gian thử việc tối đa cho vị trí chuyên viên nhân sự là bao lâu?",
  "Doanh nghiệp chậm trả lương 10 ngày có vi phạm không và bị xử lý thế nào?",
];

interface Props {
  session: Session;
  onUpdate: (session: Session) => void;
}

export default function ChatPanel({ session, onUpdate }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>(session.messages);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [llmProvider, setLlmProvider] = useState<string | null>(null);
  const [embedProvider, setEmbedProvider] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const taRef = useRef<HTMLTextAreaElement>(null);
  // Theo dõi session id để reset khi chuyển phiên
  const sessionIdRef = useRef(session.id);

  useEffect(() => {
    health()
      .then((h) => {
        setLlmProvider(h.llm_provider);
        setEmbedProvider(h.embed_provider);
      })
      .catch(() => setLlmProvider(null));
  }, []);

  // Khi chuyển sang phiên khác → load messages mới, dừng stream cũ
  useEffect(() => {
    if (session.id === sessionIdRef.current) return;
    sessionIdRef.current = session.id;

    abortRef.current?.abort();
    abortRef.current = null;
    setStreaming(false);
    setMessages(session.messages);
    setInput("");
  }, [session.id, session.messages]);

  // Đồng bộ messages về parent và lưu
  useEffect(() => {
    const updated: Session = {
      ...session,
      messages,
      // Tự đặt title từ câu hỏi đầu tiên
      title:
        session.title ||
        (messages[0]?.role === "user"
          ? messages[0].content.slice(0, 60)
          : ""),
    };
    onUpdate(updated);
    // Không thêm session vào deps để tránh vòng lặp
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messages]);

  // Auto-scroll on new content
  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  // Auto-grow textarea
  useEffect(() => {
    if (!taRef.current) return;
    taRef.current.style.height = "auto";
    taRef.current.style.height = `${Math.min(taRef.current.scrollHeight, 200)}px`;
  }, [input]);

  const stopStreaming = () => {
    abortRef.current?.abort();
    abortRef.current = null;
    setStreaming(false);
    setMessages((prev) =>
      prev.map((m) => (m.isStreaming ? { ...m, isStreaming: false } : m)),
    );
  };

  const send = useCallback(
    async (text: string) => {
      const question = text.trim();
      if (!question || streaming) return;

      const userMsg: ChatMessage = { role: "user", content: question };
      const assistantMsg: ChatMessage = {
        role: "assistant",
        content: "",
        isStreaming: true,
        sources: [],
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setInput("");
      setStreaming(true);

      const ctrl = new AbortController();
      abortRef.current = ctrl;

      const history = _historyToApi(messages);
      // Public site calls Render directly. Streaming tokens are buffered there,
      // so the bubble stays empty. Ask for the full answer instead.
      const directApi = Boolean(process.env.NEXT_PUBLIC_BACKEND_ORIGIN);

      if (directApi) {
        try {
          const result = await askChat({
            question,
            chatHistory: history,
            topK: 5,
            signal: ctrl.signal,
          });
          setMessages((prev) => {
            const copy = [...prev];
            const last = copy[copy.length - 1];
            if (last?.role === "assistant") {
              copy[copy.length - 1] = {
                ...last,
                content: result.answer,
                sources: result.sources,
                isStreaming: false,
              };
            }
            return copy;
          });
        } catch (e) {
          if ((e as Error).name === "AbortError") return;
          const err = (e as Error).message || "Không nhận được câu trả lời";
          setMessages((prev) => {
            const copy = [...prev];
            const last = copy[copy.length - 1];
            if (last?.role === "assistant") {
              copy[copy.length - 1] = { ...last, isStreaming: false, error: err };
            }
            return copy;
          });
        } finally {
          setStreaming(false);
        }
        return;
      }

      await streamChat({
        question,
        chatHistory: history,
        topK: 5,
        signal: ctrl.signal,
        onSources: (sources) => {
          setMessages((prev) => {
            const copy = [...prev];
            const last = copy[copy.length - 1];
            if (last?.role === "assistant") {
              copy[copy.length - 1] = { ...last, sources };
            }
            return copy;
          });
        },
        onToken: (token) => {
          setMessages((prev) => {
            const copy = [...prev];
            const last = copy[copy.length - 1];
            if (last?.role === "assistant") {
              copy[copy.length - 1] = {
                ...last,
                content: last.content + token,
              };
            }
            return copy;
          });
        },
        onDone: () => {
          setMessages((prev) => {
            const copy = [...prev];
            const last = copy[copy.length - 1];
            if (last?.role === "assistant") {
              copy[copy.length - 1] = { ...last, isStreaming: false };
            }
            return copy;
          });
          setStreaming(false);
        },
        onError: (err) => {
          setMessages((prev) => {
            const copy = [...prev];
            const last = copy[copy.length - 1];
            if (last?.role === "assistant") {
              copy[copy.length - 1] = {
                ...last,
                isStreaming: false,
                error: err,
              };
            }
            return copy;
          });
          setStreaming(false);
        },
      });
    },
    [messages, streaming],
  );

  const onKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send(input);
    }
  };

  const clearChat = () => {
    if (!messages.length) return;
    if (!confirm("Xóa toàn bộ tin nhắn trong phiên này?")) return;
    setMessages([]);
  };

  return (
    <main className="flex-1 flex flex-col bg-slate-50 min-w-0">
      {/* Toolbar */}
      <div className="border-b border-slate-200 bg-white px-6 py-2.5 flex items-center justify-between">
        <p className="text-sm text-slate-600">
          {messages.length === 0
            ? "Đặt câu hỏi pháp luật để bắt đầu"
            : `${messages.filter((m) => m.role === "user").length} câu hỏi trong phiên này`}
        </p>
        <div className="flex items-center">
          <button
            onClick={clearChat}
            disabled={!messages.length || streaming}
            className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-600 hover:text-red-600 disabled:opacity-40 disabled:hover:text-slate-600"
          >
            <Trash2 size={13} />
            Xóa hội thoại
          </button>
        </div>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-6">
        {messages.length === 0 ? (
          <EmptyState onPick={send} cloud={Boolean(process.env.NEXT_PUBLIC_BACKEND_ORIGIN)} />
        ) : (
          <div className="max-w-4xl mx-auto space-y-6">
            {messages.map((m, i) => (
              <MessageBubble key={i} msg={m} />
            ))}
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-slate-200 bg-white px-6 py-4">
        <div className="max-w-4xl mx-auto">
          <div className="relative flex items-end gap-2 rounded-xl border border-slate-300 bg-white focus-within:border-brand-500 focus-within:ring-2 focus-within:ring-brand-100 transition px-3 py-2">
            <textarea
              ref={taRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKey}
              placeholder="Nhập câu hỏi pháp luật của bạn… (Enter để gửi, Shift+Enter để xuống dòng)"
              rows={1}
              disabled={streaming}
              className="flex-1 resize-none bg-transparent outline-none text-sm py-1.5 max-h-[200px] disabled:opacity-50"
            />
            {streaming ? (
              <button
                onClick={stopStreaming}
                className="shrink-0 inline-flex items-center justify-center w-9 h-9 rounded-lg bg-red-600 hover:bg-red-700 text-white"
                aria-label="Stop"
              >
                <StopCircle size={16} />
              </button>
            ) : (
              <button
                onClick={() => send(input)}
                disabled={!input.trim()}
                className={cn(
                  "shrink-0 inline-flex items-center justify-center w-9 h-9 rounded-lg transition-colors",
                  input.trim()
                    ? "bg-brand-600 hover:bg-brand-700 text-white"
                    : "bg-slate-200 text-slate-400 cursor-not-allowed",
                )}
                aria-label="Send"
              >
                <Send size={16} />
              </button>
            )}
          </div>
          <p className="text-[11px] text-slate-400 mt-2 text-center">
            Hệ thống chỉ trả lời dựa trên các tài liệu đã được nạp. Câu trả lời
            không thay thế tư vấn pháp lý chuyên nghiệp.
            {((llmProvider && llmProvider !== "ollama") ||
              embedProvider === "hf-inference") && (
              <>
                {" "}
                Câu hỏi được xử lý qua dịch vụ AI bên ngoài, không nhập thông
                tin cá nhân nhạy cảm.
              </>
            )}
          </p>
        </div>
      </div>
    </main>
  );
}

function EmptyState({
  onPick,
  cloud,
}: {
  onPick: (q: string) => void;
  cloud: boolean;
}) {
  return (
    <div className="max-w-2xl mx-auto text-center pt-12">
      <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-brand-100 text-brand-600 mb-4">
        <Scale size={32} />
      </div>
      <h2 className="text-2xl font-bold text-slate-900 mb-2">
        Trợ lý Hợp đồng Lao động
      </h2>
      <p className="text-slate-600 mb-8">
        Hỏi đáp quyền và nghĩa vụ NLĐ/NSDLĐ dựa trên tài liệu đã nạp.
        {cloud
          ? " Câu hỏi được xử lý qua dịch vụ AI bên ngoài, không nhập thông tin cá nhân nhạy cảm."
          : " Xử lý cục bộ, không gửi dữ liệu ra ngoài."}
      </p>

      <div className="flex items-center justify-center gap-1.5 mb-3 text-xs font-medium text-slate-500">
        <Sparkles size={13} />
        Câu hỏi gợi ý
      </div>
      <div className="grid sm:grid-cols-2 gap-2">
        {SUGGESTED_QUESTIONS.map((q) => (
          <button
            key={q}
            onClick={() => onPick(q)}
            className="text-left text-sm bg-white border border-slate-200 hover:border-brand-300 hover:bg-brand-50 px-4 py-3 rounded-lg transition-colors"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}
