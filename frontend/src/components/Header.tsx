"use client";

import { Scale, Cpu } from "lucide-react";
import { useEffect, useState } from "react";
import { health } from "@/lib/api";
import type { HealthResponse } from "@/lib/types";

export default function Header() {
  const [info, setInfo] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    health()
      .then(setInfo)
      .catch((e) => setError(e.message));
    const id = setInterval(() => {
      health().then(setInfo).catch(() => {});
    }, 30_000);
    return () => clearInterval(id);
  }, []);

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

        <div className="flex items-center gap-4 text-xs">
          {info && (
            <>
              <Badge
                icon={<Cpu size={12} />}
                label={`LLM: ${info.llm_provider}`}
                tone="indigo"
              />
              <Badge
                label={`Embed: ${info.embed_provider}`}
                tone="emerald"
              />
              <Badge
                label={`${info.total_chunks} chunks`}
                tone="slate"
              />
            </>
          )}
          {error && (
            <Badge label="Backend offline" tone="red" />
          )}
        </div>
      </div>
    </header>
  );
}

function Badge({
  label,
  icon,
  tone,
}: {
  label: string;
  icon?: React.ReactNode;
  tone: "indigo" | "emerald" | "slate" | "red";
}) {
  const tones: Record<string, string> = {
    indigo: "bg-indigo-50 text-indigo-700 border-indigo-200",
    emerald: "bg-emerald-50 text-emerald-700 border-emerald-200",
    slate: "bg-slate-100 text-slate-700 border-slate-200",
    red: "bg-red-50 text-red-700 border-red-200",
  };
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-md border font-medium ${tones[tone]}`}
    >
      {icon}
      {label}
    </span>
  );
}
