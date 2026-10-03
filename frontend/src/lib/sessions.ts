import type { Session } from "./types";

export const SESSIONS_KEY = "legal_rag_sessions";
export const ACTIVE_SESSION_KEY = "legal_rag_active_session";
const MAX_SESSIONS = 30;

// ── Helpers ────────────────────────────────────────────────────────────────

export function loadSessions(): Session[] {
  try {
    const raw = localStorage.getItem(SESSIONS_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? (parsed as Session[]) : [];
  } catch {
    return [];
  }
}

export function saveSession(session: Session): void {
  try {
    const sessions = loadSessions();
    const idx = sessions.findIndex((s) => s.id === session.id);
    if (idx >= 0) {
      sessions[idx] = session;
    } else {
      sessions.unshift(session); // mới nhất đầu tiên
    }
    // Giữ tối đa MAX_SESSIONS phiên
    const trimmed = sessions.slice(0, MAX_SESSIONS);
    localStorage.setItem(SESSIONS_KEY, JSON.stringify(trimmed));
  } catch {}
}

export function deleteSession(id: string): void {
  try {
    const sessions = loadSessions().filter((s) => s.id !== id);
    localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions));
  } catch {}
}

export function loadActiveId(): string | null {
  try {
    return localStorage.getItem(ACTIVE_SESSION_KEY);
  } catch {
    return null;
  }
}

export function saveActiveId(id: string): void {
  try {
    localStorage.setItem(ACTIVE_SESSION_KEY, id);
  } catch {}
}

export function newSession(): Session {
  return {
    id: crypto.randomUUID(),
    title: "",
    createdAt: Date.now(),
    messages: [],
  };
}

/**
 * Trả về phiên đầu tiên trong danh sách, hoặc tạo mới nếu chưa có.
 * Phiên mới được lưu ngay để activeId có thể khớp.
 */
export function getOrCreateInitialSession(sessions: Session[]): Session {
  if (sessions.length > 0) return sessions[0];
  const s = newSession();
  saveSession(s);
  return s;
}
