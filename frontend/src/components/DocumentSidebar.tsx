"use client";

import {
  FileText,
  Trash2,
  RefreshCw,
  FolderOpen,
  Database,
  Inbox,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { deleteDocument, listDocuments } from "@/lib/api";
import type { DocumentInfo } from "@/lib/types";
import UploadZone from "./UploadZone";

export default function DocumentSidebar({
  onChange,
}: {
  onChange?: () => void;
}) {
  const [docs, setDocs] = useState<DocumentInfo[]>([]);
  const [totalChunks, setTotalChunks] = useState(0);
  const [loading, setLoading] = useState(true);
  const [pendingDelete, setPendingDelete] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listDocuments();
      setDocs(data.documents);
      setTotalChunks(data.total_chunks);
    } catch {
      setDocs([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleDelete = async (source: string) => {
    if (!confirm(`Xóa "${source}" khỏi index?`)) return;
    setPendingDelete(source);
    try {
      await deleteDocument(source);
      await refresh();
      onChange?.();
    } finally {
      setPendingDelete(null);
    }
  };

  const handleUploaded = async () => {
    await refresh();
    onChange?.();
  };

  return (
    <aside className="w-80 border-r border-slate-200 bg-white flex flex-col shrink-0">
      <div className="p-4 border-b border-slate-200">
        <div className="flex items-center gap-2 mb-3">
          <FolderOpen size={16} className="text-brand-600" />
          <h2 className="font-semibold text-slate-900">Quản lý tài liệu</h2>
        </div>
        <UploadZone onUploaded={handleUploaded} />
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-1.5 text-xs font-medium text-slate-700">
            <Database size={13} />
            <span>Đã nạp</span>
            <span className="text-slate-400">
              ({docs.length} VB · {totalChunks} chunks)
            </span>
          </div>
          <button
            onClick={refresh}
            className="p-1 rounded hover:bg-slate-100 text-slate-500"
            aria-label="Refresh"
          >
            <RefreshCw
              size={13}
              className={loading ? "animate-spin" : ""}
            />
          </button>
        </div>

        {!loading && docs.length === 0 && (
          <div className="text-center py-8 text-slate-400">
            <Inbox className="mx-auto mb-2" size={32} />
            <p className="text-xs">Chưa có tài liệu nào</p>
          </div>
        )}

        <ul className="space-y-1.5">
          {docs.map((doc) => (
            <li
              key={doc.source}
              className="group rounded-md border border-slate-200 bg-slate-50 hover:bg-white hover:border-brand-200 px-3 py-2 transition-colors"
            >
              <div className="flex items-start gap-2">
                <FileText
                  size={14}
                  className="text-brand-600 mt-0.5 shrink-0"
                />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-800 truncate">
                    {doc.title || doc.source}
                  </p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {doc.doc_type && (
                      <span className="text-[10px] uppercase tracking-wide font-semibold px-1.5 py-0.5 bg-brand-100 text-brand-700 rounded">
                        {doc.doc_type}
                      </span>
                    )}
                    {doc.year && (
                      <span className="text-[10px] px-1.5 py-0.5 bg-slate-200 text-slate-700 rounded">
                        {doc.year}
                      </span>
                    )}
                    <span className="text-[10px] px-1.5 py-0.5 bg-emerald-100 text-emerald-700 rounded">
                      {doc.chunk_count} chunks
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(doc.source)}
                  disabled={pendingDelete === doc.source}
                  className="text-slate-400 hover:text-red-600 disabled:opacity-50 transition-colors shrink-0"
                  aria-label="Delete"
                  title="Xóa tài liệu"
                >
                  {pendingDelete === doc.source ? (
                    <RefreshCw size={14} className="animate-spin" />
                  ) : (
                    <Trash2 size={14} />
                  )}
                </button>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </aside>
  );
}
