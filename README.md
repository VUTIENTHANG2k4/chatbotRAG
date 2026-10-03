# Báo cáo dự án: Chatbot hỏi đáp pháp luật lao động Việt Nam

Chatbot dùng kỹ thuật RAG (truy xuất tài liệu rồi mới sinh câu trả lời) để tra cứu quy định hợp đồng lao động. Câu trả lời bám văn bản đã nạp, có trích điều luật, và viết bằng tiếng Việt.

Link dự án: https://legal-rag-three.vercel.app

## 1. Mục tiêu

Giúp người lao động và doanh nghiệp hỏi một tình huống cụ thể rồi nhận lại quy định tương ứng, thay vì tự tìm trong cả bộ luật.

Hệ thống chỉ được trả lời từ tài liệu đã nạp. Mỗi câu trả lời phải nêu điều, khoản hoặc văn bản nguồn. Câu nằm ngoài kho tài liệu thì từ chối, không bịa số ngày, mức lương hay mức phạt.

## 2. Phạm vi

- Hỏi đáp trên Văn bản hợp nhất Bộ luật Lao động (18/VBHN-VPQH).
- Tìm kiếm lai: vector và từ khóa, rồi gộp bằng Reciprocal Rank Fusion.
- Cắt văn bản theo từng Điều, lặp tiêu đề Điều ở mọi đoạn con.
- Giao diện chat, nhiều phiên hội thoại, lọc loại văn bản và năm, kèm nguồn trích dẫn.

## 3. Người dùng

| Đối tượng | Việc cần làm |
|---|---|
| Người lao động | Tra quyền, nghĩa vụ, thời hạn báo trước, thử việc, nghỉ phép |
| Doanh nghiệp, nhân sự | Kiểm tra một tình huống hợp đồng có đúng khung luật đã nạp hay không |

Câu trả lời là tra cứu, không thay tư vấn pháp lý.

## 4. Cách hệ thống trả lời

1. Câu hỏi được embed bằng `keepitreal/vietnamese-sbert` (768 chiều, đã chuẩn hóa).
2. Qdrant tìm các đoạn gần nghĩa. BM25 tìm các đoạn trùng từ khóa pháp lý.
3. Hai danh sách gộp bằng RRF (`k = 60`), lấy top 5.
4. Các đoạn đó đưa vào prompt. Mô hình phải nêu số liệu đúng như tài liệu (ngày, giờ, tháng, phần trăm, mức tiền) và đánh dấu nguồn `[1]`, `[2]`.
5. Giao diện hiện câu trả lời cùng thẻ nguồn.

## 5. Công nghệ

| Lớp | Local | Public |
|---|---|---|
| Giao diện | Next.js 14, TypeScript, Tailwind | Vercel |
| API | FastAPI, LangChain | Render Free, Singapore, 512 MB RAM |
| Mô hình sinh | Ollama `qwen2.5:3b` | Gemini `gemini-3.8-flash` |
| Embedding | PyTorch, model trên máy | Cùng model, qua Hugging Face Inference |
| Vector | Qdrant file trên đĩa | Qdrant Cloud, `australia-southeast1` |
| Từ khóa | BM25 ghi ra file pickle | BM25 dựng trong RAM lúc khởi động, từ payload Qdrant |

## 6. Dữ liệu

Một file: 18-vbhn-vpqh.pdf, bản scan Văn bản hợp nhất Bộ luật Lao động. Chữ được OCR sẵn, rồi cắt lại theo Điều.

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



