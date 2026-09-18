import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Trợ lý Pháp luật Việt Nam — RAG",
  description:
    "Hệ thống hỏi đáp văn bản pháp luật Việt Nam dùng RAG + Hybrid Search (Qdrant + BM25) chạy LLM local.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="vi">
      <body>{children}</body>
    </html>
  );
}
