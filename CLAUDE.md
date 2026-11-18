# CLAUDE.md

Hướng dẫn cho Claude Code khi làm việc trong repo này. Trả lời và viết tài liệu bằng **tiếng Việt**.

## Dự án

Kho dữ liệu NYC Yellow Taxi 2024–2025, dự án cá nhân cho CV. Pipeline: Parquet nguồn → Mage (ingestion) → DuckDB (staging) → dbt (ELT) → DDS Dimension/Fact + OLAP mart → Power BI.

**Đọc [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md) trước khi làm bất cứ việc gì.** File này ghi tình trạng hiện tại, lộ trình chuyển sang DuckDB (mục 8) và nhật ký thay đổi.

## Quy tắc bắt buộc

- **Mỗi thay đổi phải cập nhật `docs/PROJECT_STATUS.md`** trong cùng lượt làm việc: sửa bảng trạng thái, thêm mục có ngày vào "Nhật ký thay đổi", và ghi rõ đã kiểm tra những gì.
- **Repo độc lập**: `origin` = `thinhdao-77/NYC_TAXI_DataPipeline`. Không thêm remote, không push, không tạo PR vào repo nhóm `nguyenanhtuan2702/NYC_TAXI` (từng merge nhầm PR #7, phải revert). Tạo PR bằng `gh` và kiểm tra base repo trước.
- **Làm từng bước theo thứ tự pipeline**, xong và chạy thử một bước rồi mới sang bước sau (xem mục 8 của PROJECT_STATUS).
- Chỉ commit/push khi người dùng yêu cầu.

## Môi trường và phụ thuộc

- Chỉ có một service Docker: `mage` (image Mage 0.9.79, **Python 3.10**), ghim theo digest trong `Dockerfile`.
- **dbt cài trong venv riêng `/opt/dbt`** (lệnh `dbt` là symlink). Không `pip install` gói dbt vào môi trường Python của Mage: dbt-core 1.12 cần `click>=8.3`, làm hỏng CLI Mage (`typer 0.9`).
  - `requirements.txt`: gói thêm cho Mage (chỉ `duckdb`).
  - `requirements-dbt.txt`: gói cho venv dbt.
- **duckdb phải là 1.5.x** ở cả hai file (duckdb 2.x cần Python >= 3.11). Mage và dbt phải cùng phiên bản vì đọc/ghi chung một file.
- File DuckDB: `data/warehouse/nyc_taxi.duckdb` (bind mount, không commit). Chỉ một tiến trình được ghi tại một thời điểm.
- Biến cấu hình `DUCKDB_*`, `RAW_DATA_DIR` đều có mặc định trong `docker-compose.yml`; `.env` không bắt buộc.

## Lệnh thường dùng (PowerShell, từ gốc repo)

```powershell
.\tasks.ps1 help                 # danh sách lệnh
.\tasks.ps1 up                   # docker compose up -d --build
.\tasks.ps1 sql "show all tables" # truy vấn DuckDB chỉ đọc
.\tasks.ps1 dbt-build [selector]  # dbt trong container
.\tasks.ps1 qa smoke              # runner QA (chưa chuyển sang DuckDB)
```

Khi chạy `docker compose run/exec` với đường dẫn Linux từ Git Bash, đặt `MSYS_NO_PATHCONV=1` để Git Bash không đổi `/home/src/...` thành đường dẫn Windows.

## Cấu trúc

- `mage/`: ingestion (pipelines `ingest_zone_lookup`, `ingest_yellow_trips`) ghi vào schema `raw` của DuckDB; helper chung ở `mage/utils/duckdb_helpers.py`, DDL ở `sql/ddl/`.
- `dbt/`: transform chính, adapter **dbt-duckdb** (cùng file DuckDB với Mage). `sources.yml` trỏ `raw.*`; staging (`models/staging`, view trong schema `stage`) giữ đủ dòng và gắn cờ `is_*`, `is_valid_for_fact`; Dimension/Fact đọc staging bằng `ref()`. Dimension dùng SK ổn định từ khóa tự nhiên (vd `DateSK = YYYYMMDD`); Fact incremental theo `batch_id`.
- `sql/ddl`: DDL `raw`/`control`. `sql/profiling`: truy vấn đo lỗi trên `raw.*` (chạy `.\tasks.ps1 profile <file>`). `sql/run_sql.py`: chạy SQL chỉ đọc cho `tasks.ps1 sql/profile`. `sql/warehouse`: bản SQL thủ công cũ (PostgreSQL), chỉ tham khảo.
- `tests/run_quality_tests.py`: runner QA chỉ đọc.
- `docs/guides/`: hướng dẫn từng phần. `docs/02_test_plans_and_logs/runs/`: log tự sinh, không commit (trừ một bản mẫu).

## Lưu ý về CI

- `.github/workflows/ci.yml`: chạy khi push lên **mọi nhánh** (không dùng sự kiện `pull_request`), kiểm tra cú pháp Python, `docker compose config`, `dbt parse`.
- `.github/workflows/auto-pr.yml`: push một nhánh khác `main` thì tự mở PR vào `main` nếu nhánh chưa có PR đang mở và có commit mới. PR do `GITHUB_TOKEN` tạo không kích hoạt workflow khác, vì vậy CI chạy theo `push`.
- Repo bật *Automatically delete head branches*: merge PR thì nhánh remote tự xóa; dọn nhánh local bằng `.\tasks.ps1 prune-branches`.
- Quy trình: tạo nhánh từ `main` mới nhất → commit → push → PR tự mở → kiểm tra → merge.

Nếu job báo *"account is locked due to a billing issue"* thì đó là vấn đề tài khoản GitHub, không phải code; chạy lại các bước này ở local để kiểm chứng.
