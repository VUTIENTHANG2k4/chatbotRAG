"use client";

import ChatPanel from "@/components/ChatPanel";
import Header from "@/components/Header";

export default function Home() {
  return (
    <div className="h-screen flex flex-col bg-slate-50">
      <Header />
      <div className="flex-1 flex min-h-0">
        <ChatPanel />
      </div>
    </div>
  );
}
