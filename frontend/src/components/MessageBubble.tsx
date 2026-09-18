"use client";

import { Bot, User, AlertTriangle, ChevronDown } from "lucide-react";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage } from "@/lib/types";
import { cn } from "@/lib/utils";
import SourceCard from "./SourceCard";

export default function MessageBubble({ msg }: { msg: ChatMessage }) {
  const [showSources, setShowSources] = useState(true);
  const isUser = msg.role === "user";

  return (
    <div
      className={cn(
        "flex gap-3 animate-fade-in",
        isUser ? "flex-row-reverse" : "flex-row",
      )}
    >
      <div
        className={cn(
          "shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
          isUser ? "bg-slate-200 text-slate-700" : "bg-brand-600 text-white",
        )}
      >
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>

      <div className={cn("flex-1 min-w-0 max-w-3xl", isUser && "flex flex-col items-end")}>
        <div
          className={cn(
            "px-4 py-3 rounded-2xl",
            isUser
              ? "bg-brand-600 text-white rounded-tr-sm"
              : msg.error
                ? "bg-red-50 border border-red-200 text-red-900 rounded-tl-sm"
                : "bg-white border border-slate-200 text-slate-800 rounded-tl-sm",
          )}
        >
          {msg.error ? (
            <div className="flex items-start gap-2">
              <AlertTriangle size={16} className="mt-0.5 shrink-0" />
              <div className="text-sm whitespace-pre-wrap">{msg.error}</div>
            </div>
          ) : isUser ? (
            <p className="text-sm whitespace-pre-wrap leading-relaxed">
              {msg.content}
            </p>
          ) : (
            <div
              className={cn(
                "prose-answer text-sm",
                msg.isStreaming && "streaming-cursor",
              )}
            >
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {msg.content || (msg.isStreaming ? "" : "(Không có phản hồi)")}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {!isUser && msg.sources && msg.sources.length > 0 && (
          <div className="mt-2 w-full">
            <button
              onClick={() => setShowSources(!showSources)}
              className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-600 hover:text-brand-700"
            >
              <ChevronDown
                size={14}
                className={cn(
                  "transition-transform",
                  showSources ? "rotate-0" : "-rotate-90",
                )}
              />
              Nguồn trích dẫn ({msg.sources.length})
            </button>

            {showSources && (
              <div className="mt-2 grid gap-1.5">
                {msg.sources.map((src, i) => (
                  <SourceCard key={i} index={i + 1} source={src} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
