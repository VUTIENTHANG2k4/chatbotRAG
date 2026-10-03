# Báo cáo dự án: Chatbot hỏi đáp pháp luật lao động Việt Nam

**Cập nhật:** 04/10/2026

Chatbot dùng kỹ thuật RAG (truy xuất tài liệu rồi mới sinh câu trả lời) để tra cứu quy định hợp đồng lao động. Câu trả lời bám văn bản đã nạp, có trích điều luật, và viết bằng tiếng Việt.

- Giao diện: https://legal-rag-three.vercel.app
- API: https://legal-rag-backend-z8am.onrender.com

## 1. Mục tiêu

Giúp người lao động và doanh nghiệp hỏi một tình huống cụ thể rồi nhận lại quy định tương ứng, thay vì tự tìm trong cả bộ luật.

Hệ thống chỉ được trả lời từ tài liệu đã nạp. Mỗi câu trả lời phải nêu điều, khoản hoặc văn bản nguồn. Câu nằm ngoài kho tài liệu thì từ chối, không bịa số ngày, mức lương hay mức phạt.

## 2. Phạm vi

Đã làm:

- Hỏi đáp trên Văn bản hợp nhất Bộ luật Lao động (18/VBHN-VPQH).
- Tìm kiếm lai: vector và từ khóa, rồi gộp bằng Reciprocal Rank Fusion.
- Cắt văn bản theo từng Điều, lặp tiêu đề Điều ở mọi đoạn con.
- Giao diện chat, nhiều phiên hội thoại, lọc loại văn bản và năm, kèm nguồn trích dẫn.
- Hai cách chạy: máy cá nhân (Ollama, Qdrant trên đĩa) và bản public miễn phí (Gemini, Qdrant Cloud, Hugging Face).

Chưa làm:

- Chế độ đối chiếu nhiều quy định trên cùng một tình huống.
- Metadata hiệu lực (ngày có hiệu lực, văn bản bị thay thế).
- Nạp nghị định hướng dẫn, mẫu hợp đồng và nghị định xử phạt. Kho public hiện chỉ có Bộ luật.
- Triển khai Google Cloud Run. Tài khoản Google chưa gắn thanh toán.

## 3. Người dùng

| Đối tượng | Việc cần làm |
|---|---|
| Người lao động | Tra quyền, nghĩa vụ, thời hạn báo trước, thử việc, nghỉ phép |
| Doanh nghiệp, nhân sự | Kiểm tra một tình huống hợp đồng có đúng khung luật đã nạp hay không |

Câu trả lời là tra cứu, không thay tư vấn pháp lý. Bản public gửi câu hỏi và đoạn luật đã tìm thấy tới dịch vụ AI bên ngoài; giao diện ghi rõ điều này.

## 4. Cách hệ thống trả lời

1. Câu hỏi được embed bằng `keepitreal/vietnamese-sbert` (768 chiều, đã chuẩn hóa).
2. Qdrant tìm các đoạn gần nghĩa. BM25 tìm các đoạn trùng từ khóa pháp lý.
3. Hai danh sách gộp bằng RRF (`k = 60`), lấy top 5.
4. Các đoạn đó đưa vào prompt. Mô hình phải nêu số liệu đúng như tài liệu (ngày, giờ, tháng, phần trăm, mức tiền) và đánh dấu nguồn `[1]`, `[2]`.
5. Giao diện hiện câu trả lời cùng thẻ nguồn.

Local dùng Ollama `qwen2.5:3b`. Bản public dùng Gemini `gemini-3.8-flash`. Cùng một không gian vector nên chỉ mục 618 điểm dùng được cho cả hai.

## 5. Công nghệ

| Lớp | Local | Public |
|---|---|---|
| Giao diện | Next.js 14, TypeScript, Tailwind | Vercel |
| API | FastAPI, LangChain | Render Free, Singapore, 512 MB RAM |
| Mô hình sinh | Ollama `qwen2.5:3b` | Gemini `gemini-3.8-flash` |
| Embedding | PyTorch, model trên máy | Cùng model, qua Hugging Face Inference |
| Vector | Qdrant file trên đĩa | Qdrant Cloud, `australia-southeast1` |
| Từ khóa | BM25 ghi ra file pickle | BM25 dựng trong RAM lúc khởi động, từ payload Qdrant |

Bản public không cài PyTorch. Gói Render Free không đủ RAM cho model local. `requirements-cloud.txt` chỉ giữ thư viện gọi API. Một process uvicorn, vì chỉ mục BM25 nằm trong RAM của process đó.

Upload, xóa tài liệu và ingest đĩa tắt trên bản public (`ENABLE_ADMIN_API=false`, `AUTO_INGEST=false`). Nạp văn bản làm trên máy dev rồi copy vector lên Qdrant Cloud.

## 6. Dữ liệu

Một file: `backend/data/legal_documents/core/18-vbhn-vpqh.pdf`, bản scan Văn bản hợp nhất Bộ luật Lao động. Chữ được OCR sẵn, rồi cắt lại theo Điều.

Kết quả chỉ mục: **618 đoạn**. Mỗi đoạn mang metadata nguồn, loại văn bản, năm, số Điều và tiêu đề Điều. Bộ lọc trên giao diện áp vào cả nhánh vector và nhánh BM25.

