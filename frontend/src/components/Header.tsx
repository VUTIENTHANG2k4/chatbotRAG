"use client";

import { Scale } from "lucide-react";

export default function Header() {
  return (
    <header className="border-b border-slate-200 bg-white/80 backdrop-blur-sm sticky top-0 z-10">
      <div className="px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-brand-600 text-white">
            <Scale size={20} />
          </div>
          <div>
            <h1 className="font-semibold text-slate-900">
              Chatbot Pháp luật Lao động VN
            </h1>
            <p className="text-xs text-slate-500">
              Hợp đồng lao động · RAG Hybrid Search · Local LLM
            </p>
          </div>
        </div>
      </div>
    </header>
  );
}
