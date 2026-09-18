# Bước 0 — Thiết lập AGENTS.md & .cursor/rules

**Ngày:** 2026-09-18  
**Trạng thái:** ✅ HOÀN THÀNH  
**Phase:** 0 — Thiết lập context & workflow

---

## Mục tiêu bước này

Thiết lập hệ thống context và workflow cho toàn bộ dự án:
- AGENTS.md là nguồn sự thật duy nhất về trạng thái dự án
- `.cursor/rules/` cung cấp context domain và quy tắc code persistent cho mọi phiên agent

## Files tạo mới

| File | Vai trò |
|------|---------|
| `AGENTS.md` | Living document — dashboard, trạng thái, lịch sử gần |
| `.cursor/rules/00-project-context.mdc` | alwaysApply — nhận dạng dự án, domain, stack |
| `.cursor/rules/01-workflow.mdc` | alwaysApply — quy trình agent, bắt buộc test |
| `.cursor/rules/02-backend-rag.mdc` | globs `backend/**/*.py` — quy ước RAG/Python |
| `.cursor/rules/03-frontend.mdc` | globs `frontend/**/*.{ts,tsx}` — quy ước UI |
| `.cursor/rules/04-legal-domain.mdc` | alwaysApply — kiến thức domain HĐLĐ |
| `docs/agent-history/INDEX.md` | Index toàn bộ lịch sử bước |

## Files thay đổi code

_Không có file code nào bị thay đổi._

## Quyết định

- Tách lịch sử chi tiết ra `docs/agent-history/` để AGENTS.md không phình to
- Dùng `.mdc` rules theo cơ chế Cursor alwaysApply / globs để tự động load đúng context
- Recent history trong AGENTS.md tối đa 5 dòng, archive khi tràn

## Test checklist

| Kiểm tra | Kết quả |
|---------|---------|
| AGENTS.md tồn tại và đọc được | ✅ |
| Tất cả 5 file `.mdc` tồn tại trong `.cursor/rules/` | ✅ |
| `docs/agent-history/INDEX.md` tồn tại | ✅ |
| Không có file code nào bị thay đổi ngoài ý muốn | ✅ |

> Bước 0 là bước setup, không có test chức năng phần mềm. Test checklist ở các bước sau sẽ bao gồm kiểm tra API/UI thực tế.

## Bước tiếp theo gợi ý

**Bước 1:** Nạp văn bản pháp luật lao động cốt lõi vào `backend/data/` theo quy ước đặt tên trong `02-backend-rag.mdc`:
- `bo-luat-lao-dong-45-2019-QH14.pdf`
- `nghi-dinh-145-2020-ND-CP.pdf`
- `thong-tu-10-2020-TT-BLDTBXH.pdf`
- `nghi-dinh-12-2022-ND-CP.pdf`

Sau đó upload qua UI hoặc gọi API `POST /api/v1/documents/upload`.
