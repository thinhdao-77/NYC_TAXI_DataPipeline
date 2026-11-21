# NYC Yellow Taxi Data Warehouse

> **Đang chuyển từ PostgreSQL sang DuckDB (từ 16/11/2026).** Đã xong bước 1 (Docker Compose, không còn PostgreSQL), bước 2 (ingestion vào DuckDB, xem [docs/guides/ingestion.md](docs/guides/ingestion.md)) bước 3 (staging bằng dbt-duckdb, xem [docs/guides/staging.md](docs/guides/staging.md)) bước 4 (Dimension/Fact trên DuckDB, xem [docs/guides/fact.md](docs/guides/fact.md#0-chạy-trên-duckdb-dbt)) bước 5 (OLAP mart, SCD2 cho `dim_location`, runner QA trên DuckDB, xem [docs/guides/olap.md](docs/guides/olap.md) và [docs/guides/testing.md](docs/guides/testing.md)) và phần chuẩn bị bước 6 (xuất Parquet, truy vấn M, measure DAX, bản đồ cho Power BI, xem [docs/guides/powerbi.md](docs/guides/powerbi.md)). Các hướng dẫn PostgreSQL bên dưới sẽ được viết lại theo từng bước; tiến độ xem [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md#8-chuyển-sang-duckdb).

Dự án xây dựng quy trình xử lý và phân tích dữ liệu **NYC Yellow Taxi Trip Records** cho giai đoạn 2024–2025. Repo hiện có: nạp dữ liệu nguồn vào PostgreSQL Staging bằng Mage.ai, và tầng DDS (8 Dimension + Fact) build bằng dbt. OLAP mart, Power BI và pipeline ELT end-to-end đang phát triển tiếp. Tình trạng chi tiết: [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md).

## Trạng thái dự án

| Hạng mục | Trạng thái hiện tại |
|---|---|
| PostgreSQL Staging | Có DDL tạo schema, bảng chuyến đi, bảng Zone Lookup và bảng log ETL |
| Nạp dữ liệu bằng Mage.ai | Có pipeline nạp Taxi Zone Lookup và Yellow Taxi Parquet; pipeline chuyến đi hỗ trợ tải file, retry, nạp theo batch và chạy lại |
| Docker Compose | Có cấu hình chạy PostgreSQL và Mage.ai |
| Dimension DDS | 8 model dbt trong `dbt/models/dds/dimensions/` (bản SQL thủ công tham khảo ở `sql/warehouse/`) |
| Fact DDS | Model dbt incremental `dbt/models/dds/facts/fact_taxi_trips.sql` |
| dbt | Có `dbt_project.yml`, `profiles.yml`, sources, test schema; `dbt parse` chạy được. Chưa chạy trên dữ liệu đầy đủ |
| OLAP | Chưa có mart trong `dbt/models/olap_marts/` |
| End-to-end ELT | Chưa có pipeline Mage gọi ingestion → dbt |
| CI | GitHub Actions: kiểm tra cú pháp Python, `docker compose config`, `dbt parse` |
| Power BI | Dashboard 7 trang, template `powerbi/dashboard/NYC_Taxi_Dashboard.pbit` (đọc Parquet từ `.\tasks.ps1 export-bi`); hướng dẫn: [docs/guides/powerbi.md](docs/guides/powerbi.md) |

> README này mô tả trạng thái của repo hiện tại. Các mô hình Dimension, Fact, truy vấn OLAP và dashboard là mục tiêu phát triển tiếp, không phải chức năng đã triển khai đầy đủ.

## Kiến trúc

```text
NYC Taxi source files
        │
        ▼
Mage.ai ingestion
        │
        ▼
PostgreSQL: stage / control
        │
        ├── stage.stg_yellow_taxi_trips
        ├── stage.stg_taxi_zone_lookup
        └── control.etl_control
        │
        ▼
dbt: dds.dim* (8 Dimension) → dds.facttaxitrip
        │
        ▼
OLAP mart / Power BI (kế hoạch phát triển)
```

| Thành phần | Công nghệ | Vai trò |
|---|---|---|
| Dữ liệu chuyến đi | Parquet | Yellow Taxi Trip Records theo tháng, 2024–2025 |
| Dữ liệu tham chiếu | CSV, ZIP | Taxi Zone Lookup và ranh giới Taxi Zone |
| Orchestration / ingestion | Mage.ai, Python, PyArrow | Đọc, tải và nạp dữ liệu vào PostgreSQL |
| Staging / control | PostgreSQL | Lưu dữ liệu nguồn và lịch sử các lần nạp |
| Transformation / analytics | dbt, PostgreSQL | Build Dimension và Fact (DDS); dự kiến thêm mart OLAP |
| Visualization | Power BI | Dự kiến xây dựng dashboard và bản đồ |

## Cấu trúc repository

```text
NYC_TAXI_DataPipeline/
├── .github/workflows/ci.yml         # CI: cú pháp Python, compose config, dbt parse
├── .env.example
├── Dockerfile                       # Image Mage + requirements.txt
├── docker-compose.yml
├── requirements.txt                 # gói thêm cho Mage (duckdb)
├── requirements-dbt.txt             # dbt, cài trong venv riêng /opt/dbt
├── tasks.ps1                        # Lệnh thường dùng: .\tasks.ps1 help
├── README.md
├── data/
│   ├── download_raw.ps1
│   ├── raw/                         # File tải về, không commit
│   ├── reference/                   # Taxi Zone Lookup và ranh giới khu vực
│   └── warehouse/                   # File DuckDB nyc_taxi.duckdb, không commit
├── dbt/                             # Tầng transform chính
│   ├── dbt_project.yml, profiles.yml
│   ├── macros/
│   ├── models/
│   │   ├── sources.yml              # stage.stg_yellow_taxi_trips, stage.stg_taxi_zone_lookup
│   │   ├── staging/
│   │   ├── dds/{dimensions,facts}/
│   │   └── olap_marts/
│   ├── seeds/
│   └── tests/
├── docs/
│   ├── PROJECT_STATUS.md            # Tình trạng dự án, cập nhật theo mỗi thay đổi
│   ├── guides/                      # staging, dimension, fact, testing
│   ├── data_modeling/
│   └── test_plans_and_logs/      # test plan + một lần chạy mẫu (log mới không commit)
├── mage/                            # Ingestion / orchestration
│   ├── data_exporters/
│   ├── data_loaders/
│   ├── pipelines/                   # ingest_zone_lookup, ingest_yellow_trips (ghi vào DuckDB)
│   ├── transformers/
│   ├── custom/
│   └── io_config.yaml
├── powerbi/
├── sql/
│   ├── ddl/                         # DDL Staging, Docker tự chạy khi tạo volume lần đầu
│   ├── profiling/                   # SQL/Python kiểm tra dữ liệu nguồn
│   └── warehouse/                   # SQL thủ công Dimension/Fact (tham khảo, đối chiếu)
└── tests/                           # Runner QA chỉ đọc
```

Các file hướng dẫn chi tiết:

- [Hướng dẫn chạy Staging](docs/guides/staging.md)
- [Dimension](docs/guides/dimension.md), [Fact](docs/guides/fact.md)
- [Runner kiểm thử](docs/guides/testing.md)

## Yêu cầu

- Git
- Docker Desktop và Docker Compose
- PowerShell trên Windows (các lệnh trong hướng dẫn chạy Staging sử dụng PowerShell)
- Kết nối Internet khi cần tải Parquet từ nguồn
- Đủ dung lượng cho dữ liệu và Docker. Theo hướng dẫn Staging, toàn bộ dữ liệu Parquet khoảng 1,5 GB và bảng staging có thể chiếm khoảng 20 GB sau khi nạp đủ.
- Nên có RAM từ 12 GB để chạy cấu hình Docker hiện tại; tham khảo cách giới hạn WSL trong [docs/guides/staging.md](docs/guides/staging.md).

Không cần cài PostgreSQL hoặc Python trực tiếp trên máy để chạy các pipeline Mage trong Docker.

## Bắt đầu nhanh: PostgreSQL Staging và Mage

### 1. Lấy source và cấu hình môi trường

```powershell
git clone https://github.com/thinhdao-77/NYC_TAXI_DataPipeline.git
Set-Location NYC_TAXI_DataPipeline
Copy-Item .env.example .env
```

Mở `.env`, thay `POSTGRES_PASSWORD=change_me` bằng mật khẩu riêng trước lần khởi động đầu tiên. Không commit `.env`.

Các biến mặc định trong `.env.example`:

| Biến | Giá trị mẫu | Ý nghĩa |
|---|---|---|
| `POSTGRES_DB` | `nyc_taxi_staging` | Tên database |
| `POSTGRES_USER` | `taxi_user` | Tài khoản database |
| `POSTGRES_PASSWORD` | `change_me` | Cần thay bằng mật khẩu riêng |
| `POSTGRES_HOST` | `postgres` | Tên service trong Docker network |
| `POSTGRES_PORT` | `5432` | Cổng PostgreSQL trong Docker network |

### 2. Khởi động dịch vụ

```powershell
docker compose up -d --build
docker compose ps
```

Chờ service `postgres` ở trạng thái `healthy` và Mage chạy. Giao diện Mage: <http://localhost:6789>.

Docker Compose cấu hình PostgreSQL và Mage với `restart: unless-stopped`, giới hạn bộ nhớ, và healthcheck cho PostgreSQL. Các tham số cụ thể nằm trong [docker-compose.yml](docker-compose.yml).

### 3. Xác nhận các bảng Staging

Các script trong `sql/ddl/` được PostgreSQL image chạy khi khởi tạo volume lần đầu. Kiểm tra bảng:

```powershell
docker compose exec -T postgres psql -P pager=off -U taxi_user -d nyc_taxi_staging -c "\dt stage.*" -c "\dt control.*"
```

Các bảng dự kiến:

- `stage.stg_yellow_taxi_trips`
- `stage.stg_taxi_zone_lookup`
- `control.etl_control`

Nếu đã có volume PostgreSQL từ trước, thay đổi các script khởi tạo không tự chạy lại trên volume đó. Hướng dẫn kiểm tra và chạy DDL thủ công xem trong [docs/guides/staging.md](docs/guides/staging.md).

### 4. Nạp Taxi Zone Lookup

Trong Mage, mở pipeline `ingest_zone_lookup`, sau đó chạy block `export_zone_lookup` cùng các upstream block. Pipeline đọc `data/reference/taxi_zone_lookup.csv` và nạp vào `stage.stg_taxi_zone_lookup`.

Chi tiết thao tác trên Mage UI được mô tả trong [docs/guides/staging.md](docs/guides/staging.md).

### 5. Nạp Yellow Taxi Trip Records

Mở pipeline `ingest_trips_to_postgres`. Mặc định biến `file_name` là `ALL`, nghĩa là pipeline xét các tháng 2024–2025.

Các biến pipeline được hỗ trợ:

| Biến | Ví dụ | Ý nghĩa |
|---|---|---|
| `file_name` | `yellow_tripdata_2024-01.parquet` | Chỉ nạp một file cụ thể |
| `file_name` | `ALL` | Xét toàn bộ các tháng trong phạm vi và bộ lọc |
| `year` | `2024` | Chỉ xét một năm |
| `start_month` | `2024-01` | Tháng bắt đầu |
| `end_month` | `2024-03` | Tháng kết thúc |
| `use_lset` | `true` | Bắt đầu từ tháng LSET liên tục cuối cùng; file đã thành công sẽ được bỏ qua |

Pipeline có thể tự tải các Parquet còn thiếu vào `data/raw/`; chạy script tải trước là tùy chọn:

```powershell
powershell -ExecutionPolicy Bypass -File data\download_raw.ps1
```

Để kiểm tra lịch sử nạp:

```powershell
docker compose exec -T postgres psql -P pager=off -U taxi_user -d nyc_taxi_staging -c "SELECT source_file_name, rows_read, rows_loaded, status, started_at, finished_at FROM control.etl_control ORDER BY control_id;"
```

Pipeline nạp theo batch, thử lại khi mở kết nối PostgreSQL hoặc tải file, ghi log trạng thái theo file và tiếp tục xét các file còn lại khi một file lỗi. Nếu kết nối bị gián đoạn trong lúc nạp, giao dịch của file đó sẽ thất bại; xem log `FAILED`, xử lý nguyên nhân rồi chạy lại pipeline để nạp lại file. Không chạy đồng thời nhiều lượt nạp trên cùng một file.

> Hướng dẫn đầy đủ về biến Mage, kiểm tra dữ liệu, SQL profiling, chạy lại và xử lý sự cố nằm trong [docs/guides/staging.md](docs/guides/staging.md).

## Kiểm tra dữ liệu Staging

Các truy vấn kiểm tra dữ liệu đặt tại `sql/profiling/`. Chạy truy vấn bằng PowerShell, ví dụ:

```powershell
Get-Content sql\profiling\03_profile_by_vendor.sql | docker compose exec -T postgres psql -P pager=off -U taxi_user -d nyc_taxi_staging
```

Một số truy vấn cần tham số hoặc tùy chọn `psql`; xem phần tương ứng trong [docs/guides/staging.md](docs/guides/staging.md) trước khi chạy. Một số phép kiểm tra quét toàn bảng lớn và có thể mất vài phút.

Staging giữ dữ liệu nguồn và các cột kiểm toán; các bước làm sạch, lọc nghiệp vụ và mô hình hóa thuộc các tầng tiếp theo.

## Kiểm thử ETL Stage và Dimension

Runner QA chỉ đọc nằm trong `tests/run_quality_tests.py`; hướng dẫn và Test Plan ở `docs/guides/testing.md` và `docs/test_plans_and_logs/test-plan.md`.

```powershell
python tests\run_quality_tests.py --suite smoke
python tests\run_quality_tests.py --suite all
```

Các kết quả được lưu dạng Markdown và JSON dưới `docs/test_plans_and_logs/runs/`. Full scans trên bảng trips chỉ chạy khi thêm `--include-large-scans`. Runner không gọi script ETL hoặc DDL/DML.

## dbt: Dimension và Fact

Tầng DDS được build bằng dbt, chạy trong container Mage (image đã cài `dbt-postgres` theo `requirements.txt`). Cần nạp Staging trước.

```powershell
.\tasks.ps1 dbt-build                  # build + test toàn bộ model
.\tasks.ps1 dbt-build dim_vendor       # một model
.\tasks.ps1 dbt-run fact_taxi_trips    # chỉ chạy Fact (incremental theo batch_id)
```

Lệnh tương đương không dùng script:

```powershell
docker compose exec -T mage dbt build --project-dir /home/src/dbt --profiles-dir /home/src/dbt
```

| Model | Bảng vật lý | Surrogate key |
|---|---|---|
| `dim_date` | `dds.dimdate` | `YYYYMMDD` |
| `dim_time` | `dds.dimtime` | `hour * 100 + minute` |
| `dim_location`, `dim_vendor`, `dim_payment_type`, `dim_rate_code` | `dds.dimlocation`, ... | bằng mã tự nhiên |
| `dim_passenger_group`, `dim_distance_group` | `dds.dimpassengergroup`, `dds.dimdistancegroup` | 1..3 (tĩnh) |
| `fact_taxi_trips` | `dds.facttaxitrip` | — (incremental) |

Mỗi Dimension có dòng Unknown `SK = -1`. SK được sinh ổn định để Fact incremental không bị lệch khóa khi Dimension build lại.

`sql/warehouse/` giữ bản SQL thủ công (`psql`) của Dimension/Fact để tham khảo và đối chiếu. **Không trộn** hai cách trên cùng database: dbt build lại bảng Dimension mỗi lần chạy, nên khóa ngoại do `03_create_fact.sql` tạo sẽ bị xóa theo.

OLAP mart và Power BI chưa được triển khai.

## Cấu hình và lưu ý dữ liệu

- Dữ liệu thô trong `data/raw/`, file `.env`, file DuckDB và dữ liệu sinh ra của Mage không nên commit.
- PostgreSQL lưu dữ liệu trong Docker volume `pgdata`; `docker compose down` không xóa volume.
- Không dùng `docker compose down -v` trừ khi chủ động muốn xóa dữ liệu PostgreSQL cục bộ.
- Đổi mật khẩu trong `.env` không tự đổi mật khẩu đã được khởi tạo trong volume hiện có.
- Dữ liệu chuyến đi được nạp vào `stage.stg_yellow_taxi_trips`; nhật ký mỗi lần nạp được lưu trong `control.etl_control`.

## Quy trình làm việc với Git

Repo cá nhân, một người phát triển. Quy trình: tạo nhánh từ `main` mới nhất → commit → push → workflow `auto-pr.yml` tự mở Pull Request vào `main` → CI (`ci.yml`) chạy theo `push` → merge. Repo bật *Automatically delete head branches*, nên sau khi merge chỉ cần dọn nhánh local.

```powershell
# Lấy code
git clone https://github.com/thinhdao-77/NYC_TAXI_DataPipeline.git
Set-Location NYC_TAXI_DataPipeline

# Tạo nhánh từ main mới nhất
git checkout main
git pull --ff-only
git checkout -b feat/<pham-vi>

# Kiểm tra và lưu thay đổi
git status
git add <duong-dan-file>
git commit -m "feat(<scope>): describe the change"
git push -u origin feat/<pham-vi>

# Sau khi merge PR
git checkout main
git pull --ff-only
.	asks.ps1 prune-branches
```

Không dùng `git add .` một cách máy móc. Kiểm tra `git status` để tránh đưa `.env`, dữ liệu lớn, file `.pbix` hoặc file sinh tự động vào commit.

### Quy ước commit

```text
<type>(<scope>): <mô tả ngắn>
```

Một số type thường dùng: `feat`, `fix`, `test`, `docs`, `chore`, `refactor`. Scope có thể là `staging`, `mage`, `dbt`, `dim`, `fact`, `olap`, `powerbi` hoặc `docs`.

## Lộ trình

Lộ trình hoàn thiện gồm: triển khai cấu hình và model dbt; xây dựng DDS/OLAP; tích hợp pipeline end-to-end; bổ sung kiểm thử; sau đó hoàn thiện Power BI và báo cáo. Chỉ đánh dấu các hạng mục là hoàn thành khi code và hướng dẫn chạy tương ứng đã có trong repo và được kiểm thử.
