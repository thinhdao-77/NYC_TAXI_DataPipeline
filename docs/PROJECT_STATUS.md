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
| Nạp Yellow Taxi Parquet | **Hoàn thành (DuckDB), đã nạp đủ 24 tháng** | Pipeline `ingest_yellow_trips` → `raw.yellow_tripdata` (89.892.322 dòng): tự tải file, retry, nạp mỗi file trong một transaction, LSET, log theo file |
| Staging (dbt, DuckDB) | **Hoàn thành, đã chạy trên 24 tháng** | `stage.stg_yellow_taxi_trips`, `stage.stg_taxi_zone_lookup` (view) đọc `raw.*`; 15 cờ chất lượng + `is_valid_for_fact`; 13 test PASS (~12 s). Hướng dẫn: [guides/staging.md](guides/staging.md) |
| Profiling dữ liệu nguồn | **Hoàn thành (DuckDB), đã chạy** | `sql/profiling/02..11` trên `raw.*`, mỗi file 3–14 s trên ~90 triệu dòng; chạy bằng `.\tasks.ps1 profile <file>` |
| dbt project | **Chạy trên DuckDB** | `profiles.yml` dùng adapter `duckdb` (cùng file với Mage), `sources.yml` trỏ `raw.*`; dbt-core 1.12.7, dbt-duckdb 1.11.1 |
| Dimension (8 bảng) | **Hoàn thành, chạy trên DuckDB** | `dbt/models/dds/dimensions/`; SK ổn định, dòng Unknown `-1`; `dim_location` là **SCD Type 2** từ snapshot `snapshots.snap_taxi_zone_lookup` (bước 5a) |
| Fact `facttaxitrip` | **Hoàn thành, chạy trên DuckDB (24 tháng)** | `dbt/models/dds/facts/fact_taxi_trips.sql`: lọc `is_valid_for_fact`, incremental `delete+insert` theo `sourcefilename`; 85.745.246 dòng, build đầy đủ 94 s, 18 test PASS. Hướng dẫn: [guides/fact.md](guides/fact.md#0-chạy-trên-duckdb-dbt) |
| SQL thủ công DDS | Lưu để tham khảo | `sql/warehouse/01..05` (Dimension idempotent + Fact + verify) |
| Runner QA (DuckDB) | **Hoàn thành, đã chạy** | `tests/run_quality_tests.py` viết lại cho DuckDB (read_only), kiểm tra xuyên tầng raw → stage → dds → olap; `.\tasks.ps1 qa full`: 53 PASS, 0 FAIL, ~32 s. Hướng dẫn: [guides/testing.md](guides/testing.md) |
| Test plan + log | Một phần | `docs/test_plans_and_logs/`: test plan viết cho giai đoạn PostgreSQL; bản chạy mẫu `run_20261118T115030Z` (DuckDB) và `run_20261026T034420Z` (PostgreSQL cũ) |
| CI / tự động hóa GitHub | **Hoàn thành, đã chạy thật trên GitHub** | `ci.yml` chạy khi push mọi nhánh; `auto-pr.yml` tự mở PR vào `main`; repo tự xóa nhánh sau khi merge |
| Lệnh tiện ích | Hoàn thành | `tasks.ps1` (up/down/shell/sql/ingest-zones/ingest/profile/dbt-*/qa/export-bi/build-map/prune-branches) |
| Data modeling docs | Một phần | `docs/data_modeling/modeling.pdf` (giai đoạn 1: business event, 8 Dimension, Fact, measures, truy vấn kiểm chứng Star Schema); sơ đồ Star Schema chỉ có qua link Google Drive trong PDF |
| OLAP mart | **Hoàn thành, chạy trên DuckDB** | 5 mart trong schema `olap` (`mart_trips_daily`, `mart_hourly_activity`, `mart_routes_monthly`, `mart_trip_profile`, `mart_monthly_kpi`) phục vụ A1–A8, B1–B5 của modeling.pdf; tổng khớp Fact. Hướng dẫn: [guides/olap.md](guides/olap.md) |
| Pipeline ELT end-to-end | **Chưa có** | Cần pipeline Mage: ingest → `dbt build` |
| Power BI | **Đã dựng 7 trang, số liệu khớp; còn sửa hiển thị** | `.\tasks.ps1 export-bi` xuất 5 mart + 7 Dimension ra `data/bi/*.parquet`; `powerbi/queries/*.pq` (Power Query), `powerbi/dax/measures.dax` (119 measure), `powerbi/map_shapes/` (TopoJSON 263 zone + tâm khu vực); hướng dẫn dựng model và 7 trang: [guides/powerbi.md](guides/powerbi.md). Template `powerbi/dashboard/NYC_Taxi_Dashboard.pbit` (không chứa dữ liệu); `.pbix` có dữ liệu chỉ giữ ở máy |

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
| `dim_date` | `dds.dimdate` | `YYYYMMDD` | sinh 2024-01-01..2026-01-31 |
| `dim_time` | `dds.dimtime` | `hour*100+minute` | sinh 24×60 |
| `dim_location` | `dds.dimlocation` | `LocationID*100 + VersionNo` | snapshot zone lookup (SCD2: `validfrom`, `validto`, `iscurrent`) |
| `dim_vendor` | `dds.dimvendor` | = `VendorID` | trips; mã ngoài 1/2 → Unknown |
| `dim_payment_type` | `dds.dimpaymenttype` | = `PaymentTypeID` | trips; mã 0 → Unknown |
| `dim_rate_code` | `dds.dimratecode` | = `RateCodeID` | trips; NULL → 99 Unknown |
| `dim_passenger_group` | `dds.dimpassengergroup` | 0..3 | tĩnh (NONE = 0/NULL hành khách, LARGE tới 9999) |
| `dim_distance_group` | `dds.dimdistancegroup` | 1..3 | tĩnh, `NUMERIC(10,4)` |

Logic nghiệp vụ giữ nguyên bản SQL đã sửa trong `feat/fact-thinh`. Khác biệt: SK không còn là `SERIAL` mà sinh từ khóa tự nhiên, để Fact incremental không bị lệch khóa khi Dimension build lại. Tên bảng/cột vật lý giữ nguyên, nên runner QA vẫn dùng được.

### 3.3 Fact (dbt)
Grain: một chuyến đi hợp lệ (`stg.is_valid_for_fact`: `dropoff > pickup`, pickup trong 2024–2025, `fare/total/distance >= 0`). Tra khóa bằng `LEFT JOIN` + `COALESCE(sk, -1)`; Location tra theo khoảng hiệu lực SCD2. Incremental `delete+insert` theo `sourcefilename`, lấy batch mới hơn `max(batchid)`.

### 3.4 QA
Lần chạy 18/11/2026 trên DuckDB (`run_20261118T115030Z`, `qa full`): 53 PASS, 0 FAIL, 1 NOT APPLICABLE. Lần chạy cũ 26/10 trên PostgreSQL (`run_20261026T034420Z`): 19 PASS, 8 FAIL, 14 BLOCKED (8 FAIL do bảng Dimension chưa tồn tại lúc test).

## 4. Vấn đề và rủi ro còn mở

1. ~~Chưa chạy dbt trên database thật~~: toàn bộ pipeline dbt chạy trên DuckDB 24 tháng (bước 3–5), runner QA đạt.
2. Hai cách build DDS cùng tồn tại (dbt và `sql/warehouse/`). Không được trộn: dbt build lại Dimension sẽ xóa khóa ngoại do `03_create_fact.sql` tạo. Nên chọn dbt làm chuẩn và cân nhắc bỏ bản SQL khi dbt đã ổn.
3. Fact dbt không có `TripSK` (bản SQL có `BIGSERIAL`). Cần thống nhất nếu Power BI cần khóa chuyến đi.
4. ~~Dimension đọc `SELECT DISTINCT` từ bảng trips~~: đo trên DuckDB 0,6–1,6 s mỗi bảng, không cần tối ưu.
12. SCD2 của `dim_location`: `validfrom` của phiên bản mới là **thời điểm chạy snapshot**, không phải ngày TLC đổi khu vực (nguồn không có ngày hiệu lực); phiên bản đầu tiên coi như áp dụng từ 1900-01-01. Vì dữ liệu chuyến đi là 2024–2025, mọi chuyến hiện tại đều trỏ phiên bản 1; phiên bản mới chỉ áp dụng cho chuyến có giờ đón sau lần snapshot phát hiện thay đổi. Chạy `dbt build --select fact_taxi_trips --full-refresh` không làm đổi phiên bản của chuyến cũ (tra theo thời điểm đón).
5. ~~Fact bị trùng khi nạp lại một file cũ~~: đã sửa ở bước 4 (`delete+insert` theo `sourcefilename`, kiểm chứng bằng cách nạp lại file 2024-01). Còn lại: file bị xóa hẳn khỏi `raw` thì dòng Fact cũ không tự mất (test `assert_fact_matches_staging` báo; chạy `--full-refresh`).
11. ~~Khóa `-1` trong Fact (nhóm hành khách 14,18 triệu dòng, ngày trả 759 dòng)~~: đã sửa ở bước 4 (nhóm `NONE`, `DimDate` tới 2026-01-31). Lưu ý: `DimDate` có tháng 01/2026 nhưng không có chuyến đón nào trong tháng đó.
6. Mage lưu lịch sử chạy theo uuid pipeline. Sau khi đổi tên (`letter_01_...` → `ingest_zone_lookup`, `ingest_trips_to_postgres` → `ingest_yellow_trips`), lịch sử cũ trên Mage UI không hiện dưới tên mới. LSET không bị ảnh hưởng vì `control.etl_control` trên DuckDB bắt đầu mới.
8. ~~`sources.yml` trỏ bảng PostgreSQL cũ~~: đã xử lý ở bước 3 (`sources.yml` trỏ `raw.*`, DDS đọc staging qua `ref()`).
10. `is_total_mismatch` dựa trên quy luật quan sát từ dữ liệu (`extra` đã gồm phụ phí ở nhiều dòng), không phải định nghĩa chính thức của TLC; còn 384.360 dòng lệch thật (0,43%) chưa phân tích nguyên nhân.
9. DuckDB không tự thu hồi chỗ của dòng đã xóa khi nạp lại một file; nạp lại nhiều lần làm file phình. Thu gọn bằng `COPY FROM DATABASE` sang file mới khi cần.
7. `data/reference/taxi_zones.zip` (nhị phân) vẫn nằm trong git; nay là nguồn của `powerbi/map_shapes/` (`tasks.ps1 build-map`) nên giữ lại.
13. Báo cáo Power BI đã dựng đủ 7 trang (template `.pbit`); số liệu đã đối chiếu và khớp (21/11/2026); phần lớn lỗi hiển thị đã sửa. Còn lại: waterfall trang 7 vẫn tắt trục X (không có tên khoản dưới cột). Heatmap trang 4 (đủ 7 ngày) chưa kiểm lại bằng ảnh chụp. Shape map là tính năng preview của Power BI.

## 5. Cấu trúc thư mục hiện tại

```text
.
├── .github/workflows/ci.yml
├── data/{raw,reference,warehouse}, download_raw.ps1
├── dbt/                      # transform chính: sources → staging → snapshots → dds (dims, facts) → olap_marts; macros/olap_trip_measures.sql
├── mage/                     # ingestion: pipelines ingest_zone_lookup, ingest_yellow_trips; utils/duckdb_helpers.py
├── sql/
│   ├── ddl/                  # DDL DuckDB (raw, control); block ingestion tự chạy
│   ├── profiling/            # truy vấn kiểm tra dữ liệu nguồn
│   └── warehouse/            # SQL thủ công Dimension/Fact (tham khảo)
├── tests/                    # runner QA chỉ đọc
├── powerbi/                  # scripts/ (export_bi, build_map_shapes), queries/ (M), dax/measures.dax, map_shapes/
├── docs/
│   ├── PROJECT_STATUS.md     # file này
│   ├── guides/               # ingestion, staging, dimension, fact, olap, testing, powerbi
│   ├── data_modeling/
│   └── test_plans_and_logs/
├── docker-compose.yml, Dockerfile, requirements.txt, requirements-dbt.txt, tasks.ps1, .env.example, README.md, CLAUDE.md
```

## 6. Việc nên làm tiếp

1. ~~Đối chiếu số liệu dashboard~~ (khớp, 21/11/2026); bật trục X của waterfall trang 7 (lỗi đã biết số 13); chụp ảnh dashboard (`powerbi/screenshots/`) và cập nhật README.
2. Quyết định giữ hay bỏ `sql/warehouse/`; thống nhất `TripSK` cho Fact.
3. Chuyển nội dung `modeling.pdf` thành markdown + ERD trong repo (sơ đồ hiện chỉ có qua link Google Drive) và bổ sung data dictionary.
4. ~~Xây OLAP mart~~: xong ở bước 5.
5. Pipeline Mage end-to-end: ingest → `dbt build`.
6. ~~Chuẩn bị dữ liệu Power BI, dựng dashboard~~: xong ở bước 6 (template `.pbit`); còn đối chiếu số liệu và ảnh chụp (việc 1).

## 7. Nhật ký thay đổi

### 18/11/2026 — DuckDB bước 6: Power BI (chuẩn bị dữ liệu, model, measure)
- Người dùng chọn: Power BI đọc **Parquet xuất từ DuckDB** (không cài ODBC, không giữ khóa file DuckDB) và **chỉ chuẩn bị file DAX/M + hướng dẫn** (tự dựng `.pbix`).
- `powerbi/scripts/export_bi.py` (`.\tasks.ps1 export-bi`): mở DuckDB read_only, `COPY` 5 mart + 7 Dimension (không xuất Fact) ra `data/bi/*.parquet` (zstd), ghi file tạm rồi đổi tên, kiểm tra số dòng ghi ra = nguồn, ghi `_manifest.json`. `data/bi/` và `powerbi/*.pbix` thêm vào `.gitignore`.
- `powerbi/scripts/build_map_shapes.py` (`.\tasks.ps1 build-map`): extension `spatial` của DuckDB đọc `data/reference/taxi_zones.zip`, đơn giản hóa 30 feet trong EPSG:2263, chuyển sang WGS84, ghi `powerbi/map_shapes/taxi_zones.topojson` (263 khu vực, 354 arc, 14.821 điểm, 331 KB; TopoJSON không lượng tử hóa, mỗi vòng biên một arc) và `taxi_zone_centroids.csv` (tâm khu vực). Hai file này được commit.
- `powerbi/queries/*.pq`: 14 truy vấn M (tham số `RepoFolder`, 8 Dimension gồm `DimMonth` dựng từ `DimDate`, 5 mart). `DimDate` bỏ dòng Unknown để đánh dấu Date table; thêm `monthkey` cho mart tháng; `DimLocation` gắn tọa độ tâm; `RoutesMonthly` thêm cột `route`.
- `powerbi/dax/measures.dax`: 55 measure dạng `DEFINE MEASURE` (dán vào DAX query view, Update model): chuyến, doanh thu, trung bình tính từ tổng cộng dồn, thành phần doanh thu, MoM/YoY (time intelligence trên `DimDate`), B2 tháng 6 so với tháng 5, đón/trả theo vai trò, hạng tuyến, lượt đón/trả theo khu vực (`USERELATIONSHIP` cho quan hệ dropoff), hồ sơ chuyến, KPI tháng; kèm `EVALUATE` kiểm tra tổng.
- `docs/guides/powerbi.md` (mới): xuất dữ liệu, tạo truy vấn, bảng quan hệ (DimMonth → DimDate → mart ngày; DimMonth → mart tháng; quan hệ dropoff inactive), Mark as date table, Sort by column, ẩn cột, measure, 7 trang báo cáo theo câu A1–B5, Shape map/bản đồ bong bóng, bảng giá trị đối chiếu, lưu `.pbit`.
- `tasks.ps1`: thêm `export-bi`, `build-map`. CI: `compileall` thêm thư mục `powerbi`.
- **Kiểm tra (đạt):**
  - `export-bi`: 12 file, ~110 MB, ~5 s; số dòng khớp nguồn (`mart_trips_daily` 1.411.379, `mart_routes_monthly` 823.930, `dimdate` 763...). Chạy được qua `.\tasks.ps1 export-bi`.
  - `build-map`: TopoJSON hợp lệ về cấu trúc (263 LocationID 1..263 không trùng, mọi chỉ số arc hợp lệ, mọi vòng khép kín, kinh độ −74,256..−73,700, vĩ độ 40,496..40,916); tâm khu vực 1 (Newark Airport) = 40,6918; −74,1740.
  - Kiểm tra tự động trên file Parquet đã xuất: 116 tham chiếu `Bảng[cột]` trong DAX, mọi cột dùng trong M và 19 cột khóa quan hệ đều tồn tại; không có tham chiếu measure chưa định nghĩa.
  - Giá trị đối chiếu (mục 5 của hướng dẫn) tính bằng SQL trên mart: 85.745.246 chuyến; 2.475.529.050,41 USD; 28,87 USD/chuyến; 10,94 mph; tỷ lệ boa 21,88%; tháng 6/2025 so với 5/2025 −4,40%.
  - `tasks.ps1` parse OK; `compileall` OK.
  - **Chưa kiểm chứng trong Power BI Desktop** (rủi ro số 13).

### 19/11/2026 — Sửa measure DAX sau khi chạy thử trong Power BI Desktop
- Người dùng dựng model theo `docs/guides/powerbi.md` mục 2.1–2.4 và chạy truy vấn kiểm tra `SUMMARIZECOLUMNS(DimMonth[year], ...)`. Đúng: `Trips` 2024 = 40.422.347, 2025 = 45.322.899; `Revenue` 1.162.091.225,73 / 1.313.437.824,68; `Revenue YoY %` 2025 = 13%; `Route Trips`, `Profile Trips` khớp `Trips` theo năm (quan hệ 2.2 đúng).
- **Lỗi 1:** `Revenue May` / `Revenue June` ra 230.228.624,18 / 218.020.293,79 ở mọi năm (= tổng tháng 5, tháng 6 của 2024 + 2025). Nguyên nhân: `REMOVEFILTERS ( DimDate )` xóa bộ lọc trên bảng mở rộng của `DimDate`, gồm cả `DimMonth` (DimDate ở phía nhiều của quan hệ DimMonth → DimDate), nên mất bộ lọc năm. Sửa: chỉ xóa bộ lọc các cột mức tháng/ngày của `DimMonth` và `DimDate`, giữ cột năm; thêm `HASONEVALUE ( DimMonth[year] )` để chỉ tính khi đang xét một năm.
- **Lỗi 2:** `Revenue YoY %` năm 2026 = −100% (2026 không có chuyến đón, doanh thu BLANK so với 2025). Sửa: `Revenue MoM %`, `Revenue YoY %`, `Trips YoY %` trả BLANK khi kỳ hiện tại không có dữ liệu.
- Kỳ vọng sau khi sửa: 2024 `Revenue May` 106.909.224,54, `Revenue June` 100.121.367,53, −6,35%; 2025 123.319.399,64, 117.898.926,26, −4,40%; dòng 2026 không còn xuất hiện. Chờ người dùng chạy lại để xác nhận.
- `docs/guides/powerbi.md` trang 4: ma trận nhiệt dùng `DimDate[dayname]` thay `HourlyActivity[dayname]` (cột này bị ẩn theo mục 2.3).

### 19/11/2026 — Thiết kế dashboard Power BI: hệ thống thiết kế + trang 1
- Theo các nguyên tắc trực quan hóa người dùng đưa ra (thuộc tính tiền chú ý, màu có mục đích và thân thiện người mù màu, trục từ 0 cho cột/thanh, tránh pie/donut, thông tin quan trọng bên trái, không xoay chữ, phân cấp chữ, mọi quyết định là đánh đổi).
- Mới `docs/guides/powerbi_design.md`: bảng áp dụng 6 nguyên tắc; hệ màu (trung tính, chính `#1F5AA6`, nhấn `#E69F00`, tăng xanh dương ▲ / giảm cam `#C65A00` ▼, tuần tự xanh dương, phân kỳ cam–xám–xanh dương, danh mục Okabe–Ito); cỡ chữ Segoe UI; lưới 1280 × 720 với thanh bộ lọc trái 200 px; **đặc tả trang 1** (A1, A6, A8): 4 KPI card, 3 biểu đồ đường small multiples chung trục thời gian, bảng theo quận có data bar từ 0, tọa độ từng visual, tương tác, đánh đổi, số liệu đối chiếu.
- Mới `powerbi/theme/nyc_taxi_theme.json` (bảng màu, màu tăng/giảm, tuần tự, cỡ chữ, tắt tiêu đề trục).
- `powerbi/queries/DimDate.pq`: thêm cột `monthstart` (date) cho hierarchy `year > monthstart > fulldate` (trục thời gian liên tục, nhãn ngang).
- `powerbi/dax/measures.dax`: `Revenue YoY %`, `Trips YoY %` chỉ tính khi chọn đúng một năm (`HASONEVALUE ( DimMonth[year] )`; chọn cả hai năm thì `SAMEPERIODLASTYEAR` trộn kỳ); thêm `Avg Revenue per Trip PY`, `Avg Revenue per Trip YoY %`, `Trips Without Passenger %`, `Borough Text Color` (59 measure).
- **Phát hiện chất lượng dữ liệu (đo trên mart):** tỷ lệ chuyến không ghi nhận số hành khách 10,79% (2024) → 21,67% (2025); tổng hành khách 2025 giảm 4,80% trong khi số chuyến tăng 12,12%. Trang 1 không hiện YoY hành khách mà hiện tỷ lệ thiếu dữ liệu.
- Số liệu đối chiếu trang 1 tính bằng SQL trên `olap.mart_trips_daily`: theo năm (chuyến, hành khách, doanh thu, doanh thu/chuyến, YoY: 12,12% / 13,02% / 0,80%) và theo quận (8 dòng).
- Chưa kiểm chứng trong Power BI Desktop: chờ người dùng dựng trang 1.

### 19/11/2026 — Giao diện dashboard bằng tiếng Anh
- Người dùng yêu cầu toàn bộ chữ hiển thị trên dashboard bằng tiếng Anh (tài liệu vẫn tiếng Việt theo quy ước repo).
- **Dữ liệu:** `dim_passenger_group` đổi nhãn sang `No passenger count`, `1 passenger`, `2-4 passengers`, `5+ passengers`; `dim_distance_group` sang `Under 2 miles`, `2-5 miles`, `Over 5 miles` (mã `*code`, SK, khoảng giá trị không đổi nên Fact không cần build lại). Các Dimension khác vốn đã tiếng Anh (tên tháng/thứ từ `strftime`, vendor, payment, rate code, zone).
- **Tài liệu thiết kế** `docs/guides/powerbi_design.md`: tiêu đề, phụ đề, nhãn KPI, nhãn so sánh, tiêu đề biểu đồ, tiêu đề cột bảng, header slicer, chú thích, sơ đồ bố cục trang 1 chuyển sang tiếng Anh; thêm tên 7 trang (`Overview`, `Revenue by Zone & Vendor`, `Payment Methods`, `Pickup & Dropoff Timing`, `Trip Profile`, `Routes & Map`, `Trends & Comparisons`) và hướng dẫn đặt locale English (United States) để định dạng số kiểu Mỹ.
- **Kiểm tra (đạt):** `dbt build --select dim_passenger_group dim_distance_group mart_trip_profile`: 3 model + test, 16/16 PASS; `export-bi` chạy lại; quét mọi cột VARCHAR của 12 file Parquet xuất ra: không còn ký tự ngoài ASCII.

### 19/11/2026 — Thiết kế dashboard trang 2: Revenue by Zone & Vendor (A2, 5b)
- `docs/guides/powerbi_design.md` mục 6 (mới):
  - 4 KPI card: Revenue + YoY; khu vực đón dẫn đầu; tỷ trọng hãng dẫn đầu; giờ cao điểm doanh thu.
  - V1: thanh ngang chồng theo hãng, Top 10 khu vực, trục từ 0, màu xanh–cam.
  - V2: matrix quận > khu vực × hãng, data bar từ 0 và tỷ trọng hãng trong dòng.
  - V3: heatmap quận × giờ, tô theo tỷ trọng doanh thu trong ngày của từng quận, bảng màu tuần tự.
  - Kèm tọa độ, tương tác, đánh đổi, số liệu đối chiếu.
  - Bỏ slicer `timeslot` của phác thảo ban đầu.
- `powerbi/dax/measures.dax`: thêm 9 measure, tổng 68 (không trùng tên): `Vendor Revenue Share`, `Top Zone`, `Top Zone Revenue Share`, `Leading Vendor`, `Leading Vendor Share`, `Pickup Revenue (Borough)`, `Pickup Revenue Hour Share`, `Peak Revenue Hour`, `Peak Hour Revenue Share`.
  - `Pickup Revenue (Borough)` dùng `TREATAS` vì `HourlyActivity[borough]` không nối `DimLocation`, nên slicer quận trước đây không lọc được dữ liệu theo giờ.
- **Phát hiện:**
  - Hai sân bay JFK và LaGuardia chiếm 19,7% doanh thu.
  - VeriFone chiếm 78,6% doanh thu; Bronx là quận duy nhất CMT dẫn (55,2%).
  - Giờ cao điểm doanh thu: Manhattan 18h, Queens 16h, Brooklyn 8h, Bronx 7h.
- **Kiểm tra:**
  - Số liệu đối chiếu tính bằng SQL (duckdb 1.5.6 cài tạm ngoài repo) trên các file Parquet đã xuất `data/bi/`, vì Docker không chạy: tổng/Top 10 khu vực, hãng theo năm và quận, giờ cao điểm, tỷ trọng giờ theo quận.
  - DAX: chỉ kiểm tra tên cột tồn tại và tên measure không trùng.
  - **Chưa chạy trong Power BI Desktop.**
- **Sửa sau khi người dùng chạy thử (cùng ngày):**
  - Lỗi: heatmap V3 cho cả 4 dòng giống hệt nhau, đều là phân bố chung toàn thành phố (17h–18h 7,1%).
  - Nguyên nhân: `TREATAS` làm đối số filter của `CALCULATE` ghi đè bộ lọc dòng matrix trên cùng cột `HourlyActivity[borough]`.
  - Sửa: `Pickup Revenue (Borough)` bọc `KEEPFILTERS ( TREATAS ( ... ) )`.
  - Kỳ vọng sau khi sửa: Manhattan đậm nhất 18h 7,5%; Queens 16h 7,8%; Brooklyn 8h 6,4%; Bronx 7h 9,7%. Chờ người dùng xác nhận.

### 19/11/2026 — Thiết kế dashboard trang 3: Payment Methods (A3)
- **Thiết kế** `docs/guides/powerbi_design.md` mục 7 (mới):
  - 4 KPI card hiện tỷ trọng thẻ, tiền mặt, Unknown và tỷ lệ boa thẻ. Thay đổi so với năm trước tính bằng **điểm phần trăm**, màu trung tính.
  - V1: đường tỷ trọng theo tháng (Credit card, Cash, Unknown), trục từ 0. Thay cho cột chồng 100% của phác thảo ban đầu.
  - V2: thanh chồng 100% theo 4 quận, Unknown ở mép phải.
  - V3: bảng tổng hợp có data bar.
  - Kèm tương tác, đánh đổi, số liệu đối chiếu.
- **Truy vấn** `powerbi/queries/DimPaymentType.pq`: thêm cột `paymentorder` làm *Sort by column* cho `paymenttypename`. Không sắp theo `paymenttypeid` được vì Unknown ứng với các mã −1, 0, 5. `docs/guides/powerbi.md` mục 2.1 và 2.3 cập nhật theo.
- **Measure** `powerbi/dax/measures.dax`: thêm 8 measure, tổng 76, không trùng tên.
  - `Payment Trip Share`, `Card Trip Share`, `Cash Trip Share`, `Unknown Payment Share`;
  - 4 measure `* Change (pp)`, chỉ tính khi chọn một năm.
  - Gom khối measure trang 2 lại liền nhau.
- **Phát hiện:**
  - Mã thanh toán 0 (Unknown, TLC gọi là Flex Fare) tăng từ 9,8% số chuyến (2024) lên 21,1% (2025); tháng 12/2025 là 28,5%.
  - Toàn bộ 13.525.377 chuyến mã 0 đều thiếu số khách và mã giá. Đây chính là nguồn gây thiếu số hành khách ở trang 1.
  - Ở Brooklyn và Bronx, Unknown chiếm 63,5% và 55,3% số chuyến.
- **Kiểm tra:**
  - Số liệu đối chiếu tính bằng SQL trên các file Parquet trong `data/bi/` (duckdb tạm ngoài repo).
  - Chưa chạy trong Power BI Desktop.

### 19/11/2026 — Thiết kế dashboard trang 4: Pickup & Dropoff Timing (A4)
- **Thiết kế** `docs/guides/powerbi_design.md` mục 8 (mới), đơn vị chung là **trung bình mỗi ngày**:
  - 4 KPI card: giờ cao điểm đón, giờ cao điểm trả, ngày đông nhất, lượt đón mỗi ngày + YoY;
  - V1: 2 đường đón/trả theo giờ, trục từ 0;
  - V2: cột chênh lệch đón − trả theo giờ, small multiples cho Manhattan, Queens, Brooklyn, chung trục, màu phân kỳ;
  - V3: heatmap thứ × giờ.
  - Kèm tương tác, đánh đổi, số liệu đối chiếu.
- **Measure** `powerbi/dax/measures.dax`: thêm 14 measure, tổng 90, không trùng tên.
  - `Pickups (Borough)`, `Dropoffs (Borough)`: KEEPFILTERS + TREATAS, áp slicer quận cho cả hai vai trò.
  - `Days with Trips`: mẫu số, bỏ bộ lọc giờ và quận.
  - `Avg Daily Pickups/Dropoffs/Net Pickups`, `PY`, `YoY %`.
  - Giờ cao điểm đón/trả kèm tỷ trọng.
  - Ngày đông nhất kèm trung bình.
- **Phát hiện:**
  - Cao điểm 18h ở cả đón và trả. Thứ Năm đông nhất (127.686 lượt đón/ngày).
  - Đêm cuối tuần lúc 1h đông gấp 5–7 lần ngày thường (thứ Hai–thứ Năm). Chủ nhật đạt đỉnh lúc 0h.
  - Queens là nơi xuất phát gần như suốt 6h–24h (sân bay), ngày đông nhất là Chủ nhật.
  - Brooklyn là nơi đến từ 9h sáng đến 4h sáng hôm sau.
- **Kiểm tra:**
  - Số liệu đối chiếu tính bằng SQL trên `data/bi/` (mart giờ nối `dimdate`): 731 ngày (366 + 365); trung bình 117.298,6 / 110.443,6 / 124.172,3 lượt đón mỗi ngày.
  - Chưa chạy trong Power BI Desktop.

### 21/11/2026 — Dọn tài liệu theo hướng repo cá nhân
- **Yêu cầu của người dùng:** repo do một người phát triển, không giữ tên hay phân công của thành viên nhóm cũ.
- **Xóa:**
  - `docs/03_reports/`:
    - hai báo cáo QA theo từng thành viên (Source → Staging, Staging → Dimension), viết cho bản PostgreSQL và đã được thay bằng runner QA trên DuckDB (`guides/testing.md`, `test_plans_and_logs/runs/`);
    - các thư mục trống `milestone_01_11`, `final_01_12`.
  - `docs/guides/dimension_handover.md`: tài liệu bàn giao giữa các thành viên, bản PostgreSQL. Cách chạy Dimension hiện tại ở `guides/dimension.md`.
- **Sửa:**
  - `docs/guides/fact.md`:
    - bỏ người phụ trách, nguồn "do ai nạp/tạo", đối tượng bàn giao và tài liệu phân công;
    - mục 5 đổi thành "Tiêu chí nghiệm thu và kết quả kiểm thử".
  - `README.md`:
    - "Quy trình làm việc với Git" viết lại cho repo cá nhân (clone `thinhdao-77/NYC_TAXI_DataPipeline`, nhánh từ `main`, PR tự mở, dọn nhánh);
    - bỏ bảng "Phân công", giữ đoạn lộ trình;
    - bỏ `03_reports/` khỏi cây thư mục.
  - `docs/PROJECT_STATUS.md`:
    - bỏ dòng "Báo cáo thành phần";
    - sửa cây thư mục;
    - mục nhật ký 16/11 không còn URL/tên tài khoản của repo nhóm.
- **Giữ nguyên:**
  - `CLAUDE.md`: vẫn nêu tên repo nhóm trong quy tắc "không push/không tạo PR vào repo nhóm", vì quy tắc cần tên đó để có tác dụng.
  - `modeling.pdf`: đã đọc, không có tên thành viên.
- **Kiểm tra:** `git grep` tên các thành viên cũ, nhãn "Người 2/3/4" và tài khoản GitHub của repo nhóm: chỉ còn trong `CLAUDE.md`.
- **Người dùng đổi tên thư mục:**
  - `docs/01_data_modeling` → `docs/data_modeling`;
  - `docs/02_test_plans_and_logs` → `docs/test_plans_and_logs`.
- **Người dùng sửa** `docs/guides/powerbi.md`: bỏ dòng về `powerbi/screenshots/`.
- **Cập nhật đường dẫn mới** ở:
  - `.gitignore` (log QA tự sinh);
  - `tests/run_quality_tests.py` (thư mục ghi log `RESULTS`);
  - `CLAUDE.md`, `README.md`;
  - `docs/guides/fact.md`, `olap.md`, `testing.md` (gồm liên kết tới `test-plan.md`);
  - bảng trạng thái và cây thư mục ở file này.
  - Các mục nhật ký cũ giữ đường dẫn cũ làm lịch sử.
- **Kiểm tra:**
  - `git grep` đường dẫn cũ chỉ còn trong nhật ký cũ;
  - `py_compile tests/run_quality_tests.py` OK;
  - các file log mẫu vẫn được `.gitignore` cho phép commit.

### 21/11/2026 — Sửa hiển thị dashboard Power BI
- **Người dùng** sửa trong Power BI Desktop và xuất lại `powerbi/dashboard/NYC_Taxi_Dashboard.pbit`.
- **Kiểm tra** bằng cách đọc JSON của báo cáo trong file `.pbit`:
  - Đã sửa:
    - 6 biểu đồ đường ở trang 1, 3, 4, 7 chuyển sang `lineChartType = linear` (bỏ làm mượt);
    - trang 7: V1 và V2 sắp theo `DimMonth[monthshort]` tăng dần;
    - trang 4: small multiples bật tiêu đề panel (`subheader show = true`).
  - **Chưa sửa:** waterfall trang 7 vẫn để `categoryAxis show = false`.
  - Không kiểm được qua JSON, cần ảnh chụp: heatmap trang 4 có hiện đủ 7 ngày không, tên cột, nhãn KPI.
  - File không có phần `DataModel` (không chứa dữ liệu). Vẫn còn `UnappliedChanges`.

### 21/11/2026 — Đối chiếu số liệu dashboard Power BI
- **Người dùng** gửi ảnh chụp 7 trang (không lọc). Tôi so từng con số với SQL trên `data/bi/*.parquet`; **mọi số khớp**:
  - Trang 1: 85.7M chuyến, 94.9M hành khách, $2.48bn, $28.87/chuyến; Manhattan $1,821.5M (73.58%).
  - Trang 2: JFK 12.7%, VeriFone 78.6%, giờ 17 chiếm 7.1%; heatmap Bronx 7h 9.7%, Brooklyn 8h 6.4%, Manhattan 18h 7.5%, Queens 16h 7.8%.
  - Trang 3:
    - tỷ trọng: thẻ 71.2%, tiền mặt 11.4%, Unknown 15.8%;
    - tỷ lệ boa 21.9% (SQL 21.88%);
    - doanh thu/chuyến: thẻ $30.10, Unknown $26.08, tiền mặt $25.11;
    - tiền boa/chuyến: thẻ $4.35, tất cả $3.18.
  - Trang 4: giờ cao điểm 18h (7.1% / 7.4%), thứ Năm 128K/ngày, trung bình 117K/ngày.
  - Trang 5: 54.6%, 79.0%, 10.9 mph, 17.5 phút; ma trận và tỷ lệ boa 25.8/21.7/19.2% khớp.
  - Trang 6: 3.7% (56K tuyến), 14.1%, 7.4%, Upper East Side South 4.6%; hai bảng Top 10 khớp.
  - Trang 7: ▲13.0%, ▲12.1%, ▲0.8%, ▼4.4% (mỗi ngày ▼1.2%); waterfall +0.26 / −0.35 / −0.05 / −0.28 / −0.02 / +0.55 / −0.17 / +0.30 = +0.23.
- **Lỗi hiển thị phát hiện** (chưa sửa, do người dùng sửa trong Power BI Desktop): xem lỗi đã biết số 13.

### 21/11/2026 — Bỏ tài liệu thiết kế dashboard
- **Theo yêu cầu người dùng**, xóa `docs/guides/powerbi_design.md`. Bản dựng cuối nằm trong template `.pbit`.
  - File vẫn còn trong lịch sử git (commit `7589b52`).
  - Các mục nhật ký cũ nhắc tới file được giữ nguyên làm lịch sử.
- **Sửa liên kết** còn trỏ tới file:
  - `docs/guides/powerbi.md` mục 3: ghi chú đầu bảng và dòng trang 7;
  - `docs/PROJECT_STATUS.md`: bảng trạng thái, lỗi đã biết số 13, việc nên làm 1 (đối chiếu theo mục 5 của `powerbi.md`);
  - `README.md`: dòng trạng thái Power BI.
- **Kiểm tra:** `grep powerbi_design` trên repo chỉ còn kết quả trong các mục nhật ký cũ.

### 21/11/2026 — Template Power BI (.pbit)
- **Người dùng** dựng đủ 7 trang trong Power BI Desktop và xuất `powerbi/dashboard/NYC_Taxi_Dashboard.pbit` (328 KB).
  - `.pbix` cùng thư mục (125 MB, có dữ liệu) bị `.gitignore` (`powerbi/**/*.pbix`) bỏ qua.
- **Tài liệu:**
  - `docs/guides/powerbi.md` mục lưu file: đổi đường dẫn `.pbit`/`.pbix` sang `powerbi/dashboard/`.
  - Bảng trạng thái, lỗi đã biết số 13, việc nên làm 1 và 6 cập nhật theo.
  - `README.md`: sửa dòng trạng thái Power BI.
- **Kiểm tra** (đọc nội dung zip của `.pbit` bằng Python):
  - Không có phần `DataModel`, tức không chứa dữ liệu.
  - `DataModelSchema` có 14 bảng, 119 measure, 16 quan hệ. Báo cáo có 7 trang.
  - Tham số `RepoFolder` để trống, nên khi mở file sẽ hỏi thư mục repo.
  - Không tìm thấy đường dẫn `C:\Users\...` hay địa chỉ email.
  - File có `UnappliedChanges`: còn thay đổi Power Query chưa Apply lúc xuất.
  - Số liệu trên dashboard chưa được đối chiếu.

### 20/11/2026 — Thiết kế dashboard trang 7: Trends & Comparisons (B2, B3, B4)
- **Thiết kế** `docs/guides/powerbi_design.md` mục 11 (mới):
  - Trang cố định so sánh 2025 với 2024: slicer Year bỏ đồng bộ trên trang, năm gắn bằng bộ lọc từng visual.
  - 4 KPI card: callout là mức thay đổi (doanh thu, số chuyến, doanh thu mỗi chuyến so với 2024; tháng 6 so với tháng 5), reference là giá trị tuyệt đối.
  - V1: đường doanh thu theo tháng của hai năm.
  - V2: cột tăng trưởng cùng kỳ của doanh thu và số chuyến.
  - V3: waterfall thay đổi doanh thu mỗi chuyến theo từng khoản.
  - V4: thanh hai phía tháng 6 so với tháng 5 theo quận.
  - Kèm tương tác, đánh đổi, số liệu đối chiếu.
- **Truy vấn:**
  - `powerbi/queries/RevenueComponent.pq` (mới): bảng tĩnh 8 khoản doanh thu cho trục waterfall, không có quan hệ.
  - `powerbi/queries/DimMonth.pq`: thêm `monthshort` (Jan…Dec) để 12 nhãn trục nằm ngang.
  - `docs/guides/powerbi.md` mục 2.1, 2.3 và dòng trang 7 ở mục 3 cập nhật theo.
- **Measure** `powerbi/dax/measures.dax`: thêm 11 measure, tổng 119, không trùng tên.
  - `Revenue per Day May`, `Revenue per Day June`, `Revenue per Day June vs May %`.
  - `Congestion Surcharge`, `Airport Fee`, `CBD Congestion Fee`, `Other Surcharges`, `Unreconciled Amount`.
  - `Component Amount`, `Component per Trip`, `Component per Trip Change`.
- **Phát hiện chất lượng dữ liệu:** TotalAmount không bằng tổng các khoản. Năm 2024 lệch −11,7 triệu USD (−0,29 USD/chuyến), năm 2025 +0,5 triệu. Waterfall giữ cột "Unreconciled" để tổng khớp và trung thực.
- **Phát hiện khác:**
  - Doanh thu 2025 tăng 13,0%, số chuyến tăng 12,1%, doanh thu mỗi chuyến chỉ tăng 0,8% (+0,23 USD).
  - Trong mức +0,23 USD mỗi chuyến: phí CBD +0,55, cước +0,26, tiền boa −0,35, phụ phí ùn tắc −0,28.
  - Tháng 6/2025 thấp hơn tháng 5 là −4,4%, nhưng tính mỗi ngày chỉ −1,2% (tháng 6 ít hơn một ngày). Manhattan đóng góp −4,93 triệu USD.
- **Kiểm tra:**
  - Số liệu đối chiếu tính bằng SQL trên `data/bi/mart_trips_daily.parquet` và `mart_monthly_kpi.parquet`.
  - Tổng các cột waterfall khớp thay đổi doanh thu mỗi chuyến (0,231).
- **`.gitignore`:** đổi `powerbi/*.pbix` thành `powerbi/**/*.pbix`, để không commit `powerbi/dashboard/NYC_Taxi_Dashboard.pbix`. File này 125 MB, chứa dữ liệu và vượt giới hạn 100 MB của GitHub.
  - Chưa chạy trong Power BI Desktop.

### 20/11/2026 — Thiết kế dashboard trang 6: Routes & Map (A7, B5)
- **Thiết kế** `docs/guides/powerbi_design.md` mục 10 (mới):
  - 4 KPI card: tỷ trọng 10 tuyến đông nhất (kèm số tuyến), tỷ trọng chuyến khác quận, tỷ trọng chuyến đón ở sân bay (hai card này so cùng kỳ bằng pp), khu vực đón nhiều nhất.
  - V1: Shape map tô theo tỷ lệ cân bằng đón/trả `(trả − đón)/(trả + đón)`, thang chia đôi cam/xanh cố định từ −1 đến +1. Không tô theo số chuyến vì số chuyến lệch rất mạnh (trung vị 18 nghìn, lớn nhất 3,9 triệu).
  - V2, V3: hai bảng Top 10 tuyến, theo số chuyến và theo doanh thu, có data bar. Dùng bảng thay cho biểu đồ thanh vì tên tuyến dài.
  - Kèm tương tác, đánh đổi, số liệu đối chiếu.
- **Measure** `powerbi/dax/measures.dax`: thêm 11 measure, tổng 108, không trùng tên.
  - `Route Avg Duration (min)`, `Route Trip Share`, `Route Count`, `Top 10 Routes Share`.
  - `Cross-Borough Trip Share`, `Airport Pickup Share` và hai measure `* Change (pp)` (lùi `monthkey` 100 như trang 5).
  - `Top Pickup Zone`, `Top Pickup Zone Share`.
  - `Zone Net Flow Ratio`: trả BLANK khi khu vực dưới 1.000 lượt.
- **Hướng dẫn** `docs/guides/powerbi.md` mục 3, trang 6: đổi `Route Avg Distance (mi)` thành `Route Avg Duration (min)`.
- **Phát hiện chất lượng dữ liệu:** tuyến Upper East Side South → North có quãng đường trung bình khoảng 1,04 dặm mỗi tháng, riêng 03/2025 là 12,07 dặm vì một chuyến bất thường. Vì vậy `Route Avg Distance (mi)` không dùng được cho bảng tuyến; trang 6 dùng thời gian trung bình.
- **Phát hiện khác:**
  - 10 tuyến đông nhất chỉ chiếm 3,7% chuyến trên 56.336 tuyến. Các tuyến này là chặng ngắn trong Upper East Side.
  - Tuyến nhiều doanh thu nhất là chặng sân bay: JFK → Outside of NYC 22,0 triệu USD, 129,51 USD/chuyến.
  - 222 trên 248 khu vực có nhiều lượt trả hơn lượt đón. JFK (−0,63) và LaGuardia (−0,46) là điểm xuất phát rõ nhất.
  - Khu vực đón nhiều nhất năm 2024 là JFK, năm 2025 là Upper East Side South.
- **Kiểm tra:**
  - Số liệu đối chiếu tính bằng SQL trên `data/bi/mart_routes_monthly.parquet`; tổng 85.745.246 chuyến khớp Fact.
  - Chưa chạy trong Power BI Desktop.

### 20/11/2026 — Thiết kế dashboard trang 5: Trip Profile (A5, B1)
- **Thiết kế** `docs/guides/powerbi_design.md` mục 9 (mới):
  - 4 KPI card: tỷ trọng chuyến dưới 2 dặm, tỷ trọng chuyến 1 khách (trên số chuyến có ghi nhận), vận tốc, thời gian chuyến. So sánh dùng pp hoặc %, màu trung tính.
  - V1: highlight table nhóm khách × nhóm cự ly.
  - V2: cột tỷ lệ boa theo cự ly, trục từ 0.
  - V3: bảng theo mã giá có data bar ở nhiều cột, thay cho biểu đồ kết hợp hai trục Y của phác thảo ban đầu.
  - Kèm tương tác, đánh đổi, số liệu đối chiếu.
- **Truy vấn** `powerbi/queries/DimPassengerGroup.pq`: thêm `passengerorder` (No passenger count, Unknown xếp cuối).
  - `docs/guides/powerbi.md` mục 2.1 và 2.3: thêm cột này và hai Sort by column (`passengergroupname` theo `passengerorder`, `distancegroupname` theo `distancegroupsk`).
- **Measure** `powerbi/dax/measures.dax`: thêm 7 measure, tổng 97, không trùng tên.
  - `Profile Avg Duration (min)`, `Short Trip Share`, `Solo Ride Share`, 2 measure `* Change (pp)`, `Profile Avg Speed YoY %`, `Profile Avg Duration YoY %`.
  - `TripProfile` chỉ nối `DimMonth`, nên so sánh cùng kỳ lùi `monthkey` đi 100 rồi áp bằng `TREATAS` sau `REMOVEFILTERS ( DimMonth )`, thay cho `SAMEPERIODLASTYEAR`.
- **Phát hiện chất lượng dữ liệu:**
  - Mã giá Unknown, nhóm "Over 5 miles": quãng đường trung bình 63,7 dặm (Standard rate 9,4). Quãng đường trung bình toàn kỳ (5,84; năm 2025 là 6,59) bị kéo lệch, nên trang 5 không dùng chỉ số này.
  - 1,26 triệu chuyến thẻ có mã giá 99 gần như không ghi tiền boa (tổng 315 USD).
- **Phát hiện khác:**
  - Chuyến ngắn boa cao hơn: 25,8% so với 19,2% ở chuyến trên 5 dặm.
  - Chuyến JFK đi nhanh gấp đôi (22,3 so với 10,2 mph) nhưng tỷ lệ boa thấp hơn (20,0% so với 23,7%).
- **Kiểm tra:**
  - Số liệu đối chiếu tính bằng SQL trên `data/bi/mart_trip_profile.parquet`: vận tốc 10,878 → 11,001 mph (+1,13%), thời gian 17,52 → 17,54 phút.
  - Chưa chạy trong Power BI Desktop.

### 18/11/2026 — DuckDB bước 5: Data warehouse (OLAP mart, SCD2, runner QA)
- **OLAP mart** (`dbt/models/olap_marts/`, schema `olap`, materialized `table`), tổ chức theo grain dùng chung (người dùng chọn thay cho một mart mỗi câu):
  - `basic/mart_trips_daily` (ngày × khu vực đón × hãng × thanh toán × mã giá; 1.411.379 dòng): A1, A2, A3, A6, A8, B2, B3.
  - `basic/mart_hourly_activity` (vai trò pickup/dropoff × ngày × giờ × quận; 242.110 dòng): A4, A2 mức giờ, 5b.
  - `basic/mart_routes_monthly` (tháng × khu vực đón × khu vực trả; 823.930 dòng): A7, B5.
  - `basic/mart_trip_profile` (tháng × nhóm khách × mã giá × nhóm cự ly × thanh toán; 5.264 dòng): A5, B1, B3.
  - `advanced/mart_monthly_kpi` (tháng; 24 dòng): B2, B3, B4; trung bình và tăng trưởng MoM/YoY (tìm kỳ so sánh bằng nối theo ngày đầu tháng).
  - Macro `dbt/macros/olap_trip_measures.sql`: bộ tổng cộng dồn dùng chung (`valid_*_trips`, `sum_trip_speed`, `sum_trip_tip_rate`, `credit_tip/fare_amount`, các khoản tiền) theo phần "Measures bổ sung" của modeling.pdf; trung bình tính lại ở BI. Tổng số nguyên ép `BIGINT` (DuckDB `sum(int)` trả `HUGEINT`, Power BI/ODBC không đọc được; phát hiện khi kiểm tra kiểu cột).
  - Test: `models/olap_marts/schema.yml` (not_null, accepted_values, unique `month_start`), `tests/olap/assert_olap_marts_reconcile_fact.sql` (tổng chuyến, hành khách bằng Fact, doanh thu lệch < 1 USD ở mọi mart; mart giờ theo từng vai trò).
  - Hướng dẫn mới: `docs/guides/olap.md` (câu hỏi → mart, công thức trung bình, lưu ý cộng mart giờ).
- **5a SCD Type 2 cho `dim_location`:** snapshot `dbt/snapshots/snap_taxi_zone_lookup.yml` (cú pháp YAML dbt ≥ 1.9, `strategy: check` trên `borough`, `zone`, `service_zone`, schema `snapshots`) đọc `stg_taxi_zone_lookup`. `dim_location` đọc snapshot: `LocationSK = LocationID*100 + VersionNo`, `validfrom` (phiên bản 1 = 1900-01-01), `validto` (hiện hành = 9999-12-31), `iscurrent`. Fact tra Location theo `locationid` và giờ đón/trả nằm trong `[validfrom, validto)`. Test `tests/dimensions/assert_dim_location_scd2_valid.sql` (một bản hiện hành, các bản nối liền, bản đầu từ 1900, VersionNo liên tục); `dimensions/schema.yml` bỏ `unique` trên `locationid`, thêm not_null cho cột SCD2.
- **Runner QA viết lại cho DuckDB** (`tests/run_quality_tests.py`): bỏ `psql`/`psycopg2`/`pg_class`; mở `duckdb.connect(read_only=True)` và chứng minh chỉ đọc bằng một lệnh `CREATE TABLE` bị từ chối; phạm vi `raw | stage | dimension | fact | olap`; kiểm tra hợp đồng schema raw, đối chiếu log nạp, `source_row_number` liên tục, staging giữ đủ dòng, cờ không NULL, khóa Dimension, SCD2, nhãn Unknown, khóa -1/mồ côi của Fact, Fact theo file khớp staging (số dòng + tổng `sourcerownumber`, thay cho đếm distinct 56 s), tổng mart khớp Fact, tháng KPI liên tục; báo cáo tiếng Việt. `tasks.ps1 qa` chạy runner trong container, thêm `qa full` (= `all --include-large-scans`). `.gitignore` giữ thêm bản chạy mẫu `run_20261118T115030Z.*`. `docs/guides/testing.md` viết lại.
- `README.md`, `CLAUDE.md`, `docs/guides/dimension.md`, `docs/guides/fact.md` cập nhật theo SCD2, mart và runner QA.
- **Kiểm tra (đạt):**
  - `dbt build --select olap_marts`: 5 mart + 18 test PASS. Số liệu hợp lý: 2,9–4,2 triệu chuyến/tháng, doanh thu/chuyến 26,7–31,7 USD; tỷ lệ boa Standard 23,69%, JFK 20,03%; vận tốc Standard 10,2 mph, JFK 22,3 mph; tuyến phổ biến nhất Upper East Side South → North (568.515 chuyến).
  - **SCD2 trên database thử nghiệm riêng** (`data/warehouse/tmp/scd2_test.duckdb`: Zone Lookup + tháng 2024-01, xóa sau khi thử): build lần 1 98/98 PASS; đổi tên khu vực 161 trong raw rồi build lại: snapshot tạo phiên bản 2 (`16102`, `iscurrent`), phiên bản 1 (`16101`) đóng tại thời điểm chạy; 141.717 chuyến đã nạp vẫn trỏ `16101`, mart vẫn hiện tên cũ; tra khóa tại 2024-01-15 ra `16101`, tại thời điểm hiện tại ra `16102`; test SCD2 PASS.
  - **Dữ liệu thật:** `dbt build --full-refresh` toàn bộ project (Fact dựng lại vì SK Location đổi): 98/98 PASS trong 3 phút 12 giây (Fact 116 s). Fact 85.745.246 dòng, 0 khóa Location -1, SK Location 101..26501; `dimlocation` 266 dòng, tất cả `iscurrent`.
  - **Runner QA:** `.\tasks.ps1 qa full` 53 PASS, 0 FAIL, 1 NOT APPLICABLE, ~32 s; `qa all` (không quét lớn) 50 PASS, 4 NOT RUN. Kiểm thử âm tính trên bản sao 2 tháng có 10 dòng nạp trùng và 1 dòng bị xóa: `RAW-DUP-01` FAIL đúng 2 file, `RAW-REC-03` FAIL, mã thoát 1 (bản sao đã xóa).
  - `dbt parse` OK; `python -m compileall tests` OK.
- Commit `e28b22a` trên nhánh `feat/duckdb-warehouse`, push lên `origin`: Auto PR mở PR #6 vào `main` của `thinhdao-77/NYC_TAXI_DataPipeline`; CI **đạt** trên GitHub Actions.
- Chưa làm: Power BI (bước 6); pipeline Mage end-to-end (ingest → `dbt build`).

### 18/11/2026 — DuckDB bước 4: ETL/ELT (Dimension + Fact)
- `dim_date`: `to_char(..., 'YYYYMMDD'/'Day'/'Month')` → `strftime(..., '%Y%m%d'/'%A'/'%B')`; `generate_series` dùng literal `date '...'` và `interval 1 day`.
- `dim_time`: `generate_series(0, 23) as h` (PostgreSQL trả bảng một cột tên `h`) → `range(0, 24) as hh(h)`; ép `int` cho `timesk`/`hour`/`minute`. 6 Dimension còn lại chạy trên DuckDB không cần sửa (`distinct on`, `VALUES`, `varchar(n)` đều hỗ trợ).
- `fact_taxi_trips`: `WHERE` 6 điều kiện thay bằng `WHERE stg.is_valid_for_fact` (quy tắc nằm một chỗ ở staging); `tripdurationminutes` lấy `round(stg.trip_duration_minutes, 2)`; **4a:** `incremental_strategy='delete+insert'`, `unique_key='sourcefilename'`, vẫn lọc `batch_id > max(batchid)`.
- Thêm test `dbt/tests/facts/assert_fact_matches_staging.sql`: số dòng Fact theo file = số dòng staging `is_valid_for_fact` theo file.
- Tài liệu: `docs/guides/fact.md` thêm mục 0 (chạy trên DuckDB, cơ chế nạp, kết quả); `docs/guides/dimension.md` ghi chú DuckDB; phần `psql` cũ đánh dấu "bản cũ, tham khảo".
- **Kiểm tra (đạt):**
  - `dbt build --select staging dds.dimensions`: 8 Dimension + test PASS (lỗi duy nhất là test của Fact khi Fact chưa tồn tại). Dimension: `dimdate` 732 dòng, `dimtime` 1.441, `dimlocation` 266, `dimvendor` 5, `dimpaymenttype` 7, `dimratecode` 8; đối chiếu mẫu `20240101` = Monday/January, `20251231` = Wednesday, `1345` = Afternoon.
  - `dbt build --select fact_taxi_trips` (build đầy đủ): 94 s, 85.745.246 dòng = số dòng `is_valid_for_fact`, 24 file; 18/18 test PASS.
  - Incremental không có dữ liệu mới: 0,3 s, số dòng không đổi.
  - 4a: nạp lại `yellow_tripdata_2024-01.parquet` qua Mage (`etl_control` #32 SUCCESS, batch `20261118081015`), chạy Fact incremental: 7 s, tổng vẫn 85.745.246 dòng, file 2024-01 mang batch mới, `assert_fact_matches_staging` PASS.
  - Khóa Unknown lần đầu: `DropoffDateSK = -1` 759 dòng (trả khách 01–05/01/2026), `PassengerGroupSK = -1` 14.181.248 dòng (`passenger_count` NULL 13.525.377 + bằng 0 655.871); các khóa khác 0 dòng.
- **Sửa khóa Unknown (theo yêu cầu, cùng bước 4):** `dim_date` kéo tới 2026-01-31 (763 dòng); `dim_passenger_group` thêm `(0, 'NONE', 'Không ghi nhận hành khách', 0, 0)`; Fact join `coalesce(passenger_count, 0)`; cập nhật mô tả trong `dimensions/schema.yml`. Kiểm tra: `dbt build --select dds --full-refresh` 57/57 PASS (Fact 137 s); Fact vẫn 85.745.246 dòng, **0 dòng `-1` ở mọi khóa**, 759 dòng có `DropoffDateSK` trong 01/2026, 14.181.248 dòng nhóm `NONE`.
- Commit `644a47a` trên nhánh `feat/duckdb-dds`, push lên `origin`: Auto PR mở PR #5 vào `main` của `thinhdao-77/NYC_TAXI_DataPipeline`; CI **đạt** trên GitHub Actions.
- Chưa làm: OLAP mart, runner QA trên DuckDB (bước 5).

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
- Commit `481dd35` trên nhánh `feat/duckdb-staging`, push lên `origin`: workflow Auto PR mở PR #4 vào `main` của `thinhdao-77/NYC_TAXI_DataPipeline`; CI (cú pháp Python, `docker compose config`, `dbt parse` với dbt-duckdb) **đạt** trên GitHub Actions.
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
- Mục "Quy trình làm việc với Git" và lệnh clone trong README đã viết lại cho repo cá nhân ngày 21/11/2026.

### 16/11/2026 — Sự cố: PR merge nhầm vào repo gốc
- PR #7 (`refactor/project-structure`) được tạo và merge nhầm vào `main` của repo nhóm gốc (merge commit `39a2f34`), kéo theo cả các commit của nhánh Fact.
- Đã mở PR revert #8 trên repo nhóm gốc (nhánh `revert/pr-7` trên fork, commit `d475177`); sau khi merge, `main` gốc giống hệt `36e24d3`. Cần nhóm duyệt và merge.
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
| 4. ETL/ELT | Sửa hàm riêng PostgreSQL trong `dim_date`/`dim_time` (`to_char` → `strftime`, `generate_series` → `range`); Fact lọc bằng `is_valid_for_fact`; Fact `delete+insert` theo `sourcefilename` (4a); test `assert_fact_matches_staging` | **Xong, đã chạy trên 24 tháng** |
| 5. Data warehouse | 5 OLAP mart (schema `olap`) + test đối chiếu Fact; runner QA viết lại cho `duckdb`; SCD Type 2 cho `dim_location` bằng `dbt snapshot` (5a) | **Xong, đã chạy trên 24 tháng** |
| 6. Power BI | Xuất mart ra Parquet (người dùng chọn thay cho ODBC); file M, DAX, bản đồ và hướng dẫn (người dùng chọn thay cho dựng sẵn `.pbip`) | **Phần chuẩn bị xong**; dựng `.pbix` do người dùng làm |

### Cơ chế nạp và lịch sử dữ liệu (quyết định 17/11/2026)

Nguồn TLC là file Parquet theo tháng, không có log giao dịch, nên **không dùng CDC**. Cơ chế cho từng tầng:

| Tầng | Cơ chế | Trạng thái |
|---|---|---|
| `raw.yellow_tripdata` | Watermark theo tháng (LSET) + delete-insert theo `source_file_name` | Đã làm (bước 2) |
| `raw.taxi_zone_lookup` | Full refresh | Đã làm (bước 2) |
| Dimension danh mục (`vendor`, `payment_type`, `rate_code`, `date`, `time`, nhóm tĩnh) | Full refresh = SCD Type 1 | Giữ nguyên |
| `fact_taxi_trips` | **4a.** Đổi từ append theo `batch_id` sang `delete+insert`: chọn các `source_file_name` có `batch_id` mới hơn lần nạp Fact trước, xóa các chuyến đi của những file đó trong Fact rồi chèn lại. Mục tiêu: nạp lại một tháng ở `raw` không làm trùng Fact | **Xong (bước 4)** |
| `dim_location` | **5a (tùy chọn).** `dbt snapshot` (SCD Type 2, `strategy: check` trên `borough`, `zone`, `service_zone`) từ `raw.taxi_zone_lookup`; `dim_location` có `valid_from`, `valid_to`, `is_current`, SK riêng mỗi phiên bản; Fact tra khóa theo `pickup_datetime` nằm trong khoảng hiệu lực. Giá trị thực tế thấp (khu vực hiếm đổi), chủ yếu để minh họa SCD2 | **Xong (bước 5)**: SK = `LocationID*100 + VersionNo`, phiên bản đầu từ 1900-01-01 |

Kiểm thử cần có khi làm: 4a — nạp lại một tháng ở `raw`, chạy lại Fact, số dòng Fact của tháng đó không đổi; 5a — sửa thử một khu vực trong bản sao CSV, chạy snapshot, có 2 phiên bản và Fact cũ vẫn trỏ phiên bản cũ.

**Tạm thời không chạy được cho tới bước tương ứng:** hướng dẫn PostgreSQL còn sót trong README (mục cũ) và các phần "bản cũ, tham khảo" trong `docs/guides/`.

**Lưu ý vận hành DuckDB**
- Chỉ một tiến trình được ghi vào file. Không chạy đồng thời pipeline Mage và `dbt build`; đóng Power BI/DBeaver trước khi ghi.
- File `.duckdb` nằm trên bind mount (ổ D: của Windows) để Power BI mở trực tiếp được. Đã đo: không chậm hơn filesystem trong container (xem nhật ký bước 1).
- dbt chạy từ venv `/opt/dbt` trong container (`dbt` hoặc `.\tasks.ps1 dbt-*`). Không `pip install` gói dbt vào môi trường Mage: sẽ làm hỏng CLI Mage.
