"use client";

import { useCallback, useEffect, useState } from "react";
import ChatPanel from "@/components/ChatPanel";
import Header from "@/components/Header";
import SessionSidebar from "@/components/SessionSidebar";
import {
  deleteSession,
  getOrCreateInitialSession,
  loadActiveId,
  loadSessions,
  newSession,
  saveActiveId,
  saveSession,
} from "@/lib/sessions";
import type { Session } from "@/lib/types";

export default function Home() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeId, setActiveId] = useState<string>("");
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Khởi tạo từ localStorage một lần (client-only)
  useEffect(() => {
    const stored = loadSessions();
    const initial = getOrCreateInitialSession(stored);
    const allSessions = stored.some((s) => s.id === initial.id)
      ? stored
      : [initial, ...stored];
    setSessions(allSessions);

    const savedId = loadActiveId();
    const validId = allSessions.find((s) => s.id === savedId)?.id ?? initial.id;
    setActiveId(validId);
  }, []);

  const activeSession: Session =
    sessions.find((s) => s.id === activeId) ??
    (sessions[0] ?? newSession());

  // Lưu activeId khi đổi
  useEffect(() => {
    if (activeId) saveActiveId(activeId);
  }, [activeId]);

  const handleUpdate = useCallback((updated: Session) => {
    saveSession(updated);
    setSessions((prev) => {
      const idx = prev.findIndex((s) => s.id === updated.id);
      if (idx >= 0) {
        const copy = [...prev];
        copy[idx] = updated;
        return copy;
      }
      return [updated, ...prev];
    });
  }, []);

  const handleNew = useCallback(() => {
    const s = newSession();
    saveSession(s);
    setSessions((prev) => [s, ...prev]);
    setActiveId(s.id);
  }, []);

  const handleDelete = useCallback(
    (id: string) => {
      deleteSession(id);
      setSessions((prev) => {
        const next = prev.filter((s) => s.id !== id);
        // Nếu xóa phiên đang active, chuyển sang phiên đầu hoặc tạo mới
        if (id === activeId) {
          if (next.length > 0) {
            setActiveId(next[0].id);
          } else {
            const fresh = newSession();
            saveSession(fresh);
            setActiveId(fresh.id);
            return [fresh];
          }
        }
        return next;
      });
    },
    [activeId],
  );

  const handleSelect = useCallback((id: string) => {
    setActiveId(id);
  }, []);

  return (
    <div className="h-screen flex flex-col bg-slate-50">
      <Header />
      <div className="flex-1 flex min-h-0">
        <SessionSidebar
          sessions={sessions}
          activeId={activeId}
          open={sidebarOpen}
          onToggle={() => setSidebarOpen((v) => !v)}
          onSelect={handleSelect}
          onNew={handleNew}
          onDelete={handleDelete}
        />
        <ChatPanel
          session={activeSession}
          onUpdate={handleUpdate}
        />
      </div>
    </div>
  );
}
