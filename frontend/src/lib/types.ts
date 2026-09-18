export type ChatRole = "user" | "assistant";

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

export interface IngestResult {
  status: "success" | "skipped" | "error";
  source: string;
  pages?: number | null;
  chunks?: number | null;
  reason?: string | null;
}

export interface IngestResponse {
  results: IngestResult[];
}

export interface HealthResponse {
  status: string;
  app_name: string;
  app_version: string;
  llm_provider: string;
  embed_provider: string;
  total_chunks: number;
}
