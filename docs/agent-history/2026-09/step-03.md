# Bước 3 — Tối ưu System Prompt cho HĐLĐ

**Ngày:** 2026-09-18  
**Giai đoạn:** Phase 2 — RAG Quality  
**Trạng thái:** ✅ HOÀN THÀNH (3/3 test PASS)

---

## Mục tiêu

1. Chuyên biệt hoá system prompt cho domain hợp đồng lao động Việt Nam
2. Thêm cấu trúc trả lời 3 phần: Quy định → Căn cứ pháp lý → Lưu ý thực tiễn
3. Đảm bảo model luôn trích dẫn nguồn [N]
4. Test với 3 câu hỏi đại diện qua Ollama API

---

## Thay đổi Code

### `backend/app/services/rag.py` — `_SYSTEM_PROMPT`

**Trước:**
- Prompt tổng quát về pháp luật Việt Nam
- 5 quy tắc cơ bản, không có cấu trúc trả lời
- Không hướng dẫn định dạng

**Sau:**
- Chuyên biệt cho **hợp đồng lao động**, đề cập NLĐ và NSDLĐ
- Quy tắc bắt buộc giữ nguyên + tăng cường
- Thêm **Định dạng trả lời bắt buộc** 3 phần:
  - `Quy định áp dụng:` — Điều/khoản cụ thể
  - `Căn cứ pháp lý:` — diễn giải + [số nguồn]
  - `Lưu ý thực tiễn:` — điều kiện/ngoại lệ

### `backend/app/services/llm.py`
- Thêm hàm `clear_llm_cache()` để xóa LRU cache khi cần đổi model

### `backend/.env`
- Đổi `LLM_PROVIDER=gemini` → `LLM_PROVIDER=ollama`
- Đổi `OLLAMA_MODEL=qwen2.5:7b` → `OLLAMA_MODEL=qwen2.5:3b`
- Đổi `OLLAMA_BASE_URL=http://localhost:11434` → `http://127.0.0.1:11434`

---

## Vấn đề Phát Hiện & Giải Quyết

### 1. `qwen2.5:7b` crash OOM (exit code -1)
- **Nguyên nhân:** Model 7b (~4.5 GB) vượt RAM khả dụng khi load context pháp luật
- **Fix:** Pull `qwen2.5:3b` (~1.9 GB), đủ nhẹ để chạy ổn định

### 2. `localhost` vs `127.0.0.1` — 2 server Ollama khác nhau
- **Nguyên nhân:** Windows có Docker Desktop + WSL2 bind port 11434 qua IPv6 (`::1`),
  còn Ollama CLI bind riêng ở `127.0.0.1:11434`. Khi dùng `localhost`, Python resolve
  sang IPv6 → hit Docker → model 7b crash; dùng `127.0.0.1` → hit Ollama thật với 3b.
- **Fix:** Đổi `OLLAMA_BASE_URL=http://127.0.0.1:11434` trong `.env`

### 3. Prompt "nhận diện đối tượng" làm model hỏi lại
- **Nguyên nhân:** qwen2.5:3b (model nhỏ) hiểu sai phần "nếu không rõ → hỏi lại"
- **Fix:** Xóa block "Nhận diện đối tượng", để model tự phán đoán theo context

---

## Kết Quả Test

File: `docs/tests/step03_prompt_test.py`

| # | Câu hỏi | KW | Cite | PASS |
|---|---|---|---|---|
| 1 | Nghỉ việc báo trước bao nhiêu ngày? | 2/2 | ✅ | ✅ |
| 2 | Doanh nghiệp sa thải vì lý do gì? | 2/2 | ✅ | ✅ |
| 3 | Thời gian thử việc tối đa? | 2/2 | ✅ | ✅ |

**Tổng: 3/3 PASS**

### Quan sát chất lượng câu trả lời
- Model trích dẫn đúng Điều luật (Điều 36 nghỉ việc, Điều 125 sa thải, Điều 25 thử việc)
- Sử dụng format `Quy định áp dụng:` và `Căn cứ pháp lý:` (Test 3 đầy đủ nhất)
- Tốc độ: 2.4–27s/câu (câu đơn giản rất nhanh, câu phức tạp hơn ~27s)

---

## Checklist Test

- [x] Ollama chạy được với `qwen2.5:3b` tại `127.0.0.1:11434`
- [x] 3/3 test PASS
- [x] Prompt có cấu trúc 3 phần
- [x] Citation `[N]` xuất hiện trong câu trả lời
- [x] Nội dung trích dẫn đúng Điều/khoản

---

## Bước Tiếp Theo (Bước 4)

**Xây dựng API chat endpoint** để frontend kết nối:
- `POST /api/v1/chat` nhận `question`, trả `answer` + `sources`
- Streaming SSE cho real-time response
- Multi-turn conversation với `chat_history`
