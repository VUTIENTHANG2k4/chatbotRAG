# Bước 4 — Cập nhật UI (gợi ý câu hỏi, header)

**Ngày:** 2026-09-18  
**Trạng thái:** ✅ HOÀN THÀNH  
**Phase:** 2

## Mục tiêu bước này
Đưa giao diện chat bám sát domain hợp đồng lao động Việt Nam: sửa bộ câu hỏi gợi ý và tiêu đề/định vị sản phẩm trên UI.

## Files thay đổi
| File | Thay đổi |
|---|---|
| `frontend/src/components/ChatPanel.tsx` | Thay `SUGGESTED_QUESTIONS` sang các tình huống HĐLĐ thực tế; đổi tiêu đề Empty State; cập nhật mô tả tập trung NLĐ/NSDLĐ |
| `frontend/src/components/Header.tsx` | Đổi tên sản phẩm và phụ đề sang pháp luật lao động/HĐLĐ |

## Quyết định
- Giữ disclaimer pháp lý ở input footer để nhắc giới hạn sử dụng.
- Dùng ngôn ngữ tình huống thực tế (nghỉ việc, thử việc, lương, gia hạn HĐLĐ) thay vì câu hỏi ngoài domain.
- Không đổi kiến trúc gọi API; `API_BASE="/api/backend"` vẫn giữ nguyên.

## Test Checklist
| Kiểm tra | Kết quả |
|---|---|
| Không có TypeScript error | ✅ `npm run build` PASS |
| Component render đúng với dữ liệu mẫu | ✅ `next build` compile thành công, không lỗi runtime compile |
| API call dùng đúng `API_BASE="/api/backend"` | ✅ Không thay đổi `frontend/src/lib/api.ts` |
| Disclaimer pháp lý vẫn còn ở footer input | ✅ Vẫn giữ trong `ChatPanel.tsx` |
| `SUGGESTED_QUESTIONS` đúng domain HĐLĐ | ✅ 4 câu mới đều thuộc HĐLĐ |

## Vấn đề gặp phải
- Lần đầu chạy lint thiếu dependency frontend (`next` chưa cài trong `node_modules`).
- Đã xử lý bằng `npm install`, sau đó:
  - `npm run lint` ✅
  - `npm run build` ✅

## Bước tiếp theo gợi ý
- Bước 5: thêm filter theo `doc_type` và `year` từ frontend xuống API chat/documents để lọc đúng văn bản áp dụng.
