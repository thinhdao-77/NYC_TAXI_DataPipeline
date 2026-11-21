# NYC TAXI - HƯỚNG DẪN TRIỂN KHAI TẦNG FACT (DDS)

> **Cập nhật 18/11/2026 (DuckDB):** Fact chạy bằng **dbt-duckdb** trên cùng file DuckDB với Mage (`data/warehouse/nyc_taxi.duckdb`, bảng `dds.facttaxitrip`), xem [mục 0](#0-chạy-trên-duckdb-dbt). Các mục 3 và 5 bên dưới mô tả bản PostgreSQL cũ (lệnh `psql`, bản SQL thủ công ở `sql/warehouse/`), giữ lại để tham khảo; PostgreSQL không còn trong `docker-compose.yml`. SK trong dbt sinh ổn định từ khóa tự nhiên (vd `DateSK = YYYYMMDD`), khác với `SERIAL` trong bản SQL cũ.


Tài liệu này mô tả chi tiết thiết kế, quy tắc làm sạch dữ liệu, quy trình ETL và kịch bản kiểm thử nghiệm thu cho bảng dữ kiện trung tâm **`dds.FactTaxiTrip`** thuộc mô hình kho dữ liệu NYC Yellow Taxi (Star Schema).

- **Nguồn dữ liệu:** `stage.stg_yellow_taxi_trips` kết hợp 8 bảng Dimension trong `dds`.
- **Căn cứ thiết kế:** tài liệu `docs/data_modeling/modeling.pdf` (trang 3–6).
- **Đích đến:** model dbt `dbt/models/dds/facts/fact_taxi_trips.sql` → `dds.facttaxitrip` (DuckDB). Trước 18/11/2026: `dds.FactTaxiTrip` trên PostgreSQL.

---

## 0. Chạy trên DuckDB (dbt)

| Mục | Giá trị |
| :--- | :--- |
| Model | `dbt/models/dds/facts/fact_taxi_trips.sql` → bảng `dds.facttaxitrip` |
| Nguồn | `ref('stg_yellow_taxi_trips')` (view staging) + 8 Dimension qua `ref()` |
| Điều kiện giữ dòng | `stg.is_valid_for_fact` (định nghĩa một chỗ trong staging, xem [staging.md](staging.md)) |
| Materialization | `incremental`, `incremental_strategy='delete+insert'`, `unique_key='sourcefilename'` |
| Lọc incremental | `stg.batch_id > max(batchid)` đã có trong Fact |

**Cơ chế nạp (mục 4a trong PROJECT_STATUS):**
- Lần đầu (hoặc `--full-refresh`): tạo bảng từ toàn bộ staging hợp lệ.
- Lần sau: chỉ lấy dòng có `batch_id` mới hơn batch lớn nhất trong Fact. Với các file trong lô mới, dbt **xóa mọi dòng Fact của file đó** rồi chèn lại. Nhờ vậy:
  - không có dữ liệu mới → không thay đổi gì (chạy 0,3 s);
  - nạp thêm file mới → chỉ chèn file đó;
  - **nạp lại một file đã có** (Mage thay dòng raw của file bằng batch mới) → dòng Fact cũ của file bị thay, **không trùng**.
- Giới hạn: file bị xóa hẳn khỏi raw thì dòng Fact cũ vẫn còn (test `assert_fact_matches_staging` sẽ báo); chạy `--full-refresh` để dựng lại.

```powershell
.\tasks.ps1 dbt-build dds                       # build 8 Dimension + Fact + test
.\tasks.ps1 dbt-build fact_taxi_trips           # chỉ Fact (incremental) + test
docker compose exec -T -w /home/src/dbt mage dbt build --select fact_taxi_trips --full-refresh --profiles-dir .
```

**Test** (`dbt/models/dds/facts/schema.yml`, `dbt/tests/facts/`): `not_null` và `relationships` cho các khóa SK; `assert_fact_matches_staging` so số dòng Fact theo từng file với số dòng staging có `is_valid_for_fact` (bắt nạp trùng, mất dòng do join, file thiếu hoặc thừa).

**Kết quả 18/11/2026 trên 24 tháng (2024-01 → 2025-12):**

| Chỉ số | Giá trị |
| :--- | ---: |
| Dòng staging | 89.892.322 |
| Dòng Fact (`is_valid_for_fact`) | **85.745.246 (95,39%)** |
| Build đầy đủ | 94–137 s (bộ nhớ container < 1 GB sau build); 116 s sau khi thêm SCD2 cho Location |
| Incremental, không có dữ liệu mới | 0,3 s |
| Incremental sau khi nạp lại file 2024-01 | 7 s, tổng dòng không đổi, file 2024-01 mang batch mới |
| Test Fact | 18/18 PASS |

Khóa Unknown (`-1`) trong Fact: **0 dòng ở mọi khóa**. Hai trường hợp đặc biệt được xử lý trong Dimension:
- 759 chuyến đón cuối 2025 nhưng trả khách trong 01/2026 (muộn nhất 05/01/2026): `DimDate` kéo dài tới 2026-01-31 nên `DropoffDateSK` vẫn có ngày.
- 14.181.248 chuyến có `passenger_count` NULL (13,53 triệu, chủ yếu Flex Fare) hoặc 0 (0,66 triệu): gán nhóm `NONE` (`PassengerGroupSK = 0`), Fact join bằng `coalesce(passenger_count, 0)`.

Lưu ý Power BI: `DimDate` có tháng 01/2026 nhưng không có chuyến nào **đón** trong tháng đó; lọc theo `PickupDateSK` sẽ không thấy dữ liệu 2026.

---

## 1. Đặc tả Bảng dữ kiện (Fact Table Specification)

### 1.1. Grain (Độ mịn / Hạt của dữ kiện)
Mỗi dòng trong bảng `dds.FactTaxiTrip` biểu diễn **một chuyến đi taxi đơn lẻ đã hoàn thành** được ghi nhận trên hệ thống đồng hồ tính cước của xe Yellow Taxi.

### 1.2. Danh sách Khóa ngoại (11 Foreign Keys tới 8 Dimension)
Toàn bộ khóa ngoại tham chiếu đến Surrogate Key của 8 bảng Dimension (trong dbt: SK ổn định sinh từ khóa tự nhiên). Cơ chế ETL sử dụng `LEFT JOIN` và bọc hàm `COALESCE(dim.SK, -1)` để bảo toàn 100% doanh thu, đưa các bản ghi mồ côi hoặc thiếu thông tin về dòng mặc định `-1 (Unknown)`.

| Tên cột Foreign Key | Kiểu | Bảng Dimension tham chiếu | Khóa tự nhiên nguồn | Ghi chú nghiệp vụ |
| :--- | :--- | :--- | :--- | :--- |
| `PickupDateSK` | INT | `dds.DimDate(DateSK)` | `tpep_pickup_datetime::date` | Ngày đón khách |
| `DropoffDateSK` | INT | `dds.DimDate(DateSK)` | `tpep_dropoff_datetime::date` | Ngày trả khách |
| `PickupTimeSK` | INT | `dds.DimTime(TimeSK)` | `pickup (hour, minute)` | Khung giờ đón khách |
| `DropoffTimeSK` | INT | `dds.DimTime(TimeSK)` | `dropoff (hour, minute)` | Khung giờ trả khách |
| `PickupLocationSK` | INT | `dds.DimLocation(LocationSK)` | `pu_location_id` + giờ đón trong `[ValidFrom, ValidTo)` (SCD2) | Điểm đón (Taxi Zone) |
| `DropoffLocationSK`| INT | `dds.DimLocation(LocationSK)` | `do_location_id` + giờ trả trong `[ValidFrom, ValidTo)` (SCD2) | Điểm trả (Taxi Zone) |
| `VendorSK` | INT | `dds.DimVendor(VendorSK)` | `vendor_id` | Hãng xe (CMT / VTS) |
| `PaymentTypeSK` | INT | `dds.DimPaymentType(PaymentTypeSK)` | `payment_type` | Thẻ tín dụng, tiền mặt,... |
| `RateCodeSK` | INT | `dds.DimRateCode(RateCodeSK)` | `COALESCE(ratecode_id, 99)` | Tiêu chuẩn, JFK, Newark,... |
| `PassengerGroupSK`| INT | `dds.DimPassengerGroup(PassengerGroupSK)` | `coalesce(passenger_count, 0)` | Không ghi nhận (0/NULL), 1 người, 2-4 người, 5+ |
| `DistanceGroupSK` | INT | `dds.DimDistanceGroup(DistanceGroupSK)` | `trip_distance` | <2mi, 2-5mi, >5mi |

### 1.3. Base Measures vật lý (Lưu trực tiếp trong Fact - Additive Measures)
Theo đúng trang 3 của tài liệu `modeling.pdf`, Fact lưu 14 measures cơ sở có thể cộng dồn theo mọi chiều phân tích:

| Tên cột Measure | Kiểu | Ý nghĩa nghiệp vụ |
| :--- | :--- | :--- |
| `TotalTrips` | INT | Luôn bằng `1` cho mỗi bản ghi hợp lệ. Dùng `SUM(TotalTrips)` để đếm tổng số chuyến. |
| `PassengerCount` | INT | Số lượng hành khách ghi nhận trên xe. |
| `TripDistance` | DOUBLE | Quãng đường di chuyển (dặm - miles). |
| `TripDurationMinutes` | DOUBLE | Thời lượng chuyến đi tính bằng phút: `(DropoffDateTime - PickupDateTime)`. |
| `FareAmount` | DOUBLE | Tiền cước chính tính theo đồng hồ. |
| `Extra` | DOUBLE | Phụ phí giờ cao điểm ($1.00) / ban đêm ($0.50). |
| `MTATax` | DOUBLE | Thuế/phí MTA ($0.50). |
| `TipAmount` | DOUBLE | Tiền boa ghi nhận (chủ yếu từ thanh toán thẻ tín dụng). |
| `TollsAmount` | DOUBLE | Tiền phí cầu đường, hầm qua trạm thu phí. |
| `ImprovementSurcharge` | DOUBLE | Phí cải thiện hạ tầng và dịch vụ taxi. |
| `CongestionSurcharge` | DOUBLE | Phụ phí chống ùn tắc giao thông Manhattan ($2.50). |
| `AirportFee` | DOUBLE | Phụ phí đưa/đón tại các sân bay JFK, LaGuardia ($1.25). |
| `CBDCongestionFee` | DOUBLE | Phí ùn tắc khu vực trung tâm Manhattan (áp dụng từ 2025). |
| `TotalAmount` | DOUBLE | Tổng số tiền thanh toán thực tế của hành khách. |

### 1.4. Audit & Lineage Metadata (Kiểm toán & Nguồn gốc dữ liệu)
Bảng Fact được trang bị 4 cột metadata kỹ thuật chuẩn Kimball để phục vụ **nạp gia tăng (Incremental Load)**, theo dõi nguồn gốc dữ liệu (Data Lineage) và kiểm toán hệ thống:

| Tên cột Metadata | Kiểu | Ý nghĩa kỹ thuật |
| :--- | :--- | :--- |
| `SourceFileName` | VARCHAR(200) | Tên file Parquet nguồn gốc (ví dụ: `yellow_tripdata_2025-01.parquet`). |
| `SourceRowNumber` | BIGINT | Thứ tự dòng trong file Parquet gốc (Lineage tracking). |
| `BatchID` | BIGINT | Mã phiên nạp (Batch ID) từ pipeline Mage / Staging. |
| `LoadedAt` | TIMESTAMP | Thời điểm bản ghi được nạp vào Fact (Watermark). |

### 1.5. Semantic Measures (Được tính toán động trên BI / OLAP - Không lưu vật lý)
Theo trang 4 của `modeling.pdf`, các measures phái sinh sau được định nghĩa bằng công thức động (DAX / SQL aggregations) để tối ưu dung lượng và tránh sai sót khi tổng hợp nhiều chiều:
- **`AvgRevenuePerTrip`** = `SUM(TotalAmount) / SUM(TotalTrips)`
- **`AvgPassengersPerTrip`** = `SUM(PassengerCount) / SUM(TotalTrips)`
- **`AvgDistancePerTrip`** = `SUM(TripDistance) / SUM(TotalTrips)`
- **`AvgTripDuration`** = `SUM(TripDurationMinutes) / SUM(TotalTrips)`
- **`AvgSpeed`** = `SUM(TripDistance) / (SUM(TripDurationMinutes) / 60.0)` *(mph)*
- **`AvgTipRate`** = `SUM(TipAmount) / NULLIF(SUM(FareAmount), 0) * 100%`

---

## 2. Quy tắc Làm sạch Dữ liệu (ETL Data Quality Rules)

Trong quá trình nạp từ `stage.stg_yellow_taxi_trips` sang Fact, các bản ghi vi phạm các điều kiện sau sẽ bị loại bỏ. Từ 18/11/2026 các điều kiện này được tính một lần trong staging thành cờ `is_valid_for_fact`; Fact chỉ lọc `WHERE stg.is_valid_for_fact`:
1. **Lỗi thời gian di chuyển:** `tpep_dropoff_datetime <= tpep_pickup_datetime` (thời lượng chuyến đi $\le 0$).
2. **Ngoài phạm vi nghiên cứu:** Chuyến đi có giờ đón trước `2024-01-01` hoặc từ `2026-01-01` trở đi.
3. **Lỗi tài chính âm:** `fare_amount < 0` hoặc `total_amount < 0` (các giao dịch tranh chấp, hủy cước, hoàn tiền).
4. **Lỗi cự ly âm:** `trip_distance < 0`.

---

## 3. Quy trình Nạp Gia tăng trên PostgreSQL (bản cũ, tham khảo)

Quy trình nạp Fact được nâng cấp toàn diện theo kiến trúc **Incremental Load (Nạp gia tăng)** bảo toàn giao dịch (`BEGIN ... COMMIT`), hoàn toàn không sử dụng lệnh `TRUNCATE` hay `DROP` phá hủy bảng:
1. **Lần chạy đầu tiên (Initial Load):** Bảng Fact chưa có dữ liệu, toàn bộ dữ liệu hợp lệ từ Staging sẽ được nạp vào Fact.
2. **Các lần chạy tiếp theo (Incremental Run):** Pipeline tự động so sánh Watermark (`BatchID` lớn hơn `MAX(BatchID)` đã có trong Fact hoặc các file mới chưa từng nạp). Do đó:
   - Nếu không có dữ liệu mới: Trả về `INSERT 0 0` an toàn, không nhân đôi số dòng, không làm gián đoạn các truy vấn đang đọc.
   - Khi có file mới: Chỉ nạp riêng file mới đó, thời gian nạp chỉ vài chục giây thay vì chạy lại toàn bộ lịch sử nhiều năm.
   - Nếu gặp sự cố giữa chừng: Khối giao dịch (`BEGIN; ... COMMIT;`) tự động `ROLLBACK`, bảng Fact cũ không bao giờ bị mất dữ liệu.

### Bước 1: Khởi tạo bảng Fact & Indexes (Idempotent DDL)
Chạy lệnh trong PowerShell tại thư mục gốc dự án:
```powershell
Get-Content sql\warehouse\03_create_fact.sql | docker compose exec -T postgres psql -U taxi_user -d nyc_taxi_staging
```

### Bước 2: Nạp gia tăng vào Fact từ Staging (Incremental Load)
```powershell
Get-Content sql\warehouse\04_load_fact.sql | docker compose exec -T postgres psql -U taxi_user -d nyc_taxi_staging
```

### Bước 3: Kiểm thử đối chiếu dữ liệu & phân phối Batch
```powershell
Get-Content sql\warehouse\05_verify_fact.sql | docker compose exec -T postgres psql -P pager=off -U taxi_user -d nyc_taxi_staging
```

---

## 4. Tích hợp dbt (Data Build Tool)

Cách chạy hiện tại xem [mục 0](#0-chạy-trên-duckdb-dbt). Cấu trúc trong thư mục `dbt/`:
- **File cấu hình:** `dbt/dbt_project.yml` và `dbt/profiles.yml`.
- **Macro xử lý schema:** `dbt/macros/generate_schema_name.sql` (giữ đúng schema `dds`).
- **Model Fact:** `dbt/models/dds/facts/fact_taxi_trips.sql`.
- **Tests tự động:** `dbt/models/dds/facts/schema.yml` (`not_null`, `relationships`) và `dbt/tests/facts/assert_fact_matches_staging.sql`.

Chạy kiểm thử dbt:
```powershell
.\tasks.ps1 dbt-test fact_taxi_trips
```
*Kết quả 18/11/2026 (DuckDB, 24 tháng):* `Done. PASS=18 WARN=0 ERROR=0`

---

## 5. Tiêu chí nghiệm thu và kết quả kiểm thử — số liệu PostgreSQL cũ, xem mục 0 cho số liệu DuckDB

Dưới đây là các tiêu chuẩn nghiệm thu và kết quả đo đạc thực tế (dùng cho test plan và báo cáo):

### 5.1. Tiêu chí Nghiệm thu (Acceptance Criteria)
- [x] **Toàn vẹn khóa ngoại (Referential Integrity):** Không có bản ghi nào bị lỗi trỏ sai khóa Dimension (`0 lỗi`). Toàn bộ 16 tests của dbt đạt **PASS 100%**.
- [x] **Bảo toàn dữ liệu:** Tỷ lệ nạp thành công đạt trên 95%. Tất cả các dòng bị loại (khoảng 4-5%) đều có lý do chính đáng được phân loại rõ ràng (cước âm, thời gian âm).
- [x] **Cơ chế Idempotent:** Khi chạy lại script `04_load_fact.sql`, dữ liệu cũ được dọn dẹp và nạp lại chính xác, không bị nhân đôi số dòng.

### 5.2. Kết quả Đo đạc Thực tế trên 2 Mốc Dữ liệu

| Chỉ số kiểm thử | Mốc 1: Tháng 01/2025 (1 file) | Mốc 2: Tháng 01 & 02/2025 (2 file) |
| :--- | :--- | :--- |
| **Tổng dòng Staging đọc vào** | 3.475.226 dòng | **7.052.769 dòng** |
| **Tổng dòng Fact nạp thành công** | 3.328.747 dòng (95,79%) | **6.718.093 dòng (95,25%)** |
| **Tổng dòng bị loại (Dữ liệu rác)** | 146.479 dòng (4,21%) | **334.676 dòng (4,75%)** |
| - *Lý do tiền cước âm (`fare < 0`)* | 144.118 dòng | 329.839 dòng |
| - *Lý do tổng tiền âm (`total < 0`)* | 63.037 dòng | 144.476 dòng |
| - *Lý do thời gian vô lý (`dropoff <= pickup`)* | 2.051 dòng | 4.398 dòng |
| **Tỷ lệ khóa mồ côi (Unknown = -1)** | Ngày/Giờ/Vị trí/Hãng xe: `0` dòng | Ngày/Giờ/Vị trí/Hãng xe: `0` dòng |
| **Thời lượng chuyến đi trung bình** | 15.06 phút | **15.25 phút** |
| **Quãng đường di chuyển trung bình** | 5.39 miles (~8.6 km) | **5.54 miles** |
| **Tiền cước trung bình (`FareAmount`)** | $18.33 | **$18.25** |
| **Tổng tiền trung bình (`TotalAmount`)** | $27.12 | **$26.90** |

---

## 6. Hướng dẫn Phân tích & Viết DAX (Dành cho Người làm Power BI / OLAP)

Khi kết nối Power BI hoặc viết các truy vấn OLAP Data Marts, bảng `FactTaxiTrip` liên kết với các bảng Dimension theo mô hình hình sao (Star Schema 1-n) như sau:

1. **Thống kê theo thời gian (Câu 1, Câu 4):**
   - Nối `FactTaxiTrip.PickupDateSK` ➔ `DimDate.DateSK`.
   - Nối `FactTaxiTrip.PickupTimeSK` ➔ `DimTime.TimeSK`.
2. **Thống kê doanh thu theo Quận / Hãng xe (Câu 2):**
   - Nối `FactTaxiTrip.PickupLocationSK` ➔ `DimLocation.LocationSK` (Lấy `DimLocation.Borough`).
   - Nối `FactTaxiTrip.VendorSK` ➔ `DimVendor.VendorSK` (Lấy `DimVendor.VendorName`).
3. **Thống kê hình thức thanh toán (Câu 3):**
   - Nối `FactTaxiTrip.PaymentTypeSK` ➔ `DimPaymentType.PaymentTypeSK`.
4. **Phân tích nhóm khách & cự ly (Câu 5):**
   - Nối `FactTaxiTrip.PassengerGroupSK` ➔ `DimPassengerGroup.PassengerGroupSK`.
   - Nối `FactTaxiTrip.DistanceGroupSK` ➔ `DimDistanceGroup.DistanceGroupSK`.
5. **Công thức DAX mẫu cơ bản:**
   ```dax
   Total Trips = SUM(FactTaxiTrip[TotalTrips])
   Total Revenue = SUM(FactTaxiTrip[TotalAmount])
   Avg Speed MPH = DIVIDE(SUM(FactTaxiTrip[TripDistance]), DIVIDE(SUM(FactTaxiTrip[TripDurationMinutes]), 60))
   Avg Tip Rate = DIVIDE(SUM(FactTaxiTrip[TipAmount]), SUM(FactTaxiTrip[FareAmount]))
   ```
