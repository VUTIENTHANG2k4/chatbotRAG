import type {
  ChatMessage,
  DocumentListResponse,
  HealthResponse,
  Source,
} from "./types";

// All API calls go through Next.js rewrites at /api/backend/*
// (configured in next.config.mjs → forwards to FastAPI /api/v1/*)
const API_BASE = "/api/backend";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${text || res.statusText}`);
  }

  return res.json();
}

// ── Health ────────────────────────────────────────────────────────────

export const health = () => request<HealthResponse>("/health");

// ── Documents ─────────────────────────────────────────────────────────

export const listDocuments = () =>
  request<DocumentListResponse>("/documents");

// ── Chat (SSE streaming) ──────────────────────────────────────────────

export interface StreamChatOptions {
  question: string;
  chatHistory: { role: "user" | "assistant"; content: string }[];
  topK?: number;
  filterDocType?: string;
  filterYear?: string;
  signal?: AbortSignal;
  onSources: (sources: Source[]) => void;
  onToken: (token: string) => void;
  onDone: () => void;
  onError: (err: string) => void;
}

export async function streamChat(opts: StreamChatOptions): Promise<void> {
  const res = await fetch(`${API_BASE}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question: opts.question,
      chat_history: opts.chatHistory,
      top_k: opts.topK ?? 5,
      filter_doc_type: opts.filterDocType || null,
      filter_year: opts.filterYear || null,
    }),
    signal: opts.signal,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    opts.onError(`HTTP ${res.status}: ${text || res.statusText}`);
    return;
  }
  if (!res.body) {
    opts.onError("Streaming not supported by browser");
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      // SSE events are separated by a blank line
      const events = buffer.split("\n\n");
      buffer = events.pop() ?? "";

      for (const evt of events) {
        if (!evt.trim()) continue;
        const { event, data } = parseSSE(evt);

        if (event === "sources") {
          try {
            opts.onSources(JSON.parse(data) as Source[]);
          } catch {}
        } else if (event === "token") {
          try {
            opts.onToken(JSON.parse(data) as string);
          } catch {
            opts.onToken(data);
          }
        } else if (event === "done") {
          opts.onDone();
          return;
        } else if (event === "error") {
          try {
            const parsed = JSON.parse(data);
            opts.onError(parsed.message ?? data);
          } catch {
            opts.onError(data);
          }
          return;
        }
      }
    }
    opts.onDone();
  } catch (e) {
    if ((e as Error).name === "AbortError") return;
    opts.onError((e as Error).message);
  }
}

function parseSSE(raw: string): { event: string; data: string } {
  let event = "message";
  const dataLines: string[] = [];
  for (const line of raw.split("\n")) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
  }
  return { event, data: dataLines.join("\n") };
}

export function _historyToApi(messages: ChatMessage[]) {
  return messages
    .filter((m) => m.role === "user" || m.role === "assistant")
    .map((m) => ({ role: m.role, content: m.content }));
}
