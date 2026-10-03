# Bước 11 — Session History Sidebar

**Ngày:** 2026-10-03
**Trạng thái:** ✅ HOÀN THÀNH
**Phase:** 3

## Mục tiêu bước này

Thêm sidebar trái liệt kê nhiều phiên hội thoại. Mỗi phiên lưu riêng trong localStorage, tiêu đề tự động = câu hỏi đầu tiên. Người dùng có thể chuyển phiên, tạo mới, xóa, và thu gọn sidebar.

## Files thay đổi

| File | Thay đổi |
|---|---|
| `frontend/src/lib/types.ts` | Thêm interface `Session` |
| `frontend/src/lib/sessions.ts` | Tạo mới — helpers localStorage: `loadSessions`, `saveSession`, `deleteSession`, `newSession`, `loadActiveId`, `saveActiveId`, `getOrCreateInitialSession` |
| `frontend/src/components/SessionSidebar.tsx` | Tạo mới — sidebar phiên: danh sách, tạo mới, xóa, collapse toggle |
| `frontend/src/app/page.tsx` | Nâng state session lên đây; render `SessionSidebar` + `ChatPanel` cạnh nhau |
| `frontend/src/components/ChatPanel.tsx` | Bỏ localStorage cũ; nhận props `session` + `onUpdate`; tự đặt title từ câu hỏi đầu |
| `.cursor/rules/03-frontend.mdc` | Cập nhật cấu trúc file, thêm quy tắc session |
| `AGENTS.md` | Cập nhật checklist, lộ trình, recent history |
| `docs/agent-history/INDEX.md` | Thêm dòng bước 11 |

## Quyết định

- State session nâng lên `page.tsx`, `ChatPanel` không đọc/ghi localStorage trực tiếp.
- `Session.title` tự đặt khi `useEffect([messages])` chạy lần đầu có tin nhắn user.
- Giữ tối đa 30 phiên; khi vượt, phiên cũ nhất bị cắt trong `saveSession`.
- Sidebar có chế độ collapsed (`w-12`) chỉ hiện icon phiên; mở rộng (`w-56`) hiện danh sách đầy đủ.
- Khi chuyển phiên, stream cũ bị abort.

## Test Checklist

| Kiểm tra | Kết quả |
|---|---|
| TypeScript types `Session` | ✅ |
| ESLint: `npm run lint` | ✅ No warnings or errors |
| Build: `npm run build` | ✅ Compiled successfully |
| Không có `STORAGE_KEY` cũ trong ChatPanel | ✅ |
| Disclaimer footer vẫn còn | ✅ |
| Nút Stop streaming vẫn còn | ✅ |
| SUGGESTED_QUESTIONS vẫn đúng domain | ✅ |

## Vấn đề gặp phải

- `useEffect([messages])` gọi `onUpdate` mỗi lần render có thể tạo vòng lặp nếu parent setState trigger re-render. Xử lý bằng `sessionIdRef` và tách rõ effect update vs effect switch phiên.

## Bước tiếp theo gợi ý

- Bước 6: Chế độ đối chiếu quy định (cần nạp thêm Nghị định 145/2020 trước).
- Cải thiện retrieval: khi hit một Điều, kéo thêm các khoản cùng Điều vào context.
