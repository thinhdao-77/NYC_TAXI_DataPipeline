# Tình trạng dự án NYC Yellow Taxi Data Warehouse

> Cập nhật: 17/11/2026 — nhánh `main` của repo độc lập `thinhdao-77/NYC_TAXI_DataPipeline` (không còn là fork của repo nhóm).
> File này được cập nhật cùng mỗi thay đổi. Lịch sử ở [mục 7](#7-nhật-ký-thay-đổi).

## 1. Mục tiêu

Xây dựng quy trình ELT và kho dữ liệu cho **NYC Yellow Taxi Trip Records 2024–2025**:
Parquet nguồn → Mage ingestion → DuckDB (`raw`) → dbt staging → Dimension/Fact → OLAP mart → Power BI. Đang chuyển từ PostgreSQL sang DuckDB, xem [mục 8](#8-chuyển-sang-duckdb).

## 2. Mức độ hoàn thành

| Hạng mục | Trạng thái | Ghi chú |
|---|---|---|
| Hạ tầng Docker (Mage + DuckDB) | **Đã chuyển sang DuckDB, đã chạy thử** | Chỉ còn service `mage` (Mage 0.9.79 + duckdb 1.5.6; dbt 1.12 trong venv `/opt/dbt`); file DuckDB ở `data/warehouse/nyc_taxi.duckdb`. Xem [mục 8](#8-chuyển-sang-duckdb) |
| DDL ingestion (DuckDB) | **Hoàn thành, đã chạy** | `sql/ddl/`: schema `raw`, `control`; bảng `raw.yellow_tripdata`, `raw.taxi_zone_lookup`, `control.etl_control`. Block nạp tự chạy DDL (idempotent) |
| Nạp Taxi Zone Lookup | **Hoàn thành (DuckDB), đã chạy** | Pipeline `ingest_zone_lookup` → `raw.taxi_zone_lookup` (265 dòng) |
| Nạp Yellow Taxi Parquet | **Hoàn thành (DuckDB), đã chạy 3 tháng** | Pipeline `ingest_yellow_trips` → `raw.yellow_tripdata`: tự tải file, retry, nạp mỗi file trong một transaction, LSET, log theo file. Đã nạp 2024-01, 2024-02, 2025-01; chưa nạp đủ 24 tháng |
| Staging (dbt, DuckDB) | **Hoàn thành, đã chạy trên 24 tháng** | `stage.stg_yellow_taxi_trips`, `stage.stg_taxi_zone_lookup` (view) đọc `raw.*`; 15 cờ chất lượng + `is_valid_for_fact`; 13 test PASS (~12 s). Hướng dẫn: [guides/staging.md](guides/staging.md) |
| Profiling dữ liệu nguồn | **Hoàn thành (DuckDB), đã chạy** | `sql/profiling/02..11` trên `raw.*`, mỗi file 3–14 s trên ~90 triệu dòng; chạy bằng `.\tasks.ps1 profile <file>` |
| dbt project | **Chạy trên DuckDB** | `profiles.yml` dùng adapter `duckdb` (cùng file với Mage), `sources.yml` trỏ `raw.*`; dbt-core 1.12.7, dbt-duckdb 1.11.1 |
| Dimension (8 bảng) | Có model dbt (đọc staging bằng `ref()`), **chưa chạy trên DuckDB** (bước 4) | `dbt/models/dds/dimensions/`; SK ổn định, dòng Unknown `-1`; 30 test schema + 1 test Unknown member |
| Fact `facttaxitrip` | Có model dbt (đọc staging bằng `ref()`), **chưa chạy trên DuckDB** (bước 4) | `dbt/models/dds/facts/fact_taxi_trips.sql`, incremental theo `batch_id`, 16 test |
| SQL thủ công DDS | Lưu để tham khảo | `sql/warehouse/01..05` (Dimension idempotent + Fact + verify) |
| Bộ kiểm thử QA (Stage/Dimension) | Hoàn thành | `tests/run_quality_tests.py`, chỉ đọc, suite `smoke`/`deep`/`all` |
| Test plan + log | Hoàn thành | `docs/02_test_plans_and_logs/` (giữ 1 lần chạy mẫu `run_20261026T034420Z`) |
| CI / tự động hóa GitHub | **Hoàn thành, đã chạy thật trên GitHub** | `ci.yml` chạy khi push mọi nhánh; `auto-pr.yml` tự mở PR vào `main`; repo tự xóa nhánh sau khi merge |
| Lệnh tiện ích | Hoàn thành | `tasks.ps1` (up/down/shell/sql/ingest-zones/ingest/profile/dbt-*/qa/prune-branches) |
| Báo cáo thành phần | Một phần | `docs/03_reports/sections/` (Vân, Khoa) |
| Data modeling docs | Một phần | `docs/01_data_modeling/modeling.pdf` (Giai đoạn 1 của nhóm: business event, 8 Dimension, Fact, measures, truy vấn kiểm chứng Star Schema); sơ đồ Star Schema chỉ có qua link Google Drive trong PDF |
| OLAP mart | **Chưa có** | `dbt/models/olap_marts/{basic,advanced}` rỗng |
| Pipeline ELT end-to-end | **Chưa có** | Cần pipeline Mage: ingest → `dbt build` |
| Power BI | **Chưa có** | `powerbi/` rỗng |

## 3. Chi tiết phần đã làm

### 3.1 Ingestion (DuckDB)
Hướng dẫn: [docs/guides/ingestion.md](guides/ingestion.md).
- `raw.yellow_tripdata` giữ nguyên dữ liệu nguồn + cột kiểm toán (`source_file_name`, `source_row_number`, `batch_id`, `load_datetime`); `cbd_congestion_fee` chỉ có từ 2025-01 (NULL với 2024).
- Nạp bằng `INSERT ... SELECT FROM read_parquet(...)`, khớp cột theo tên không phân biệt hoa thường; mỗi file: `DELETE` dòng cũ + `INSERT` trong một transaction.
- `batch_id` = `YYYYMMDDHHMMSS`, luôn lớn hơn giá trị lớn nhất trong log (`next_batch_id`).
- Kết nối có retry khi file DuckDB bị tiến trình khác khóa (2, 4, 8, 16 s).
- Số đo (16/11/2026): mỗi tháng ~3–3,5 triệu dòng, nạp một tháng (gồm tải ~50 MB) ~24 s; file DuckDB ~100 MB/tháng (336 MB sau 3 tháng, có 2 lần nạp lại). Trước đây trên PostgreSQL: ~20 GB cho 24 tháng.

### 3.2 Dimension (dbt)

| Model | Bảng | SK | Nguồn |
|---|---|---|---|
| `dim_date` | `dds.dimdate` | `YYYYMMDD` | sinh 2024-01-01..2025-12-31 |
| `dim_time` | `dds.dimtime` | `hour*100+minute` | sinh 24×60 |
| `dim_location` | `dds.dimlocation` | = `LocationID` | zone lookup |
| `dim_vendor` | `dds.dimvendor` | = `VendorID` | trips; mã ngoài 1/2 → Unknown |
| `dim_payment_type` | `dds.dimpaymenttype` | = `PaymentTypeID` | trips; mã 0 → Unknown |
| `dim_rate_code` | `dds.dimratecode` | = `RateCodeID` | trips; NULL → 99 Unknown |
| `dim_passenger_group` | `dds.dimpassengergroup` | 1..3 | tĩnh (LARGE tới 9999) |
| `dim_distance_group` | `dds.dimdistancegroup` | 1..3 | tĩnh, `NUMERIC(10,4)` |

Logic nghiệp vụ giữ nguyên bản SQL đã sửa trong `feat/fact-thinh`. Khác biệt: SK không còn là `SERIAL` mà sinh từ khóa tự nhiên, để Fact incremental không bị lệch khóa khi Dimension build lại. Tên bảng/cột vật lý giữ nguyên, nên runner QA vẫn dùng được.

### 3.3 Fact (dbt)
Grain: một chuyến đi hợp lệ. Lọc `dropoff > pickup`, pickup trong 2024–2025, `fare/total/distance >= 0`. Tra khóa bằng `LEFT JOIN` + `COALESCE(sk, -1)`. Nạp gia tăng theo `batch_id > max(batchid)`.

### 3.4 QA
Lần chạy 26/10 (`run_20261026T034420Z`): 19 PASS, 8 FAIL, 14 BLOCKED. 8 FAIL đều do bảng Dimension chưa tồn tại trong DB lúc test.

## 4. Vấn đề và rủi ro còn mở

1. **Chưa chạy dbt trên database thật** (Docker chưa bật khi refactor). Cần `.\tasks.ps1 dbt-build` rồi chạy lại QA.
2. Hai cách build DDS cùng tồn tại (dbt và `sql/warehouse/`). Không được trộn: dbt build lại Dimension sẽ xóa khóa ngoại do `03_create_fact.sql` tạo. Nên chọn dbt làm chuẩn và cân nhắc bỏ bản SQL khi dbt đã ổn.
3. Fact dbt không có `TripSK` (bản SQL có `BIGSERIAL`). Cần thống nhất nếu Power BI cần khóa chuyến đi.
4. Dimension đọc `SELECT DISTINCT` từ bảng trips (3 lần: vendor, payment, ratecode). Trên DuckDB (lưu theo cột) dự kiến nhanh, cần đo ở bước 5.
5. Fact incremental dựa vào `batch_id` tăng dần: nếu nạp lại một file cũ với `batch_id` mới, chuyến đi sẽ bị trùng trong Fact. **Đã lên kế hoạch sửa ở bước 4–5** (`delete+insert` theo `source_file_name`, xem mục 8).
6. Mage lưu lịch sử chạy theo uuid pipeline. Sau khi đổi tên (`letter_01_...` → `ingest_zone_lookup`, `ingest_trips_to_postgres` → `ingest_yellow_trips`), lịch sử cũ trên Mage UI không hiện dưới tên mới. LSET không bị ảnh hưởng vì `control.etl_control` trên DuckDB bắt đầu mới.
8. ~~`sources.yml` trỏ bảng PostgreSQL cũ~~: đã xử lý ở bước 3 (`sources.yml` trỏ `raw.*`, DDS đọc staging qua `ref()`).
10. `is_total_mismatch` dựa trên quy luật quan sát từ dữ liệu (`extra` đã gồm phụ phí ở nhiều dòng), không phải định nghĩa chính thức của TLC; còn 384.360 dòng lệch thật (0,43%) chưa phân tích nguyên nhân.
9. DuckDB không tự thu hồi chỗ của dòng đã xóa khi nạp lại một file; nạp lại nhiều lần làm file phình. Thu gọn bằng `COPY FROM DATABASE` sang file mới khi cần.
7. `data/reference/taxi_zones.zip` (nhị phân) vẫn nằm trong git.

## 5. Cấu trúc thư mục hiện tại

```text
.
├── .github/workflows/ci.yml
├── data/{raw,reference,warehouse}, download_raw.ps1
├── dbt/                      # transform chính: sources → dds (dims, facts) → olap_marts
├── mage/                     # ingestion: pipelines ingest_zone_lookup, ingest_yellow_trips; utils/duckdb_helpers.py
├── sql/
│   ├── ddl/                  # DDL DuckDB (raw, control); block ingestion tự chạy
│   ├── profiling/            # truy vấn kiểm tra dữ liệu nguồn
│   └── warehouse/            # SQL thủ công Dimension/Fact (tham khảo)
├── tests/                    # runner QA chỉ đọc
├── powerbi/
├── docs/
│   ├── PROJECT_STATUS.md     # file này
│   ├── guides/               # ingestion, staging (cũ, PostgreSQL), dimension, dimension_handover, fact, testing
│   ├── 01_data_modeling/
│   ├── 02_test_plans_and_logs/
│   └── 03_reports/
├── docker-compose.yml, Dockerfile, requirements.txt, requirements-dbt.txt, tasks.ps1, .env.example, README.md, CLAUDE.md
```

## 6. Việc nên làm tiếp

1. Tiếp tục chuyển sang DuckDB: bước 4 (ETL/ELT) → bước 6 (Power BI), xem [mục 8](#8-chuyển-sang-duckdb).
2. Quyết định giữ hay bỏ `sql/warehouse/`; thống nhất `TripSK` cho Fact.
3. Chuyển nội dung `modeling.pdf` thành markdown + ERD trong repo (sơ đồ hiện chỉ có qua link Google Drive) và bổ sung data dictionary.
4. Xây OLAP mart (`dbt/models/olap_marts/`).
5. Pipeline Mage end-to-end: ingest → `dbt build`.
6. Dashboard Power BI.

## 7. Nhật ký thay đổi

### 18/11/2026 — DuckDB bước 3: Staging
- **dbt chuyển sang DuckDB:** `profiles.yml` dùng `type: duckdb`, `path` = `DUCKDB_PATH` (cùng file với Mage), `settings` `memory_limit`/`threads` từ biến môi trường. Bỏ `temp_directory` khỏi `settings` vì dbt-duckdb áp settings lên mọi cursor và DuckDB báo *"Cannot switch temporary directory after the current one has been used"*; dbt dùng thư mục tạm mặc định `nyc_taxi.duckdb.tmp`. Bỏ `dbt-postgres` khỏi `requirements-dbt.txt` (image build lại, chỉ còn plugin duckdb). CI: `dbt parse` dùng `DUCKDB_PATH` tạm thay `POSTGRES_PASSWORD`; `compileall` thêm thư mục `sql/`.
- `dbt/models/sources.yml`: source `raw` (`yellow_tripdata`, `taxi_zone_lookup`, `loaded_at_field: load_datetime`).
- Model staging (view, schema `stage`): `stg_taxi_zone_lookup` (trim, `is_unknown_zone`), `stg_yellow_taxi_trips` (giữ đủ mọi dòng, cột dẫn xuất `source_month`, `trip_duration_minutes`, `component_total_amount`; 14 cờ `is_*` + `is_valid_for_fact`). Giữ tên cột cũ nên 4 Dimension và Fact chỉ đổi `source('stage', ...)` → `ref('stg_...')`.
- **Phân tích `is_total_mismatch`:** công thức cộng thẳng cho 28.848.843 dòng lệch (32%). Kiểm định hai giả thuyết: (1) Flex Fare có cột phụ phí NULL nhưng total vẫn gồm phụ phí (11,27 triệu dòng lệch đúng +2,50); (2) `extra` đã gồm phụ phí ùn tắc/CBD/sân bay (14,09 triệu dòng lệch đúng −(ùn tắc+CBD), thêm ~1,45 triệu dòng với phí sân bay). Định nghĩa lại: thêm `is_surcharge_missing`; `is_total_mismatch` chỉ bật khi không khớp cả 4 cách tính. Còn 384.360 dòng (0,43%).
- Test staging (`dbt/models/staging/schema.yml`, `dbt/tests/staging/`): `not_null`, `unique`, `relationships` (mức warn), `assert_stg_trips_match_raw`, `assert_stg_trips_unique_source_row`. Test trùng dòng viết lại từ `GROUP BY (file, rn)` (122 s) sang kiểm tra `min = 1`, `max = N`, `sum = N(N+1)/2` theo file (0,7 s); kiểm chứng trên bản sao tạm: bắt được nạp trùng một file và mất một dòng.
- `sql/profiling/*.sql`: đổi bảng sang `raw.yellow_tripdata` / `raw.taxi_zone_lookup`; file 10 dùng `SET VARIABLE f` + `getvariable('f')` thay biến psql; file 11 thêm chú thích kết quả phân tích tổng tiền.
- Thêm `sql/run_sql.py` (chạy từng câu lệnh, in mọi kết quả, tắt thanh tiến trình, chế độ chỉ đọc); `tasks.ps1 sql/profile` dùng script này thay one-liner cũ (trước chỉ in kết quả câu cuối và bị thanh tiến trình làm rối output).
- `docs/guides/staging.md` viết lại cho DuckDB/dbt (bản PostgreSQL cũ còn trong lịch sử git).
- **Dữ liệu tại thời điểm kiểm tra:** `raw.yellow_tripdata` 89.892.322 dòng, đủ 24 file (2024-01 → 2025-12; người dùng đã chạy nạp đủ, `control.etl_control` có 26 lượt SUCCESS, không có FAILED).
- **Kiểm tra (đạt):** image build lại OK (`dbt --version`: chỉ plugin duckdb 1.11.1); `dbt build --select staging`: 2 view + 13 test PASS trong ~12 s; `dbt parse` và `dbt ls` thấy đủ 11 model (2 staging, 8 Dimension, 1 Fact); cả 10 file profiling chạy không lỗi (3–14 s mỗi file), `GROUPING()` trong file 06 cho kết quả đúng; `compileall`, `docker compose config` OK; `tasks.ps1` parse OK.
- Chưa làm: chạy Dimension/Fact trên DuckDB (bước 4).

### 17/11/2026 — Commit tài liệu Data Modeling
- Commit `docs/01_data_modeling/modeling.pdf` (10 trang, 321 KB, xuất từ Google Docs) theo yêu cầu. Đã đọc nội dung trước khi đưa lên repo public: không có email, mã số sinh viên, số điện thoại; có nhắc "Nhóm 2" và một link Google Drive chia sẻ công khai tới sơ đồ Star Schema (trang 5).
- CLAUDE.md: bỏ quy tắc "không commit modeling.pdf".

### 17/11/2026 — Bỏ thư mục `data/sample/`
- Xóa `data/sample/.gitkeep` (thư mục rỗng, không dùng); bỏ dòng tương ứng trong cây thư mục của README và PROJECT_STATUS, bỏ ngoại lệ `!data/sample/*.parquet` trong `.gitignore`.

### 17/11/2026 — Tài khoản GitHub mở khóa, kiểm chứng CI và Auto PR
- Người dùng thêm phương thức thanh toán; trang Billing: gói GitHub Free + Copilot Free ($0), không có khoản nợ đang chờ. Actions chạy lại được.
- Chạy lại run `44000060286` (Auto PR): **success**, tạo PR #2 <https://github.com/thinhdao-77/NYC_TAXI_DataPipeline/pull/2> (tác giả `github-actions`, `refactor/project-structure` → `main`, liệt kê 3 commit `ccf388a`, `7f519b6`, `37e08c9`).
- Chạy lại run `44000060109` (CI): **success** trong 36 s, đủ các bước cài phụ thuộc, `compileall`, `docker compose config`, `dbt parse` trên Python 3.12.
- `gh pr checks 2`: hiện cả `checks` và `open-pr` đều pass, xác nhận kết quả CI chạy theo `push` vẫn gắn lên PR.
- PR #2 merge lúc 17/11/2026 02:17 UTC (merge commit `7dc00b6`); nhánh `refactor/project-structure` trên GitHub **tự xóa** (git báo `[gone]`). Local: `git pull` lên `7dc00b6`, `.\tasks.ps1 prune-branches` xóa nhánh local (và đã bỏ qua đúng khi nhánh đó đang checkout). Toàn bộ quy trình nhánh → PR tự mở → CI → merge → tự xóa nhánh đã chạy thật.

### 17/11/2026 — Tự mở PR và tự xóa nhánh
- Thêm `.github/workflows/auto-pr.yml`: push nhánh khác `main` → nếu nhánh chưa có PR đang mở và có commit mới so với `main` thì mở PR vào `main` (tiêu đề = dòng đầu commit mới nhất, nội dung liệt kê các commit). Bỏ qua sự kiện xóa nhánh. So sánh theo SHA để không lỗi với tên nhánh có `/`. Biến GitHub truyền qua `env`, không chèn trực tiếp vào script (tránh injection).
- `ci.yml`: đổi trigger từ `push` (main, develop) + `pull_request` sang `push` mọi nhánh, vì PR do `GITHUB_TOKEN` tạo không kích hoạt `pull_request`; thêm `concurrency` (hủy lượt cũ khi push liên tiếp) và `permissions: contents: read`.
- Cài đặt repo (qua `gh api`): bật `delete_branch_on_merge` (tự xóa nhánh sau khi merge); bật *Allow GitHub Actions to create and approve pull requests* (`can_approve_pull_request_reviews`), quyền mặc định của token vẫn là `read`.
- Local: `git config fetch.prune true` (tự bỏ ref của nhánh remote đã xóa); thêm `.\tasks.ps1 prune-branches` (xóa nhánh local có upstream `gone`, dùng `git branch -d` nên giữ nhánh chưa merge).
- CLAUDE.md: cập nhật mục CI và quy trình làm việc với nhánh.
- **Kiểm tra:**
  - YAML hai workflow parse được (PyYAML); trigger, job, permissions đúng như thiết kế.
  - Chạy thử script của `auto-pr` (thay `gh pr create` bằng `echo`) trên repo thật: nhánh có commit mới và chưa có PR → dựng đúng lệnh tạo PR; SHA trùng `main` → "không có commit mới", không tạo PR.
  - `prune-branches`: không có gì để dọn → báo đúng; giả lập nhánh có upstream `gone` → xóa đúng nhánh đó.
  - **Chưa chạy được trên GitHub Actions** vì tài khoản đang bị khóa thanh toán; `actionlint` chưa chạy (lệnh `docker run` bị chặn quyền).
- Push commit `37e08c9` (17/11/2026): cả `Auto PR` (run 44000060286) và `CI` (run 44000060109) được kích hoạt đúng theo trigger mới, nhưng job không được khởi chạy vì tài khoản bị khóa thanh toán. Sau khi mở khóa: `gh run rerun 44000060286` để tạo PR, `gh run rerun 44000060109` để chạy CI.
- Phát hiện khi kiểm tra: PR #1 đã được merge vào `main` lúc 16/11/2026 03:39 UTC (commit `a0fc1e6`); commit `ccf388a` (CLAUDE.md) push sau đó chưa vào `main`. Ref cũ `origin/revert/pr-7` đã được dọn.

### 17/11/2026 — Kế hoạch cơ chế nạp dữ liệu (chưa đổi code)
- Thêm vào mục 8 bảng "Cơ chế nạp và lịch sử dữ liệu": không dùng CDC (nguồn là file theo tháng); 4a — Fact chuyển sang `delete+insert` theo `source_file_name` để sửa lỗi trùng khi nạp lại một tháng (rủi ro số 5); 5a — SCD Type 2 cho `dim_location` bằng `dbt snapshot` (tùy chọn).
- Cập nhật phạm vi bước 4, 5 trong bảng lộ trình và rủi ro số 5.

### 16/11/2026 — DuckDB bước 2: Source → Ingestion
- **Thiết kế:** ingestion ghi vào schema `raw` của DuckDB (`raw.yellow_tripdata`, `raw.taxi_zone_lookup`) thay cho `stage.stg_*` của PostgreSQL. Tên `stage` dành cho model staging của dbt ở bước 3, tránh trùng một schema cho hai tầng.
- `sql/ddl/01_init_schemas.sql`: tạo schema `raw`, `control`. `sql/ddl/02_create_stage.sql` → `02_create_raw.sql`: DDL DuckDB cho 2 bảng `raw` và `control.etl_control` (khóa dùng `SEQUENCE`). Tất cả `IF NOT EXISTS`.
- Thêm `mage/utils/duckdb_helpers.py`: `connect()` (retry khi file bị khóa, áp `DUCKDB_MEMORY_LIMIT`/`THREADS`/`TEMP_DIR`), `init_schema()` (chạy `sql/ddl/*.sql`), `next_batch_id()` (luôn tăng), `write_log()`.
- Pipeline `ingest_trips_to_postgres` → `ingest_yellow_trips`; block `load_trips_to_stage` → `load_trips_to_raw`: bỏ psycopg2/CSV/COPY, nạp bằng `read_parquet` trong một transaction; giữ tải file + retry, biến `file_name/year/start_month/end_month/use_lset`, LSET (giờ lọc theo `pipeline_name`); thêm kiểm tra tên file theo mẫu `yellow_tripdata_YYYY-MM.parquet`.
- `ingest_zone_lookup`: loader vẫn đọc CSV bằng pandas (giữ `N/A`); exporter ghi DuckDB trong transaction và ghi log vào `control.etl_control`.
- `mage/io_config.yaml`: thay cấu hình PostgreSQL bằng `DUCKDB_DATABASE`.
- `tasks.ps1`: thêm `ingest-zones`, `ingest [file | ALL | JSON]` (chạy `mage run`, escape JSON cho PowerShell 5.1); sửa lỗi ký tự tab trong thông báo lỗi của lệnh `sql`.
- Tài liệu: thêm `docs/guides/ingestion.md`; gắn ghi chú "tài liệu cũ" vào `docs/guides/staging.md`; cập nhật README, CLAUDE.md; sửa đường dẫn file đổi tên trong `tests/run_quality_tests.py`.
- **Kiểm tra (đạt), chạy bằng `mage run` trong container:**
  - `ingest_zone_lookup`: 265/265 dòng, 1 giá trị `N/A` giữ nguyên.
  - `ingest_yellow_trips` 2024-01: tải 47,6 MB + nạp 2.964.624/2.964.624 dòng, ~24 s.
  - Nạp lại 2024-01: vẫn 2.964.624 dòng, 1 batch (không trùng).
  - 2025-01 (có `cbd_congestion_fee`): 3.475.226 dòng, `cbd_congestion_fee` không NULL ở mọi dòng; 2024 toàn NULL.
  - `ALL` + `end_month=2024-02`: bỏ qua 2024-01 đã SUCCESS, tải và nạp 2024-02 (3.007.526 dòng); chạy lại thì bỏ qua cả hai, LSET = 2024-02.
  - Đối chiếu với Parquet gốc: số dòng và `sum(total_amount)` khớp từng file; `source_row_number` chạy 1..N.
  - Tên file `../../etc/passwd` bị từ chối (`ValueError`).
  - File bị khóa: `connect()` thử lại sau 2 s, 4 s, kết nối được sau khi tiến trình kia nhả khóa (6,6 s).
  - `.\tasks.ps1 ingest-zones`, `ingest <file>`, `ingest '<json>'` chạy đúng từ PowerShell.

### 16/11/2026 — Thêm CLAUDE.md
- Thêm `CLAUDE.md` ở gốc repo: tóm tắt dự án, quy tắc bắt buộc (cập nhật PROJECT_STATUS, repo độc lập, làm từng bước), ràng buộc phụ thuộc (dbt trong venv `/opt/dbt`, duckdb 1.5.x vì Python 3.10), lệnh thường dùng, lưu ý CI. Mục đích: phiên Claude Code ở máy khác hoặc trên web có đủ ngữ cảnh mà không cần lịch sử chat.

### 16/11/2026 — CI trên PR #1 bị failed (không do code)
- PR #1 (`refactor/project-structure` → `main`, repo mới): job `checks` không được khởi chạy, GitHub báo *"The job was not started because your account is locked due to a billing issue."* Cần xử lý thanh toán ở <https://github.com/settings/billing>, rồi chạy lại.
- Đã chạy đủ 3 bước của CI ở local trên commit `32b467e`: `compileall` OK, `docker compose config --quiet` OK, `dbt parse` trong image (dbt 1.12.7) OK, chỉ có cảnh báo 3 config path chưa có model.

### 16/11/2026 — Tách khỏi repo nhóm
- PR #8 (revert) đã được merge; `main` của repo nhóm đã giống hệt `36e24d3` (đã kiểm tra bằng `git diff`).
- Fork cũ đổi tên thành `thinhdao-77/NYC_TAXI_DataPipeline-fork` (chưa xóa, còn nhánh `revert/pr-7` của PR #8).
- Tạo repo độc lập `thinhdao-77/NYC_TAXI_DataPipeline` (public, `fork: false`), đẩy `main` (`36e24d3`) và `refactor/project-structure` (`32b467e`). Không còn tạo được PR vào repo nhóm.
- Local: `origin` trỏ repo mới; xóa remote `upstream` và nhánh local `revert/pr-7`; `gh repo set-default` trỏ repo mới.
- Còn lại: mục "Quy trình làm việc với Git" và lệnh clone trong README vẫn mô tả quy trình/URL của repo nhóm, sẽ viết lại khi cập nhật README theo DuckDB.

### 16/11/2026 — Sự cố: PR merge nhầm vào repo gốc
- PR #7 (`refactor/project-structure`) được tạo và merge nhầm vào `main` của repo gốc `nguyenanhtuan2702/NYC_TAXI` (merge commit `39a2f34`), kéo theo cả các commit `feat/fact-thinh`.
- Đã mở PR revert: <https://github.com/nguyenanhtuan2702/NYC_TAXI/pull/8> (nhánh `revert/pr-7` trên fork, commit `d475177`); sau khi merge, `main` gốc giống hệt `36e24d3`. Cần nhóm duyệt và merge.
- Hệ quả cần nhớ: khi nhóm merge `develop` → `main`, code Fact sẽ không tự quay lại; phải revert commit revert trước (đã ghi trong mô tả PR #8).
- Phòng ngừa: `gh repo set-default` trỏ về fork; khi tạo PR trên web, kiểm tra ô *base repository* là `thinhdao-77/NYC_TAXI_DataPipeline` (GitHub mặc định chọn repo gốc).

### 16/11/2026 — DuckDB bước 1: Docker Compose
- `docker-compose.yml`: bỏ service `postgres` và volume `pgdata`; đặt tên project `nyc-taxi`; Mage nâng giới hạn RAM lên 6 GB (DuckDB chạy trong tiến trình Mage/dbt); thêm biến `DUCKDB_PATH`, `DUCKDB_MEMORY_LIMIT`, `DUCKDB_THREADS`, `DUCKDB_TEMP_DIR`, `RAW_DATA_DIR`, đều có giá trị mặc định nên `.env` không còn bắt buộc.
- `.env.example`: thay biến PostgreSQL bằng biến DuckDB.
- Thêm `data/warehouse/` (chứa file `.duckdb`, không commit); `.gitignore` bỏ `pgdata/`, thêm `*.duckdb.wal`, `data/warehouse/*`.
- **Image và phụ thuộc** (sửa sau 2 lần build/chạy lỗi):
  - Lỗi 1: `duckdb~=2.0.0` không cài được vì image Mage dùng Python 3.10, duckdb 2.x cần >= 3.11. Chuyển sang `duckdb~=1.5.6`.
  - Lỗi 2: container khởi động lỗi `TypeError: Secondary flag is not valid for non-boolean flag` vì `dbt-core` 1.12 kéo `click>=8.3` (và `protobuf>=6`), phá `typer 0.9` / `click 8.1.8` mà CLI Mage 0.9.79 dùng.
  - Cách sửa: `Dockerfile` ghim image theo digest (`mageai/mageai:latest@sha256:4409…`, mage-ai 0.9.79); dbt cài trong virtualenv riêng `/opt/dbt` (symlink `/usr/local/bin/dbt`), không đụng môi trường Mage. Tách `requirements.txt` (môi trường Mage: chỉ `duckdb~=1.5.6`) và `requirements-dbt.txt` (`dbt-core~=1.12.0`, `dbt-duckdb~=1.11.1`, `dbt-postgres` tạm giữ đến bước 4, `duckdb~=1.5.6`). Mage và dbt dùng cùng duckdb 1.5.6 để đọc/ghi chung một file. CI cài cả hai file.
- `tasks.ps1`: bỏ `psql`, thêm `shell` (bash trong Mage) và `sql "<câu SQL>"` (truy vấn DuckDB chỉ đọc); `profile` chạy trên DuckDB; pipe dùng UTF-8.
- **Kiểm tra trên Docker (đạt):** image build OK; trong môi trường Mage `click 8.1.8`, `typer 0.9.0`, `protobuf 4.25.8`, `duckdb 1.5.6`, `pip check` không xung đột, `mage` CLI chạy; `dbt --version` = 1.12.7 với plugin duckdb 1.11.1 và postgres 1.11.0; container `Up`, Mage UI HTTP 200 sau ~12 s; DuckDB nhận `memory_limit` 3.7 GiB, 4 threads; `.\tasks.ps1 sql` trả kết quả đúng kể cả tiếng Việt.
- **Đo I/O** (20 triệu dòng, ghi + checkpoint / đọc tổng hợp): bind mount ổ D: 14,5 s / 1,6 s; filesystem trong container 15,4 s / 2,2 s. Không chậm hơn, nên **giữ file DuckDB trên bind mount** (`data/warehouse/`) để Power BI mở trực tiếp.

### 16/11/2026 — Tái cấu trúc thư mục (nhánh `refactor/project-structure`)
- Merge `upstream/feat/fact-thinh`: dbt project, model Fact, SQL Fact, bản sửa Dimension idempotent.
- **Mục 1:** chuyển 8 Dimension sang dbt (`dbt/models/dds/dimensions/` + `schema.yml` + test Unknown member); Fact dùng `ref()` thay vì `source('dds', ...)`; `sources.yml` chỉ còn `stage`; `profiles.yml` bỏ mật khẩu mặc định, đọc `POSTGRES_PORT`; test `relationships` chuyển sang cú pháp `arguments:`. `warehouse/*.sql` → `sql/warehouse/`; bỏ luật `.gitignore` riêng cho `warehouse/`.
- **Mục 2:** pipeline `letter_01_ingest_source_to_postgres` → `ingest_zone_lookup`; xóa 2 thư mục pipeline rỗng.
- **Mục 3:** `staging/init_sql` → `sql/ddl` (cập nhật mount trong `docker-compose.yml`), `staging/pg_checks` → `sql/profiling`; README rải rác → `docs/guides/` (`staging.md`, `dimension.md`, `dimension_handover.md`, `fact.md`, `testing.md`); cập nhật đường dẫn trong README, guides, test plan và `tests/run_quality_tests.py`.
- **Mục 4:** `.gitignore` bỏ qua `docs/02_test_plans_and_logs/runs/*`, chỉ giữ `run_20261026T034420Z`; 12 file log khác bỏ khỏi git (file local vẫn còn).
- **Mục 5:** thêm `requirements.txt` (dbt-core 1.12, dbt-postgres 1.11), `Dockerfile` cài từ file này, `tasks.ps1`, CI GitHub Actions.
- Kiểm tra: `dbt parse` sạch trên dbt-core 1.12.7; `python -m compileall` OK; `tasks.ps1` parse OK; runner QA `PF-REPO-01` PASS với đường dẫn mới. Chưa chạy dbt trên DB.

### 16/11/2026 — Khởi tạo
- Fork repo, cấu hình remote `origin` (fork) và `upstream` (repo gốc, chặn push). Viết bản tóm tắt đầu tiên.

## 8. Chuyển sang DuckDB

Quyết định ngày 16/11/2026: thay PostgreSQL bằng DuckDB làm kho dữ liệu, làm lần lượt theo thứ tự pipeline. Fork sẽ khác repo nhóm (vẫn dùng PostgreSQL) ở các phần ingestion, staging, test.

| Bước | Phạm vi | Trạng thái |
|---|---|---|
| 1. Hạ tầng | `docker-compose.yml`, `Dockerfile`, `.env.example`, `requirements*.txt`, `tasks.ps1` | **Xong, đã chạy thử trên Docker** |
| 2. Source → Ingestion | Mage: tải Parquet + Zone Lookup vào `raw.*`, log nạp (`control.etl_control`) và LSET trên DuckDB; `sql/ddl`; `mage/io_config.yaml` | **Xong, đã chạy thử 3 tháng** |
| 3. Staging | `profiles.yml` sang dbt-duckdb (bỏ `dbt-postgres`); `sources.yml` trỏ `raw`; model staging (schema `stage`): đặt tên, cột dẫn xuất, cờ dữ liệu lỗi; DDS đọc staging bằng `ref()`; `sql/profiling` chạy trên DuckDB | **Xong, đã chạy trên 24 tháng** |
| 4. ETL/ELT | Sửa hàm riêng PostgreSQL trong model Dimension/Fact (`to_char`, `generate_series`, ...) để chạy trên DuckDB; cân nhắc dùng `is_valid_for_fact` của staging thay cho WHERE trong Fact; Fact chuyển sang `incremental_strategy='delete+insert'` theo `source_file_name` (4a) | Chưa làm |
| 5. Data warehouse | DDS (Dimension, Fact) + OLAP mart; test dbt; runner QA chuyển sang thư viện `duckdb`; SCD Type 2 cho `dim_location` bằng `dbt snapshot` (5a, tùy chọn) | Chưa làm |
| 6. Power BI | Kết nối DuckDB (ODBC, chế độ Import) hoặc đọc mart xuất ra Parquet | Chưa làm |

### Cơ chế nạp và lịch sử dữ liệu (quyết định 17/11/2026)

Nguồn TLC là file Parquet theo tháng, không có log giao dịch, nên **không dùng CDC**. Cơ chế cho từng tầng:

| Tầng | Cơ chế | Trạng thái |
|---|---|---|
| `raw.yellow_tripdata` | Watermark theo tháng (LSET) + delete-insert theo `source_file_name` | Đã làm (bước 2) |
| `raw.taxi_zone_lookup` | Full refresh | Đã làm (bước 2) |
| Dimension danh mục (`vendor`, `payment_type`, `rate_code`, `date`, `time`, nhóm tĩnh) | Full refresh = SCD Type 1 | Giữ nguyên |
| `fact_taxi_trips` | **4a.** Đổi từ append theo `batch_id` sang `delete+insert`: chọn các `source_file_name` có `batch_id` mới hơn lần nạp Fact trước, xóa các chuyến đi của những file đó trong Fact rồi chèn lại. Mục tiêu: nạp lại một tháng ở `raw` không làm trùng Fact | Kế hoạch bước 4 |
| `dim_location` | **5a (tùy chọn).** `dbt snapshot` (SCD Type 2, `strategy: check` trên `borough`, `zone`, `service_zone`) từ `raw.taxi_zone_lookup`; `dim_location` có `valid_from`, `valid_to`, `is_current`, SK riêng mỗi phiên bản; Fact tra khóa theo `pickup_datetime` nằm trong khoảng hiệu lực. Giá trị thực tế thấp (khu vực hiếm đổi), chủ yếu để minh họa SCD2 | Kế hoạch bước 5 |

Kiểm thử cần có khi làm: 4a — nạp lại một tháng ở `raw`, chạy lại Fact, số dòng Fact của tháng đó không đổi; 5a — sửa thử một khu vực trong bản sao CSV, chạy snapshot, có 2 phiên bản và Fact cũ vẫn trỏ phiên bản cũ.

**Tạm thời không chạy được cho tới bước tương ứng:** model Dimension/Fact trên DuckDB (bước 4), runner QA (`tests/run_quality_tests.py` gọi `psql` trong container `postgres`), và hướng dẫn PostgreSQL trong README và `docs/guides/`.

**Lưu ý vận hành DuckDB**
- Chỉ một tiến trình được ghi vào file. Không chạy đồng thời pipeline Mage và `dbt build`; đóng Power BI/DBeaver trước khi ghi.
- File `.duckdb` nằm trên bind mount (ổ D: của Windows) để Power BI mở trực tiếp được. Đã đo: không chậm hơn filesystem trong container (xem nhật ký bước 1).
- dbt chạy từ venv `/opt/dbt` trong container (`dbt` hoặc `.\tasks.ps1 dbt-*`). Không `pip install` gói dbt vào môi trường Mage: sẽ làm hỏng CLI Mage.
