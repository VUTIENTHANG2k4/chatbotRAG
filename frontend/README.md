# Frontend — Legal RAG Web App

Next.js 14 (App Router) + TypeScript + TailwindCSS frontend for the Vietnamese Legal-Document RAG system.

## Features

- Streaming chat over Server-Sent Events
- Drag-and-drop document upload (PDF / DOCX / TXT)
- Document manager: list, delete, see chunk counts
- Source citations expandable below each answer
- Persisted chat history (localStorage)
- Suggested starter questions
- Responsive desktop layout

## Folder layout

```
frontend/
├── src/
│   ├── app/                 # Next.js App Router (layout, page, globals)
│   ├── components/          # ChatPanel, MessageBubble, SourceCard, etc.
│   └── lib/                 # API client + types + utils
├── public/
├── package.json
├── next.config.mjs          # Rewrites /api/backend/* → FastAPI
├── tailwind.config.ts
└── tsconfig.json
```

## Setup (local dev)

```bash
cd frontend
cp .env.example .env.local      # Linux/Mac
# copy .env.example .env.local  # Windows

npm install
npm run dev                     # http://localhost:3000
```

The backend FastAPI must be running at `http://localhost:8000`
(or change `NEXT_PUBLIC_API_URL` in `.env.local`).

## How API requests work

```
Browser → /api/backend/chat/stream
   └── Next.js rewrite (next.config.mjs)
        └── http://backend:8000/api/v1/chat/stream
```

This avoids CORS issues and keeps the backend URL out of the browser.

## Production build

```bash
npm run build
npm run start
```

## Tech stack

- **Next.js 14** (App Router, standalone output for Docker)
- **TypeScript 5**
- **TailwindCSS 3**
- **react-markdown + remark-gfm** for rendering assistant answers
- **lucide-react** for icons
- Native `fetch` + SSE parsing (no extra deps)
