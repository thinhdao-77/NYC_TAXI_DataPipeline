# CLAUDE.md

Hướng dẫn cho Claude Code khi làm việc trong repo này. Trả lời và viết tài liệu bằng **tiếng Việt**.

## Dự án

Kho dữ liệu NYC Yellow Taxi 2024–2025, dự án cá nhân cho CV. Pipeline: Parquet nguồn → Mage (ingestion) → DuckDB (staging) → dbt (ELT) → DDS Dimension/Fact + OLAP mart → Power BI.

**Đọc [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md) trước khi làm bất cứ việc gì.** File này ghi tình trạng hiện tại, cơ chế nạp và lưu ý vận hành DuckDB (mục 8) và nhật ký thay đổi.

## Quy tắc bắt buộc

- **Mỗi thay đổi phải cập nhật `docs/PROJECT_STATUS.md`** trong cùng lượt làm việc: sửa bảng trạng thái, thêm mục có ngày vào "Nhật ký thay đổi", và ghi rõ đã kiểm tra những gì.
- **Repo độc lập**: `origin` = `thinhdao-77/NYC_TAXI_DataPipeline`. Không thêm remote, không push, không tạo PR vào repo nhóm `nguyenanhtuan2702/NYC_TAXI` (từng merge nhầm PR #7, phải revert). Tạo PR bằng `gh` và kiểm tra base repo trước.
- **Làm từng bước theo thứ tự pipeline** (ingestion → staging → Dimension/Fact → OLAP → Power BI), xong và chạy thử một bước rồi mới sang bước sau.
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
.\tasks.ps1 qa full               # runner QA chỉ đọc trên DuckDB (smoke | deep | all | full)
.\tasks.ps1 export-bi             # xuất mart + Dimension ra data/bi/*.parquet cho Power BI
.\tasks.ps1 e2e                   # pipeline Mage nyc_taxi_e2e qua scheduler: ingest -> dbt build -> QA -> export-bi
.\tasks.ps1 status                # lần chạy thành công gần nhất, cảnh báo lỗi gần đây
```

Khi chạy `docker compose run/exec` với đường dẫn Linux từ Git Bash, đặt `MSYS_NO_PATHCONV=1` để Git Bash không đổi `/home/src/...` thành đường dẫn Windows.

## Cấu trúc

- `mage/`: ingestion (pipelines `ingest_zone_lookup`, `ingest_yellow_trips`) ghi vào schema `raw` của DuckDB; helper chung ở `mage/utils/duckdb_helpers.py`, DDL ở `sql/ddl/`. Pipeline `nyc_taxi_e2e` nối ingestion với các block `mage/custom/` (dbt build qua subprocess `/opt/dbt/bin/dbt`, QA, xuất Power BI); lịch ở `triggers.yaml` (cron theo UTC, Mage tự viết lại file; trigger API `manual_e2e` cho `tasks.ps1 e2e` qua `mage/utils/trigger_run.py`). Lỗi block gọi callback `mage/callbacks/notify_pipeline_failure.py` → `data/warehouse/alerts/pipeline_alerts.jsonl` + `ALERT_WEBHOOK_URL` (chỉ khi chạy qua scheduler, không với `mage run`). Ingestion chặn schema drift và nạp lại file TLC đã phát hành lại (`control.source_file_meta`). Giao diện Mage chỉ bind `127.0.0.1`. Hướng dẫn: `docs/guides/pipeline.md`.
- `dbt/`: transform chính, adapter **dbt-duckdb** (cùng file DuckDB với Mage). `sources.yml` trỏ `raw.*`; staging (`models/staging`, view trong schema `stage`) giữ đủ dòng và gắn cờ `is_*`, `is_valid_for_fact`; Dimension/Fact đọc staging bằng `ref()`. Dimension dùng SK ổn định từ khóa tự nhiên (vd `DateSK = YYYYMMDD`); `dim_location` là SCD Type 2 từ snapshot `snap_taxi_zone_lookup` (SK = `LocationID*100 + VersionNo`, Fact tra theo khoảng hiệu lực). Fact lọc `is_valid_for_fact`, incremental `delete+insert` theo `sourcefilename` (lấy batch mới hơn `max(batchid)`), nạp lại một file không làm trùng. OLAP mart (`models/olap_marts`, schema `olap`) dùng macro `olap_trip_measures`, chỉ lưu tổng cộng dồn được.
- `sql/ddl`: DDL `raw`/`control`. `sql/profiling`: truy vấn đo lỗi trên `raw.*` (chạy `.\tasks.ps1 profile <file>`). `sql/run_sql.py`: chạy SQL chỉ đọc cho `tasks.ps1 sql/profile`.
- `powerbi/`: `scripts/export_bi.py` (DuckDB → Parquet, read_only), `scripts/build_map_shapes.py` (shapefile → TopoJSON), `queries/*.pq` (Power Query), `dax/measures.dax`, `map_shapes/`. Power BI đọc Parquet, không đọc file DuckDB trực tiếp. Hướng dẫn: `docs/guides/powerbi.md`.
- `tests/run_quality_tests.py`: runner QA chỉ đọc trên DuckDB (`duckdb.connect(read_only=True)`), chạy trong container qua `.\tasks.ps1 qa`; không chạy được khi Mage/dbt đang ghi.
- `docs/guides/`: hướng dẫn từng phần. `docs/test_plans_and_logs/runs/`: log tự sinh, không commit (trừ một bản mẫu).

## Lưu ý về CI

- `.github/workflows/ci.yml`: chạy khi push lên **mọi nhánh** (không dùng sự kiện `pull_request`), kiểm tra cú pháp Python, `docker compose config`, `dbt parse`.
- `.github/workflows/auto-pr.yml`: push một nhánh khác `main` thì tự mở PR vào `main` nếu nhánh chưa có PR đang mở và có commit mới. PR do `GITHUB_TOKEN` tạo không kích hoạt workflow khác, vì vậy CI chạy theo `push`.
- Repo bật *Automatically delete head branches*: merge PR thì nhánh remote tự xóa; dọn nhánh local bằng `.\tasks.ps1 prune-branches`.
- Quy trình: tạo nhánh từ `main` mới nhất → commit → push → PR tự mở → kiểm tra → merge.

Nếu job báo *"account is locked due to a billing issue"* thì đó là vấn đề tài khoản GitHub, không phải code; chạy lại các bước này ở local để kiểm chứng.