OCR trên Windows cần Tesseract và Poppler. Bản đang chạy không OCR lại file này.

## 7. Chức năng đã có

- Hỏi đáp tiếng Việt, cấu trúc trả lời gồm quy định áp dụng, căn cứ và lưu ý thực tiễn khi tài liệu có các ý đó.
- Hybrid search và trích nguồn.
- Nhiều phiên chat, tạo mới, xóa, thu gọn; lưu trong `localStorage` của trình duyệt.
- Upload PDF, DOCX, TXT và ảnh trên máy dev; PDF scan đi qua OCR.
- Quét đệ quy thư mục `data/` và tự nạp khi bật auto-ingest.
- Nhận metadata văn bản hợp nhất.
- Lọc theo loại văn bản và năm.
- Câu hỏi gợi ý đúng miền hợp đồng lao động.
- Cảnh báo trên giao diện public: câu hỏi được xử lý qua dịch vụ AI bên ngoài.

## 8. Kết quả đánh giá

Bộ 100 câu bám Văn bản hợp nhất: 25 dễ, 30 trung bình, 25 khó, 20 câu ngoài phạm vi. Không chấm bằng BLEU hay ROUGE. Câu trong phạm vi được chấm theo việc nhắc đúng sự kiện và có trích dẫn. Câu ngoài phạm vi được chấm theo việc từ chối.

Sau khi cắt theo Điều, trên chỉ mục 618 đoạn:

| Hạng mục | Kết quả |
|---|---|
| Truy xuất, 80 câu trong phạm vi | 73/80 |
| Sinh câu trả lời, cả 100 câu | 68/100 |
| Sinh câu trả lời, 80 câu trong phạm vi | 48/80 |
| Mốc cũ, trước khi cắt theo Điều | sinh 60/100, truy xuất 69/80 |

Bản Gemini chưa chấm đủ 100 câu. Gói miễn phí giới hạn số request; một phần lượt gọi trả 503 hoặc 429.

## 9. Triển khai đang chạy

| Thành phần | Địa chỉ | Ghi chú |
|---|---|---|
| Giao diện | https://legal-rag-three.vercel.app | Trình duyệt gọi thẳng API |
| API | https://legal-rag-backend-z8am.onrender.com | Tự deploy khi đẩy nhánh `main` |

Render Free tắt máy sau khoảng 15 phút không có request. Lần hỏi kế tiếp có thể mất khoảng một phút để máy mở lại.

Gemini gói miễn phí thêm một giới hạn khoảng 5 request mỗi phút cho `gemini-3.8-flash`, và đôi khi trả 503 vì model phía Google đang đông. Hai lỗi này là tạm thời, không có nghĩa là key đã hết hạn mức cả ngày.

Secret (`GOOGLE_API_KEY`, `HF_TOKEN`, `QDRANT_URL`, `QDRANT_API_KEY`) chỉ đặt trên dashboard Render, không ghi vào git.

## 10. Hạn chế

- Kho public mới có Bộ luật. Câu về mức phạt hoặc mẫu hợp đồng chưa có văn bản để trích.
- Chưa đối chiếu song song quyền của người lao động và nghĩa vụ của người sử dụng lao động trên một tình huống.
- Chưa gắn ngày hiệu lực từng điều.
- Chất lượng sinh còn trượt một số câu trong bộ 100, nhất là khi đoạn truy xuất không đúng Điều.
- Bản public phụ thuộc hạn mức Gemini và máy Render ngủ.
- Lịch sử chat chỉ ở trình duyệt. Xóa dữ liệu site là mất phiên.

## 11. Việc nên làm tiếp

1. Chế độ đối chiếu trong Bộ luật: cùng một tình huống, xếp các điều liên quan cạnh nhau.
2. Nạp Nghị định 145/2020/NĐ-CP và Nghị định 12/2022/NĐ-CP để có chi tiết hợp đồng và mức phạt.
3. Gắn metadata hiệu lực cho từng văn bản.
4. Chấm lại bộ 100 câu trên Gemini khi còn hạn mức.

## 12. Chạy trên máy dev

Cần Docker Desktop, hoặc Python 3.11 và Node.js. OCR thêm Tesseract và Poppler. Local mặc định dùng Ollama `qwen2.5:3b` và Qdrant trên đĩa.

```bash
docker compose up -d --build
docker exec legal-rag-ollama ollama pull qwen2.5:3b
```

- Giao diện: http://localhost:3000
- API: http://127.0.0.1:8001 (ánh xạ cổng 8000 trong container)

Không dùng Docker:

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

```bash
cd frontend
npm install
npm run dev
```

Biến chính, xem `backend/.env.example`: `LLM_PROVIDER`, `EMBED_PROVIDER`, `HF_EMBED_MODEL`, `QDRANT_URL`, `TOP_K=5`, `RRF_K=60`. Để `QDRANT_URL` trống thì chạy local. `EMBED_PROVIDER=hf-inference` thì gọi Hugging Face và cần `HF_TOKEN`.

Endpoint chính: `GET /api/v1/health`, `GET /api/v1/documents`, `POST /api/v1/documents/upload`, `POST /api/v1/documents/ingest-disk`, `DELETE /api/v1/documents/{source}`, `POST /api/v1/chat`, `POST /api/v1/chat/stream`.
