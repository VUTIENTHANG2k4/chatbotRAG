"use client";

import { MessageSquare, PanelLeftClose, PanelLeftOpen, Plus, Trash2 } from "lucide-react";
import type { Session } from "@/lib/types";
import { cn } from "@/lib/utils";

interface Props {
  sessions: Session[];
  activeId: string;
  open: boolean;
  onToggle: () => void;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
}

function formatDate(ts: number): string {
  const d = new Date(ts);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffDays = Math.floor(diffMs / 86_400_000);

  if (diffDays === 0) {
    return d.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });
  }
  if (diffDays === 1) return "Hôm qua";
  if (diffDays < 7) return `${diffDays} ngày trước`;
  return d.toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit" });
}

export default function SessionSidebar({
  sessions,
  activeId,
  open,
  onToggle,
  onSelect,
  onNew,
  onDelete,
}: Props) {
  return (
    <aside
      className={cn(
        "flex flex-col border-r border-slate-200 bg-white transition-all duration-200 shrink-0",
        open ? "w-56" : "w-12",
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-2 py-3 border-b border-slate-100">
        {open && (
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide pl-1">
            Phiên hội thoại
          </span>
        )}
        <button
          onClick={onToggle}
          className={cn(
            "p-1.5 rounded-md text-slate-500 hover:bg-slate-100 hover:text-slate-700 transition-colors",
            !open && "mx-auto",
          )}
          aria-label={open ? "Thu gọn sidebar" : "Mở rộng sidebar"}
        >
          {open ? <PanelLeftClose size={16} /> : <PanelLeftOpen size={16} />}
        </button>
      </div>

      {/* Nút tạo phiên mới */}
      <div className={cn("px-2 py-2", !open && "flex justify-center")}>
        <button
          onClick={onNew}
          className={cn(
            "flex items-center gap-2 rounded-lg transition-colors text-sm font-medium",
            "bg-brand-600 text-white hover:bg-brand-700",
            open ? "w-full px-3 py-2" : "p-2",
          )}
          aria-label="Phiên mới"
        >
          <Plus size={15} className="shrink-0" />
          {open && <span>Phiên mới</span>}
        </button>
      </div>

      {/* Danh sách phiên */}
      {open && (
        <div className="flex-1 overflow-y-auto py-1 px-2 space-y-0.5">
          {sessions.length === 0 && (
            <p className="text-xs text-slate-400 text-center pt-6 px-2">
              Chưa có phiên nào
            </p>
          )}
          {sessions.map((s) => {
            const isActive = s.id === activeId;
            return (
              <div
                key={s.id}
                className={cn(
                  "group flex items-start gap-2 rounded-lg px-2 py-2 cursor-pointer transition-colors",
                  isActive
                    ? "bg-brand-50 border border-brand-200 text-brand-900"
                    : "hover:bg-slate-100 text-slate-700",
                )}
                onClick={() => onSelect(s.id)}
              >
                <MessageSquare
                  size={14}
                  className={cn(
                    "mt-0.5 shrink-0",
                    isActive ? "text-brand-600" : "text-slate-400",
                  )}
                />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium leading-snug truncate">
                    {s.title || "Phiên mới"}
                  </p>
                  <p className="text-[10px] text-slate-400 mt-0.5">
                    {formatDate(s.createdAt)}
                  </p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(s.id);
                  }}
                  className={cn(
                    "shrink-0 p-0.5 rounded text-slate-300 hover:text-red-500 transition-colors",
                    "opacity-0 group-hover:opacity-100",
                  )}
                  aria-label="Xóa phiên"
                >
                  <Trash2 size={12} />
                </button>
              </div>
            );
          })}
        </div>
      )}

      {/* Collapsed: chỉ icon từng phiên */}
      {!open && sessions.length > 0 && (
        <div className="flex-1 overflow-y-auto py-1 flex flex-col items-center gap-1 px-1">
          {sessions.slice(0, 20).map((s) => (
            <button
              key={s.id}
              onClick={() => onSelect(s.id)}
              className={cn(
                "p-1.5 rounded-md transition-colors",
                s.id === activeId
                  ? "bg-brand-100 text-brand-700"
                  : "text-slate-400 hover:bg-slate-100 hover:text-slate-700",
              )}
              title={s.title || "Phiên mới"}
              aria-label={s.title || "Phiên mới"}
            >
              <MessageSquare size={14} />
            </button>
          ))}
        </div>
      )}
    </aside>
  );
}
