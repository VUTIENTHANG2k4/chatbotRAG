"use client";

import { BookOpen } from "lucide-react";
import type { Source } from "@/lib/types";

export default function SourceCard({
  index,
  source,
}: {
  index: number;
  source: Source;
}) {
  return (
    <div className="bg-brand-50/60 border border-brand-100 rounded-lg px-3 py-2 text-xs">
      <div className="flex items-start gap-2">
        <span className="shrink-0 inline-flex items-center justify-center w-5 h-5 rounded bg-brand-600 text-white text-[10px] font-bold">
          {index}
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 font-semibold text-brand-900">
            <BookOpen size={11} />
            <span className="truncate">{source.label}</span>
          </div>

          <div className="flex flex-wrap gap-1 mt-1 text-[10px]">
            {source.doc_type && (
              <span className="px-1.5 py-0.5 bg-white text-brand-700 rounded border border-brand-200">
                {source.doc_type}
              </span>
            )}
            {source.year && (
              <span className="px-1.5 py-0.5 bg-white text-slate-700 rounded border border-slate-200">
                {source.year}
              </span>
            )}
            {source.page != null && (
              <span className="px-1.5 py-0.5 bg-white text-slate-700 rounded border border-slate-200">
                Trang {source.page}
              </span>
            )}
            <span className="px-1.5 py-0.5 bg-emerald-50 text-emerald-700 rounded border border-emerald-200">
              RRF {source.rrf_score}
            </span>
          </div>

          <p className="mt-2 text-slate-700 leading-relaxed">
            {source.snippet}
          </p>
        </div>
      </div>
    </div>
  );
}
