export type ChatRole = "user" | "assistant";

export interface Session {
  id: string;           // crypto.randomUUID()
  title: string;        // câu hỏi đầu tiên, tối đa 60 ký tự; "" khi phiên mới chưa có câu hỏi
  createdAt: number;    // Date.now()
  messages: ChatMessage[];
}

export interface ChatMessage {
  role: ChatRole;
  content: string;
  sources?: Source[];
  isStreaming?: boolean;
  error?: string;
}

export interface Source {
  label: string;
  source: string;
  title?: string;
  doc_type?: string;
  year?: string | null;
  page?: number | null;
  chunk_index?: number | null;
  snippet: string;
  rrf_score: number;
}

export interface DocumentInfo {
  source: string;
  title: string;
  doc_type: string;
  year?: string | null;
  chunk_count: number;
}

export interface DocumentListResponse {
  total_documents: number;
  total_chunks: number;
  documents: DocumentInfo[];
}

export interface HealthResponse {
  status: string;
  app_name: string;
  app_version: string;
  llm_provider: string;
  embed_provider: string;
  total_chunks: number;
}
