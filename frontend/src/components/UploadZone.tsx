"use client";

import { Upload, FileText, Loader2, CheckCircle2, XCircle, MinusCircle } from "lucide-react";
import { useRef, useState } from "react";
import { uploadDocuments } from "@/lib/api";
import type { IngestResult } from "@/lib/types";
import { cn, formatBytes } from "@/lib/utils";

interface Props {
  onUploaded: () => void;
}

const ACCEPT = ".pdf,.docx,.txt";

export default function UploadZone({ onUploaded }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [overwrite, setOverwrite] = useState(false);
  const [busy, setBusy] = useState(false);
  const [results, setResults] = useState<IngestResult[]>([]);
  const [dragActive, setDragActive] = useState(false);

  const addFiles = (incoming: FileList | File[]) => {
    const arr = Array.from(incoming).filter((f) => {
      const ext = "." + f.name.split(".").pop()?.toLowerCase();
      return ACCEPT.includes(ext);
    });
    setFiles((prev) => [...prev, ...arr]);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files) addFiles(e.dataTransfer.files);
  };

  const handleUpload = async () => {
    if (!files.length) return;
    setBusy(true);
    setResults([]);
    try {
      const res = await uploadDocuments(files, overwrite);
      setResults(res.results);
      setFiles([]);
      onUploaded();
    } catch (e) {
      setResults([
        { status: "error", source: "upload", reason: (e as Error).message },
      ]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-3">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={cn(
          "border-2 border-dashed rounded-lg px-4 py-6 text-center cursor-pointer transition-colors",
          dragActive
            ? "border-brand-500 bg-brand-50"
            : "border-slate-300 hover:border-brand-400 hover:bg-slate-50",
        )}
      >
        <Upload className="mx-auto text-slate-400 mb-2" size={24} />
        <p className="text-sm font-medium text-slate-700">
          Kéo thả hoặc nhấn để chọn tài liệu
        </p>
        <p className="text-xs text-slate-500 mt-1">
          Hỗ trợ PDF, DOCX, TXT (tối đa 50 MB / file)
        </p>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={ACCEPT}
          className="hidden"
          onChange={(e) => e.target.files && addFiles(e.target.files)}
        />
      </div>

      {files.length > 0 && (
        <div className="space-y-1.5">
          {files.map((f, i) => (
            <div
              key={`${f.name}-${i}`}
              className="flex items-center gap-2 text-xs px-2 py-1.5 bg-slate-100 rounded-md"
            >
              <FileText size={14} className="text-slate-500 shrink-0" />
              <span className="truncate flex-1 text-slate-700">{f.name}</span>
              <span className="text-slate-500">{formatBytes(f.size)}</span>
              <button
                onClick={() =>
                  setFiles((prev) => prev.filter((_, idx) => idx !== i))
                }
                className="text-slate-400 hover:text-red-600"
                aria-label="Remove"
              >
                <MinusCircle size={14} />
              </button>
            </div>
          ))}
        </div>
      )}

      <label className="flex items-center gap-2 text-xs text-slate-600 cursor-pointer select-none">
        <input
          type="checkbox"
          checked={overwrite}
          onChange={(e) => setOverwrite(e.target.checked)}
          className="rounded border-slate-300 text-brand-600 focus:ring-brand-500"
        />
        Ghi đè nếu tài liệu đã tồn tại
      </label>

      <button
        onClick={handleUpload}
        disabled={!files.length || busy}
        className={cn(
          "w-full inline-flex items-center justify-center gap-2 py-2 px-3 text-sm font-medium rounded-md transition-colors",
          !files.length || busy
            ? "bg-slate-200 text-slate-400 cursor-not-allowed"
            : "bg-brand-600 hover:bg-brand-700 text-white",
        )}
      >
        {busy ? (
          <>
            <Loader2 className="animate-spin" size={14} /> Đang nạp…
          </>
        ) : (
          <>
            <Upload size={14} /> Bắt đầu nạp ({files.length})
          </>
        )}
      </button>

      {results.length > 0 && (
        <div className="space-y-1 pt-1">
          {results.map((r, i) => (
            <ResultRow key={i} result={r} />
          ))}
        </div>
      )}
    </div>
  );
}

function ResultRow({ result }: { result: IngestResult }) {
  const map = {
    success: {
      icon: <CheckCircle2 size={14} className="text-emerald-600" />,
      cls: "bg-emerald-50 border-emerald-200 text-emerald-800",
      msg: result.chunks
        ? `${result.chunks} chunks · ${result.pages ?? "?"} trang`
        : "Thành công",
    },
    skipped: {
      icon: <MinusCircle size={14} className="text-amber-600" />,
      cls: "bg-amber-50 border-amber-200 text-amber-800",
      msg: "Đã tồn tại — bật 'Ghi đè' để cập nhật",
    },
    error: {
      icon: <XCircle size={14} className="text-red-600" />,
      cls: "bg-red-50 border-red-200 text-red-800",
      msg: result.reason ?? "Lỗi không xác định",
    },
  } as const;

  const item = map[result.status];

  return (
    <div className={`text-xs px-2 py-1.5 rounded-md border ${item.cls}`}>
      <div className="flex items-center gap-1.5 font-medium">
        {item.icon}
        <span className="truncate">{result.source}</span>
      </div>
      <div className="ml-5 text-[11px] opacity-80">{item.msg}</div>
    </div>
  );
}
