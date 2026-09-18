"use client";

import { useState } from "react";
import ChatPanel from "@/components/ChatPanel";
import DocumentSidebar from "@/components/DocumentSidebar";
import Header from "@/components/Header";

export default function Home() {
  const [docVersion, setDocVersion] = useState(0);

  return (
    <div className="h-screen flex flex-col bg-slate-50">
      <Header />
      <div className="flex-1 flex min-h-0">
        <DocumentSidebar onChange={() => setDocVersion((v) => v + 1)} />
        <ChatPanel refreshKey={docVersion} />
      </div>
    </div>
  );
}
