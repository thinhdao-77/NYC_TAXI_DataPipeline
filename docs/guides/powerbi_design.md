# Thiết kế dashboard Power BI

Hệ thống thiết kế dùng chung cho 7 trang báo cáo và đặc tả chi tiết từng trang. Cách dựng model (truy vấn, quan hệ, measure): [powerbi.md](powerbi.md).

## 1. Nguyên tắc áp dụng

| # | Nguyên tắc | Áp dụng trong báo cáo |
|---|---|---|
| 1 | Thuộc tính tiền chú ý: ưu tiên **chiều dài** và **vị trí**; không dùng **kích thước** để so sánh; không nhồi nhiều thuộc tính vào một biểu đồ, tách thành nhiều panel chung trục | So sánh định lượng bằng cột/thanh (chiều dài) và đường (vị trí). Không dùng bubble để so sánh số. Nhiều chỉ số theo thời gian → **small multiples** (nhiều biểu đồ đường xếp chồng, chung trục X), không dùng biểu đồ hai trục Y |
| 2 | Màu có mục đích; ba loại bảng màu (tuần tự, phân kỳ, danh mục); thân thiện người mù màu: **không đỏ–xanh lá**, dùng **xanh dương–cam**; cẩn trọng xanh dương–tím, hồng/đỏ–xám, xám–nâu | Mặc định **một màu xanh dương** cho dữ liệu; màu chỉ thêm khi mã hóa một ý nghĩa. Tăng = xanh dương ▲, giảm = cam ▼ (kèm ký hiệu, không chỉ dựa vào màu). Bảng màu danh mục dựa trên Okabe–Ito, xếp để xanh dương không đứng cạnh tím |
| 3 | Trục: biểu đồ mã hóa bằng chiều dài/diện tích **bắt đầu từ 0**; biểu đồ mã hóa bằng vị trí (đường, điểm) có thể không chứa 0 | Cột, thanh, data bar trong bảng, area: trục và giá trị nhỏ nhất = 0. Biểu đồ đường: trục Y tự động (không ép 0) để thấy biến động theo tháng; luôn hiện nhãn trục để không gây hiểu sai |
| 4 | Nên dùng cột/thanh (đã sắp xếp), đường, scatter, bullet, highlight table, choropleth, dot plot, bảng; **tránh pie/donut/radial** | Không có pie/donut. Tỷ trọng thể hiện bằng cột % trong bảng hoặc thanh ngang sắp xếp. Bản đồ khu vực dùng choropleth (Shape map) |
| 5 | Thông tin quan trọng **bên trái**; bộ lọc bên trái cho người dùng mới; **không xoay chữ**; phân cấp cỡ chữ nhất quán | Người xem là nhà tuyển dụng / người lần đầu xem → **thanh bộ lọc bên trái**. Trong vùng dữ liệu: KPI ở hàng trên, bắt đầu từ trái; biểu đồ chính bên trái. Tắt tiêu đề trục (chữ dọc), tên chỉ số đặt ở tiêu đề visual; trục thời gian dạng liên tục để nhãn nằm ngang; thanh ngang thay cho cột khi nhãn danh mục dài |
| 6 | Mọi quyết định là đánh đổi; trung thực và công năng trước, thẩm mỹ sau | Mỗi trang có mục "Đánh đổi". Chỉ số có vấn đề chất lượng dữ liệu được ghi chú ngay trên trang (vd hành khách) |

## 2. Hệ thống màu

Nhập theme một lần: **View > Themes > Browse for themes** > `powerbi/theme/nyc_taxi_theme.json` (đặt sẵn bảng màu danh mục, màu tăng/giảm, màu tuần tự, cỡ chữ, tắt tiêu đề trục). Nếu Power BI báo lỗi khi nhập, xóa khối `visualStyles` trong file và đặt các tùy chọn đó bằng tay.

### 2.1 Màu giao diện (trung tính)

| Vai trò | Mã | Dùng cho |
|---|---|---|
| Nền trang | `#FFFFFF` | Canvas |
| Nền thanh bộ lọc | `#F3F5F8` | Hình chữ nhật bên trái, nền header của bảng |
| Viền | `#E1E5EB` | Viền card, đường kẻ phân vùng |
| Lưới | `#E6E9EE` | Gridline ngang |
| Chữ chính | `#1F2933` | Tiêu đề, số KPI |
| Chữ phụ | `#5F6B7A` | Phụ đề, nhãn trục, nhãn KPI |
| Chữ mờ | `#8A94A3` | Chú thích, dòng "Unknown"/"N/A" |

### 2.2 Màu dữ liệu

| Loại | Mã màu | Dùng khi |
|---|---|---|
| **Chính** (một chuỗi dữ liệu) | `#1F5AA6` | Mặc định cho mọi cột, đường, thanh |
| **Nhấn** (làm nổi bật một phần) | `#E69F00` | Chỉ một phần tử cần chú ý (vd tháng đang so sánh, top 1) |
| **Tăng / tốt** | `#1F5AA6` + ▲ | Giá trị % thay đổi dương |
| **Giảm / xấu** | `#C65A00` + ▼ | Giá trị % thay đổi âm |
| **Tuần tự** (thấp → cao) | `#EAF1FA` → `#A9C8EA` → `#6FA3D8` → `#1F5AA6` → `#123B70` | Heatmap, choropleth một chiều, data bar (`#6FA3D8`) |
| **Phân kỳ** (âm ← 0 → dương) | `#C65A00` → `#F0A35E` → `#F2F2F2` → `#7FB0DE` → `#1F5AA6` | Chênh lệch có điểm 0 ý nghĩa (vd đón − trả theo khu vực) |
| **Danh mục** (theo thứ tự) | `#1F5AA6`, `#E69F00`, `#56B4E9`, `#009E73`, `#D55E00`, `#CC79A7`, `#8A94A3` (Unknown/khác) | Phân biệt nhóm không có thứ tự (quận, hãng, hình thức thanh toán). Tối đa 6 nhóm có màu; nhóm còn lại gộp xám |

Quy tắc: một trang không dùng quá **một** bảng màu dữ liệu ngoài màu chính; không tô màu chỉ để trang trí.

## 3. Chữ (Segoe UI)

**Ngôn ngữ giao diện: tiếng Anh.** Mọi chữ hiển thị trên dashboard (tiêu đề, nhãn KPI, tiêu đề cột, header slicer, tên trang, chú thích) và nhãn dữ liệu của Dimension đều bằng tiếng Anh; tài liệu này vẫn viết bằng tiếng Việt. Định dạng số theo kiểu Mỹ (`85,745,246`, `$2.48bn`, `13.0%`): đặt **File > Options and settings > Options > CURRENT FILE > Regional settings > Locale for import = English (United States)**, rồi Refresh.

| Cấp | Cỡ | Độ đậm | Màu | Ví dụ |
|---|---:|---|---|---|
| Tiêu đề trang | 20 | Semibold | `#1F2933` | "NYC Yellow Taxi Overview" |
| Phụ đề trang | 10 | Regular | `#5F6B7A` | Câu hỏi trang trả lời |
| Số KPI | 28 | Semibold | `#1F2933` | 85.7M |
| Nhãn KPI | 10 | Regular | `#5F6B7A` | "Trips" |
| So sánh KPI | 9 | Semibold | tăng/giảm | ▲ 13.0% |
| Tiêu đề visual | 12 | Semibold | `#1F2933` | "Monthly Trips" |
| Nhãn trục, ô bảng | 9 | Regular | `#5F6B7A` / `#1F2933` | |
| Chú thích | 8 | Regular | `#8A94A3` | Định nghĩa, nguồn |

## 4. Lưới bố cục (mọi trang)

Canvas **1280 × 720** (16:9). Đặt vị trí, kích thước chính xác ở **Format > General > Properties > Size / Position**.

```text
x: 0        200 216                                                        1264 1280
   ┌──────────┬─────────────────────────────────────────────────────────────────┐ y 0
   │ THANH    │  Tiêu đề trang (20)                                              │ 16
   │ BỘ LỌC   │  Phụ đề (10)                                                     │ 44
   │ (200 px) ├─────────────────────────────────────────────────────────────────┤ 76
   │ tên báo  │  Hàng KPI (cao 96)                                               │
   │ cáo      ├─────────────────────────────────────────────────────────────────┤ 184
   │ slicer   │                                                                  │
   │ điều     │  Vùng dữ liệu chính (1048 × 520)                                 │
   │ hướng    │  quan trọng nhất đặt bên trái                                   │
   │ chú thích│                                                                  │
   └──────────┴─────────────────────────────────────────────────────────────────┘ 704 / 720
```

Tên trang (hiện trên Page navigator): `Overview`, `Revenue by Zone & Vendor`, `Payment Methods`, `Pickup & Dropoff Timing`, `Trip Profile`, `Routes & Map`, `Trends & Comparisons`.

Thanh bộ lọc giống nhau ở mọi trang (copy từ trang 1, đồng bộ slicer bằng **View > Sync slicers**):

| Thành phần | Visual | x | y | w | h | Ghi chú |
|---|---|---:|---:|---:|---:|---|
| Nền | Shape > Rectangle | 0 | 0 | 200 | 720 | Fill `#F3F5F8`, không viền |
| Tên báo cáo | Text box | 16 | 16 | 168 | 44 | "NYC Yellow Taxi" (14 Semibold) + dòng 2 "2024–2025" (10, `#5F6B7A`) |
| Năm | Slicer `DimMonth[year]` | 16 | 76 | 168 | 76 | Style **Tile**, header "Year" (10 Semibold); Multi-select with CTRL |
| Tháng | Slicer `DimMonth[yearmonth]` | 16 | 164 | 168 | 60 | Style **Dropdown**, header "Month" |
| Quận | Slicer `DimLocation[borough]` | 16 | 236 | 168 | 60 | Style **Dropdown**, header "Borough (pickup)" |
| Điều hướng | Insert > Buttons > Navigator > **Page navigator** | 16 | 320 | 168 | 224 | Orientation **Vertical**; chữ 10; trang hiện tại nền `#1F5AA6` chữ trắng, trang khác nền trong suốt chữ `#1F2933` |
| Chú thích | Text box | 16 | 600 | 168 | 104 | 8 pt `#8A94A3`: "Valid trips: dropoff after pickup, pickup in 2024–2025, non-negative fare, total and distance. Revenue = TotalAmount (USD). Source: NYC TLC Trip Records." |

---

## 5. Trang 1: Tổng quan (A1, A6, A8)

**Câu hỏi:** A1 số chuyến và hành khách theo ngày → tháng → năm; A6 hoạt động từng quận; A8 tổng doanh thu, roll-up theo thời gian và địa lý.

**Mục tiêu đọc trong 5 giây:** tổng quy mô (KPI) → xu hướng theo tháng (bên trái) → quận nào chiếm phần lớn (bên phải).

### 5.1 Bố cục

```text
0      200 216                     472 480        736 744        1000 1008       1264
┌───────┬──────────────────────────────────────────────────────────────────────────┐ 16
│ NYC   │ NYC Yellow Taxi Overview                                                 │
│ Yellow│ Volume, monthly trends and borough contribution · answers A1, A6, A8     │ 44
│ Taxi  ├─────────────┬──────────────┬──────────────┬──────────────────────────────┤ 76
│       │ Trips       │ Passengers   │ Revenue      │ Revenue per Trip             │
│ [Year]│ 85.7M       │ 94.9M        │ $2.48bn      │ $28.87                       │
│ [Mon.]│ ▲12.1% ...  │ 16.5% missing│ ▲13.0% ...   │ ▲0.8% ...                    │ 172
│ [Boro]├─────────────────────────────────────┬────────────────────────────────────┤ 184
│       │ Monthly Trips                  (L1) │ Activity by Borough (pickup)  (T1) │
│ Over- │ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ │ Borough  Trips   Revenue  ...      │
│ view ■├─────────────────────────────────────┤ Manh.    ██████  ██████            │ 352
│ Rev.  │ Monthly Passengers             (L2) │ Queens   █       ███               │
│ Paym. │ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ │ Brook.   ▏       ▏                 │
│ ...   ├─────────────────────────────────────┤ ...                                │ 524
│ notes │ Monthly Revenue (USD)          (L3) │                                    │
│       │ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ │ Total    ██████  ██████            │
│       │ Jan 2024  Apr  Jul  Oct  Jan 2025   │                                    │ 704
└───────┴─────────────────────────────────────┴────────────────────────────────────┘
        216                              816 832                               1264
```

| Thành phần | Visual | x | y | w | h |
|---|---|---:|---:|---:|---:|
| Tiêu đề | Text box | 216 | 16 | 1048 | 28 |
| Phụ đề | Text box | 216 | 44 | 1048 | 20 |
| K1 Số chuyến | Card (new) | 216 | 76 | 256 | 96 |
| K2 Hành khách | Card (new) | 480 | 76 | 256 | 96 |
| K3 Doanh thu | Card (new) | 744 | 76 | 256 | 96 |
| K4 Doanh thu / chuyến | Card (new) | 1008 | 76 | 256 | 96 |
| L1 Số chuyến mỗi tháng | Line chart | 216 | 184 | 600 | 168 |
| L2 Hành khách mỗi tháng | Line chart | 216 | 356 | 600 | 168 |
| L3 Doanh thu mỗi tháng | Line chart | 216 | 528 | 600 | 176 |
| T1 Hoạt động theo quận | Table | 832 | 184 | 432 | 520 |

### 5.2 Chuẩn bị (một lần)

1. **Cập nhật truy vấn `DimDate`**: dán lại nội dung mới của `powerbi/queries/DimDate.pq` vào Advanced Editor (thêm cột `monthstart`), Close & Apply.
2. **Sửa hierarchy `Calendar`** của DimDate thành `year` > `monthstart` > `fulldate` (bỏ `monthname`; chuột phải `monthstart` > Add to hierarchy, kéo lên giữa; chuột phải `monthname` trong hierarchy > Remove from hierarchy). Lý do: `monthstart` là kiểu ngày nên trục X liên tục, nhãn nằm ngang, không xoay chữ.
3. **Cập nhật measure**: dán lại toàn bộ `powerbi/dax/measures.dax` vào DAX query view > Run > Update model with changes. Có 3 measure mới (`Avg Revenue per Trip PY`, `Avg Revenue per Trip YoY %`, `Trips Without Passenger %`) và 2 measure sửa (`Revenue YoY %`, `Trips YoY %` chỉ hiện khi chọn đúng một năm). Sau đó định dạng:
   - `Trips YoY %`, `Revenue YoY %`, `Avg Revenue per Trip YoY %`: Format **Custom** `▲ 0.0%;▼ 0.0%;0.0%`.
   - `Trips Without Passenger %`: Percentage, 1 chữ số.
   - `Avg Revenue per Trip PY`: Currency, 2 chữ số.
4. **Nhập theme** (mục 2).

### 5.3 Cấu hình từng visual

**Tiêu đề, phụ đề.** Text box, chữ theo bảng mục 3. Tiêu đề: "NYC Yellow Taxi Overview". Phụ đề: "Volume, monthly trends and borough contribution · answers A1, A6, A8".

**K1–K4: Card (new).** Mỗi card một measure chính, một nhãn so sánh:

| Card | Data (giá trị) | Callout label | Reference label: giá trị | Reference label: tiêu đề | Màu reference |
|---|---|---|---|---|---|
| K1 | `Trips` | Trips | `Trips YoY %` | vs same period last year | fx: > 0 `#1F5AA6`; < 0 `#C65A00` |
| K2 | `Passengers` | Passengers | `Trips Without Passenger %` | of trips missing passenger count | `#5F6B7A` (cố định) |
| K3 | `Revenue` | Revenue | `Revenue YoY %` | vs same period last year | fx như K1 |
| K4 | `Avg Revenue per Trip` | Revenue per Trip | `Avg Revenue per Trip YoY %` | vs same period last year | fx như K1 |

Thiết lập chung cho 4 card:
- *Callout value*: 28 Semibold `#1F2933`, **Display units: Auto** (85.7M; $2.48bn; cần locale English (United States), xem mục 3). K4 Display units **None**, 2 chữ số.
- *Label*: vị trí **trên** giá trị, 10 `#5F6B7A`.
- *Reference labels*: **Add** > chọn measure, *Title* như bảng, chữ 9; *Layout* đặt dưới giá trị.
- Màu fx: Reference labels > Value > Color > **fx** > Format style *Rules*: "If value > 0 then `#1F5AA6`", "If value < 0 then `#C65A00`".
- *Visual border* On, màu `#E1E5EB`, rounded corners 4; *Background* `#FFFFFF`; *Title* Off (nhãn đã nói chỉ số là gì).

Khi không chọn hoặc chọn cả hai năm, nhãn so sánh để trống: YoY chỉ có nghĩa khi xét một năm (năm 2024 cũng trống vì không có 2023).

**K2 không có YoY:** tỷ lệ chuyến không ghi nhận số khách tăng từ 10,79% (2024) lên 21,67% (2025), nên tổng hành khách 2025 thấp hơn 2024 (−4,8%) trong khi số chuyến tăng 12,1%. So sánh hành khách giữa hai năm sẽ sai; card hiện tỷ lệ thiếu dữ liệu để người xem tự đánh giá (nguyên tắc 6).

**L1–L3: small multiples (Line chart × 3).** Ba chỉ số khác đơn vị và độ lớn; một biểu đồ hai trục Y gây hiểu lầm về độ dốc, nên tách ba panel chung trục thời gian (nguyên tắc 1).

| | L1 | L2 | L3 |
|---|---|---|---|
| X-axis | hierarchy `DimDate > Calendar` | như L1 | như L1 |
| Y-axis | `Trips` | `Passengers` | `Revenue` |
| Tiêu đề | Monthly Trips | Monthly Passengers · 11–22% of trips missing passenger count | Monthly Revenue (USD) |
| Nhãn trục X | **Off** | **Off** | On (9 pt) |

Thiết lập chung:
1. Sau khi kéo hierarchy vào X-axis, bấm **⇊ Go to the next level in the hierarchy** một lần để hiện mức `monthstart` (24 tháng). Người xem dùng ↓ / ↑ trên header visual để drill xuống ngày hoặc lên năm (A1).
2. *X-axis > Type*: **Continuous**; *Title* Off. Trục ngày liên tục tự giãn nhãn (Jan 2024, Apr 2024...), không xoay chữ.
3. *Y-axis*: *Title* Off; *Range minimum* để **Auto** (biểu đồ đường mã hóa bằng vị trí, không bắt buộc từ 0; xem Đánh đổi); *Display units* **Millions** (L3: **Millions**, tiền tệ).
4. *Lines*: màu `#1F5AA6`, độ dày 2 px, *Markers* Off. Không legend (mỗi panel một chuỗi; tên chỉ số nằm ở tiêu đề).
5. *Gridlines*: chỉ ngang, `#E6E9EE`; *Vertical gridlines* Off.
6. *Tooltips*: giữ mặc định (giá trị chính xác khi rê chuột).
7. Ba panel cùng x = 216, cùng w = 600 để trục thời gian thẳng hàng; chỉ L3 hiện nhãn trục X.

**T1: Highlight table (Table).** Bảng tra cứu chính xác kèm data bar (chiều dài) để so sánh nhanh (nguyên tắc 1, 4).

| Thứ tự | Field | Tiêu đề cột (Rename for this visual) | Định dạng |
|---:|---|---|---|
| 1 | `DimLocation[borough]` | Borough | Chữ; dòng Unknown, N/A màu `#8A94A3` (fx, xem dưới) |
| 2 | `Trips` | Trips | Display units Millions, 1 chữ số; **Data bars** |
| 3 | `Revenue` | Revenue | Currency, Millions, 1 chữ số; **Data bars** |
| 4 | `Passengers` | Passengers | Millions, 1 chữ số |
| 5 | `Avg Revenue per Trip` | Rev / Trip | Currency, 2 chữ số |
| 6 | `Revenue Share` | Rev Share | Percentage, 1 chữ số |

Thiết lập:
1. **Sắp xếp** theo `Revenue` giảm dần (bấm tiêu đề cột hoặc ... > Sort by).
2. **Data bars** (*Cell elements* > chọn series `Trips` > Data bars On > fx): Positive bar `#6FA3D8`, **Minimum: Number = 0** (mặc định Power BI lấy giá trị nhỏ nhất làm gốc, vi phạm nguyên tắc 3), Maximum: Highest value, *Show bar only* Off. Lặp lại cho `Revenue`.
3. **Chữ mờ cho dòng không phải quận**: *Cell elements* > series `Borough` > Font color > fx > Format style *Field value* > field `Borough Text Color` (measure trong `measures.dax`: Unknown, N/A → `#8A94A3`).
4. *Column headers*: 9 Semibold, nền `#F3F5F8`; *Values*: 9; *Grid*: Horizontal gridlines `#E6E9EE`, Vertical Off; *Totals* On (Semibold).
5. *Title*: "Activity by Borough (pickup) · sorted by revenue", 12 Semibold.
6. *Specific column* chỉnh độ rộng: Borough 92, Trips 88, Revenue 88, Passengers 72, Rev / Trip 48, Rev Share 44 (tổng ≈ 432).

### 5.4 Tương tác
- Bấm một dòng trong T1 → K1–K4 và L1–L3 lọc theo quận đó (mặc định *Filter*; kiểm tra ở **Format > Edit interactions**).
- L1–L3 không lọc lẫn nhau khi bấm điểm (Edit interactions: chọn L1, đặt L2, L3 là *None*; tương tự cho L2, L3), tránh trạng thái "một panel bị lọc, panel kia không".
- Slicer bên trái lọc mọi visual.

### 5.5 Đánh đổi (nguyên tắc 6)
| Quyết định | Được | Mất |
|---|---|---|
| 3 panel thay cho 1 biểu đồ nhiều chuỗi | Hình dạng từng chỉ số rõ, không cần hai trục Y | Không so trực tiếp độ lớn giữa chỉ số (khác đơn vị nên vốn không nên so) |
| Trục Y biểu đồ đường không bắt đầu từ 0 | Thấy rõ biến động mùa vụ (2,9–4,2 triệu chuyến/tháng) | Biến động trông lớn hơn tỷ lệ thật; bù lại bằng nhãn trục và lưới |
| Bảng có data bar thay cho biểu đồ thanh | Tra cứu số chính xác + so sánh bằng chiều dài trong một visual | Ít nổi bật hơn biểu đồ; Manhattan chiếm 74% nên các quận nhỏ gần như không có thanh |
| Hành khách không có YoY | Không đưa ra kết luận sai (−4,8%) | Người xem không có so sánh hành khách theo năm |
| Bộ lọc bên trái (người xem mới) | Dễ khám phá | Vùng dữ liệu hẹp hơn 216 px |
| Không dùng donut cho tỷ trọng | So sánh chính xác bằng số và thanh | Kém "bắt mắt" |

### 5.6 Đối chiếu số liệu

| Lựa chọn | Số chuyến | Hành khách | Doanh thu | DT/chuyến |
|---|---|---|---|---|
| Không lọc | 85.745.246 (so sánh trống) | 94.871.342 · 16,5% missing | 2.475.529.050,41 (trống) | 28,87 (trống) |
| Năm 2024 | 40.422.347 (trống) | 48.601.241 · 10,8% thiếu | 1.162.091.225,73 (trống) | 28,75 (trống) |
| Năm 2025 | 45.322.899 · ▲ 12,1% | 46.270.101 · 21,7% thiếu | 1.313.437.824,68 · ▲ 13,0% | 28,98 · ▲ 0,8% |

T1 (không lọc), sắp theo doanh thu:

| Quận | Số chuyến | Doanh thu (triệu USD) | Hành khách | DT/chuyến | Tỷ trọng |
|---|---:|---:|---:|---:|---:|
| Manhattan | 74.799.227 | 1.821,55 | 83.377.281 | 24,35 | 73,6% |
| Queens | 8.064.659 | 559,73 | 10.019.516 | 69,41 | 22,6% |
| Brooklyn | 2.141.981 | 66,30 | 892.677 | 30,95 | 2,7% |
| Bronx | 480.000 | 15,80 | 225.443 | 32,92 | 0,6% |
| Unknown | 198.918 | 6,13 | 269.088 | 30,82 | 0,2% |
| N/A | 43.084 | 4,56 | 64.206 | 105,92 | 0,2% |
| EWR | 11.654 | 1,18 | 20.727 | 101,36 | 0,05% |
| Staten Island | 5.723 | 0,27 | 2.404 | 47,35 | 0,01% |

Nhận xét để viết lên trang (tùy chọn, text box 9 pt dưới tiêu đề T1): "Queens: 9.4% of trips but 22.6% of revenue (JFK and LaGuardia airports; $69 per trip vs $24 in Manhattan)."

---

## 6. Trang 2: Revenue by Zone & Vendor (A2, 5b)

**Câu hỏi:** A2 doanh thu theo quận/khu vực đón × hãng xe × thời điểm; 5b doanh thu theo quận × tháng × khung giờ.

**Mục tiêu đọc trong 5 giây:** khu vực nào mang lại nhiều tiền nhất (trái) → hãng nào chiếm phần lớn, ở đâu (phải) → mỗi quận kiếm tiền vào giờ nào (dưới).

### 6.1 Bố cục

```text
0      200 216                     472 480        736 744        1000 1008       1264
┌───────┬──────────────────────────────────────────────────────────────────────────┐ 16
│ (thanh│ Revenue by Zone & Vendor                                                 │
│  bộ   │ Where revenue comes from, which vendor earns it, and when · A2, 5b       │ 44
│  lọc  ├─────────────┬──────────────┬──────────────┬──────────────────────────────┤ 76
│  như  │ Revenue     │ Top pickup   │ Leading      │ Peak pickup hour (revenue)   │
│ trang │ $2.48bn     │ JFK Airport  │ 78.6%        │ 17:00 - 18:00                │
│  1)   │ ▲13.0% ...  │ 12.7% of rev.│ VeriFone Inc.│ 7.1% of daily pickup revenue │ 172
│       ├─────────────────────────────────┬────────────────────────────────────────┤ 184
│       │ Top 10 Pickup Zones (V1)        │ Revenue by Borough > Zone (V2)         │
│       │ JFK Airport   ████████████▒▒    │ Borough  VeriFone      CMT            │
│       │ LaGuardia     ██████▒▒          │          Rev   Share   Rev   Share    │
│       │ Midtown Ctr   ███▒              │ + Manh.  ████  78.3%   ██    21.7%    │
│       │ ...           (■ VeriFone ■ CMT)│ + Queens ██    82.4%   ▏     17.5%    │ 484
│       ├─────────────────────────────────┴────────────────────────────────────────┤ 496
│       │ When each borough earns: share of daily pickup revenue by hour     (V3)  │
│       │          0   1   2   3 ...  16  17  18 ...  23                           │
│       │ Bronx    ░   ░   ░   ░      ▒   ▒   ▒       ░                            │
│       │ Manhattan░   ░   ░   ░      ▓   █   █       ▒                            │
│       │ Queens   ▒   ░   ░   ░      █   ▓   ▓       ▓                            │ 704
└───────┴──────────────────────────────────────────────────────────────────────────┘
        216                          732 748                                   1264
```

| Thành phần | Visual | x | y | w | h |
|---|---|---:|---:|---:|---:|
| Thanh bộ lọc | copy từ trang 1 (mục 4) | 0 | 0 | 200 | 720 |
| Tiêu đề / phụ đề | Text box | 216 | 16 / 44 | 1048 | 28 / 20 |
| K1 Revenue | Card (copy K3 trang 1) | 216 | 76 | 256 | 96 |
| K2 Top pickup zone | Card | 480 | 76 | 256 | 96 |
| K3 Leading vendor | Card | 744 | 76 | 256 | 96 |
| K4 Peak pickup hour | Card | 1008 | 76 | 256 | 96 |
| V1 Top 10 khu vực | Stacked bar chart | 216 | 184 | 516 | 300 |
| V2 Quận > khu vực × hãng | Matrix | 748 | 184 | 516 | 300 |
| V3 Heatmap quận × giờ | Matrix (highlight table) | 216 | 496 | 1048 | 208 |

### 6.2 Chuẩn bị

1. Dán lại `powerbi/dax/measures.dax` (thêm 9 measure của trang 2: `Vendor Revenue Share`, `Top Zone`, `Top Zone Revenue Share`, `Leading Vendor`, `Leading Vendor Share`, `Pickup Revenue (Borough)`, `Pickup Revenue Hour Share`, `Peak Revenue Hour`, `Peak Hour Revenue Share`) > Run > Update model with changes.
2. Định dạng: các measure `Share` Percentage 1 chữ số; `Pickup Revenue (Borough)` Currency.
3. Trang 1: chuột phải tab trang > **Duplicate page**, đổi tên `Revenue by Zone & Vendor`, xóa mọi visual trừ thanh bộ lọc, tiêu đề, phụ đề, card K3 (Revenue). Slicer giữ đồng bộ.

**Vì sao cần `Pickup Revenue (Borough)`:** `HourlyActivity` có cột `borough` riêng, không có quan hệ với `DimLocation` (mục 2.2 của powerbi.md), nên slicer *Borough (pickup)* không lọc được V3 và K4. Measure dùng `TREATAS` để chuyển lựa chọn quận sang `HourlyActivity[borough]`. Slicer Year/Month vẫn lọc bình thường qua `DimDate`.

### 6.3 Cấu hình từng visual

**Tiêu đề:** "Revenue by Zone & Vendor". Phụ đề: "Where revenue comes from, which vendor earns it, and when · answers A2, 5b".

**K1–K4 (Card new):** thiết lập chung như trang 1 (mục 5.3). Callout là chữ (tên khu vực, khung giờ) thì đặt cỡ **20** để tên dài không bị cắt.

| Card | Callout (Data) | Label | Reference label: giá trị | Reference label: tiêu đề | Màu reference |
|---|---|---|---|---|---|
| K1 | `Revenue` | Revenue | `Revenue YoY %` | vs same period last year | fx như trang 1 |
| K2 | `Top Zone` (20 pt) | Top pickup zone | `Top Zone Revenue Share` | of revenue | `#5F6B7A` |
| K3 | `Leading Vendor Share` (28 pt) | Leading vendor share | `Leading Vendor` | (để trống) | `#5F6B7A` |
| K4 | `Peak Revenue Hour` (20 pt) | Peak pickup hour (revenue) | `Peak Hour Revenue Share` | of daily pickup revenue | `#5F6B7A` |

**V1: Top 10 khu vực đón theo doanh thu (Stacked bar chart).** Thanh ngang vì tên khu vực dài (nguyên tắc 5: không xoay chữ).

| Ô | Field |
|---|---|
| Y-axis | `DimLocation[zone]` |
| X-axis | `Revenue` |
| Legend | `DimVendor[vendorname]` |
| Tooltips | `DimLocation[borough]`, `Avg Revenue per Trip` |

1. *Filters on this visual*: `zone` > Filter type **Top N** > Show items **Top 10** > By value `Revenue` > Apply. `vendorname` > Basic filtering, bỏ chọn **Unknown** (0,03% doanh thu).
2. Sắp xếp: ... > Sort axis > `Revenue` > Sort descending.
3. Màu (*Bars > Colors*): VeriFone Inc. `#1F5AA6`, Creative Mobile Technologies `#E69F00` (xanh–cam, an toàn mù màu).
4. *X-axis*: Title Off, Display units Millions, bắt đầu 0 (mặc định, không đổi). *Y-axis*: Title Off, 9 pt.
5. *Gridlines*: dọc `#E6E9EE`. *Data labels* Off; **Total labels** On (Millions, 1 chữ số, 9 pt).
6. *Legend*: Top, Left, không tiêu đề.
7. *Title*: "Top 10 Pickup Zones by Revenue (USD)"; *Subtitle*: "Split by vendor · Unknown vendor hidden (0.03% of revenue)", 9 `#5F6B7A`.

**V2: Doanh thu quận > khu vực × hãng (Matrix).**

| Ô | Field |
|---|---|
| Rows | `DimLocation[borough]`, `DimLocation[zone]` |
| Columns | `DimVendor[vendorname]` |
| Values | `Revenue` (đổi tên "Revenue"), `Vendor Revenue Share` (đổi tên "Share") |

1. *Filters on this visual*: `vendorname` bỏ chọn Unknown.
2. *Row headers*: **+/- icons** On; mặc định thu gọn ở mức quận, người xem bấm + để xem khu vực.
3. *Subtotals*: **Row subtotals** On (dòng tổng cuối bảng); **Column subtotals** Off (cột Total của "Share" luôn 100%, vô nghĩa).
4. *Cell elements* > `Revenue` > **Data bars** > fx: `#6FA3D8`, **Minimum: Number 0**, Maximum: Highest value.
5. `Revenue`: Currency, Millions, 1 chữ số. `Share`: 1 chữ số.
6. Sắp xếp theo `Revenue` giảm dần.
7. *Title*: "Revenue by Borough > Zone and Vendor"; *Subtitle*: "Share = vendor's share of the row's revenue".

**V3: Heatmap doanh thu theo giờ (Matrix, highlight table).** Doanh thu Manhattan (1.822 triệu) gấp 3 lần Queens và 27 lần Brooklyn: biểu đồ vùng/đường chung trục sẽ làm phẳng mọi quận trừ Manhattan. Heatmap tô theo **tỷ trọng trong ngày của từng quận** (mỗi dòng cộng = 100%) nên so được hình dạng nhịp giờ giữa các quận.

| Ô | Field |
|---|---|
| Rows | `HourlyActivity[borough]` |
| Columns | `HourlyActivity[hour]` |
| Values | `Pickup Revenue Hour Share` |

1. *Filters on this visual*: `HourlyActivity[borough]` chỉ chọn **Bronx, Brooklyn, Manhattan, Queens** (99,5% doanh thu). EWR, Staten Island, Unknown, N/A quá ít chuyến, phân bố theo giờ nhiễu.
2. *Subtotals*: Row và Column subtotals **Off**.
3. *Cell elements* > **Background color** On > fx > *Format style* **Gradient** > Minimum: Lowest value `#EAF1FA`; bật *Add a middle color*: Center `#6FA3D8`; Maximum: Highest value `#123B70` (bảng màu tuần tự).
4. *Cell elements* > **Font color** > fx > Rules: value >= 0.055 → `#FFFFFF`; value < 0.055 → `#1F2933` (chữ đủ tương phản trên nền đậm).
5. Giá trị: Percentage, 1 chữ số, 8 pt; *Values* căn giữa.
6. *Column headers*: 9 pt; *Specific column*/*Auto-size width* Off: cột borough 96 px, mỗi cột giờ ~38 px.
7. *Grid*: Off cả ngang và dọc, *Padding* 2 (các ô liền nhau như heatmap).
8. *Title*: "When each borough earns: share of daily pickup revenue by hour (0–23)"; *Subtitle*: "Each row sums to 100% · EWR, Staten Island, Unknown and N/A hidden (0.5% of revenue)".

### 6.4 Tương tác

- V1, V2 → **V3, K4: None** (V3, K4 đọc `HourlyActivity`, chỉ biết quận; bấm một khu vực sẽ hiện nhịp giờ của *cả quận*, gây hiểu nhầm).
- V1 ↔ V2: Filter (bấm một khu vực ở V1, V2 lọc theo khu vực đó; bấm một hãng trong legend V1, V2 lọc theo hãng).
- V1, V2 → K1–K3: Filter.
- V3 không lọc visual khác (HourlyActivity không nối với TripsDaily).

### 6.5 Đánh đổi

| Quyết định | Được | Mất |
|---|---|---|
| Thanh chồng theo hãng (V1) | Một visual trả lời cả "khu vực nào" và "hãng nào" | Đoạn của CMT không cùng gốc nên khó so chính xác giữa khu vực; bù bằng cột Share ở V2 |
| Top 10 thay cho mọi khu vực | Đọc nhanh, nhãn không chồng | Không thấy đuôi dài 250 khu vực; xem đầy đủ ở V2 |
| Heatmap tỷ trọng trong ngày thay cho doanh thu tuyệt đối | So được nhịp giờ của quận nhỏ với Manhattan | Mất độ lớn tuyệt đối theo giờ (có ở tooltip và K4); màu kém chính xác hơn chiều dài, nên hiện số trong ô |
| Ẩn EWR, Staten Island, Unknown, N/A ở V3 | Không bị nhiễu do mẫu nhỏ (EWR 11.654 chuyến) | Mất 0,5% doanh thu; ghi ở subtitle |
| Ẩn vendor Unknown ở V1, V2 | Legend gọn, hai màu | 0,81 triệu USD; ghi ở subtitle |
| Bỏ slicer `timeslot` của phác thảo ban đầu | V3 đã hiện đủ 24 giờ; ít bộ lọc hơn | Không lọc V1/V2 theo giờ (TripsDaily không có giờ) |

### 6.6 Đối chiếu số liệu

| Lựa chọn | K1 Revenue | K2 Top zone | K3 Leading vendor | K4 Peak hour |
|---|---|---|---|---|
| Không lọc | $2.48bn (trống) | JFK Airport · 12.7% | 78.6% · VeriFone Inc. | 17:00 - 18:00 · 7.1% |
| Năm 2024 | $1.16bn (trống) | JFK Airport · 13.5% | 77.4% · VeriFone Inc. | 17:00 - 18:00 · 7.1% |
| Năm 2025 | $1.31bn · ▲ 13.0% | JFK Airport · 11.9% | 79.7% · VeriFone Inc. | 17:00 - 18:00 · 7.1% |
| Borough = Queens | $559.7M | JFK Airport · 56.0% | 82.4% · VeriFone Inc. | 16:00 - 17:00 · 7.8% |

V1 (không lọc, triệu USD, tổng · VeriFone · CMT): JFK Airport 313,2 · 268,9 · 44,3; LaGuardia Airport 174,4 · 139,5 · 34,9; Midtown Center 99,7 · 78,6 · 21,1; Upper East Side South 82,7; Times Sq/Theatre District 81,2; Upper East Side North 74,5; Penn Station/Madison Sq West 72,4; Midtown East 70,7; East Chelsea 59,9; Midtown North 59,7.

V2 (mức quận, Share VeriFone / CMT): Manhattan 78,3% / 21,7%; Queens 82,4% / 17,5%; Brooklyn 64,0% / 35,7%; **Bronx 44,3% / 55,2%** (quận duy nhất CMT dẫn).

V3 (giờ cao nhất mỗi dòng): Manhattan 18h 7,5%; Queens 16h 7,8%; Brooklyn 8h 6,4%; Bronx 7h 9,7%. Thấp nhất: Manhattan 4h 0,7%; Queens 3h 0,3%.

Nhận xét để viết lên trang (tùy chọn): "Airports lead: JFK and LaGuardia earn 20% of revenue. Manhattan peaks at 6 pm, Queens at 4 pm (airport arrivals), Brooklyn and the Bronx in the morning commute."

---

## 7. Trang 3: Payment Methods (A3)

**Câu hỏi:** A3 tỷ lệ các hình thức thanh toán theo thời gian và khu vực.

**Mục tiêu đọc trong 5 giây:** thẻ chiếm phần lớn nhưng đang giảm (KPI) → giảm vì chuyến không ghi nhận hình thức thanh toán tăng nhanh (trái) → hiện tượng tập trung ở Brooklyn, Bronx (phải).

**Phát hiện chính (đo trên mart):** nhóm *Unknown* (mã 0) tăng từ 9,8% số chuyến (2024) lên 21,1% (2025), có tháng 28,5% (12/2025). Toàn bộ 13.525.377 chuyến mã 0 cũng thiếu số khách và mã giá (`RatecodeID`), tức là bản ghi không có metadata từ đồng hồ tính tiền. TLC đặt mã 0 cho chuyến *Flex Fare* (giá thỏa thuận trước qua ứng dụng). Đây cũng chính là nhóm làm thiếu số hành khách ở trang 1.

### 7.1 Bố cục

```text
0      200 216                     472 480        736 744        1000 1008       1264
┌───────┬──────────────────────────────────────────────────────────────────────────┐ 16
│ (thanh│ Payment Methods                                                          │
│  bộ   │ How riders pay, how it changes over time and by borough · answers A3     │ 44
│  lọc) ├─────────────┬──────────────┬──────────────┬──────────────────────────────┤ 76
│       │ Credit card │ Cash         │ Unknown      │ Card tip rate                │
│       │ 71.2%       │ 11.4%        │ 15.8%        │ 21.9%                        │
│       │ ▼ 7.8 pp ...│ ▼ 3.6 pp ... │ ▲ 11.3 pp ...│ of fare, card trips          │ 172
│       ├─────────────────────────────────────────┬────────────────────────────────┤ 184
│       │ Monthly share of trips by payment  (V1) │ Payment mix by borough    (V2) │
│       │ 80% ─── Credit card ──╲___╱‾‾╲_         │ Manhattan ████████▒▒░░░░       │
│       │ 20%          Unknown ___╱‾‾╲_╱‾         │ Queens    ███████▒▒▒░░░        │
│       │ 10% ─── Cash ─────────────────          │ Brooklyn  ███░░░░░░░░░░        │
│       │ Jan 2024    Jul     Jan 2025   Jul      │ Bronx     ████░░░░░░░░░        │ 484
│       ├─────────────────────────────────────────┴────────────────────────────────┤ 496
│       │ Payment type summary (V3)                                                │
│       │ Payment type  Trips ████   Share  Revenue ████  Rev / Trip  Tip / Trip   │
│       │ Credit card   61.0M        71.2%  $1,837.5M     $30.10      $4.35        │ 704
└───────┴──────────────────────────────────────────────────────────────────────────┘
        216                                  856 872                           1264
```

| Thành phần | Visual | x | y | w | h |
|---|---|---:|---:|---:|---:|
| Tiêu đề / phụ đề | Text box | 216 | 16 / 44 | 1048 | 28 / 20 |
| K1–K4 | Card (new) | 216 / 480 / 744 / 1008 | 76 | 256 | 96 |
| V1 Tỷ trọng theo tháng | Line chart | 216 | 184 | 640 | 300 |
| V2 Cơ cấu theo quận | 100% stacked bar chart | 872 | 184 | 392 | 300 |
| V3 Bảng tổng hợp | Table | 216 | 496 | 1048 | 208 |

### 7.2 Chuẩn bị

1. **Truy vấn `DimPaymentType`:** dán lại `powerbi/queries/DimPaymentType.pq` (thêm cột `paymentorder`) > Close & Apply.
2. **Sort by column:** chọn `DimPaymentType[paymenttypename]` > Column tools > Sort by column > `paymentorder`. Legend và thanh chồng sẽ theo thứ tự Credit card → Cash → Dispute → No charge → Unknown, nên Unknown luôn nằm ở mép phải (cùng gốc 100%) và dễ so giữa các quận. Ẩn cột `paymentorder`.
3. **Measure:** dán lại `measures.dax` (thêm 8 measure, tổng 76) > Run > Update model with changes. Định dạng:
   - `Payment Trip Share`, `Card Trip Share`, `Cash Trip Share`, `Unknown Payment Share`: Percentage, 1 chữ số.
   - `Card Share Change (pp)`, `Cash Share Change (pp)`, `Unknown Payment Share Change (pp)`, `Tip Rate Change (pp)`: Custom `▲ 0.0 "pp";▼ 0.0 "pp";0.0 "pp"`.
4. **Trang:** Duplicate trang 2, đổi tên `Payment Methods`, xóa mọi visual trừ thanh bộ lọc, tiêu đề, phụ đề, một card.

### 7.3 Cấu hình từng visual

**Tiêu đề:** "Payment Methods". Phụ đề: "How riders pay, how it changes over time and by borough · answers A3".

**K1–K4 (Card new):** đơn vị so sánh là **điểm phần trăm (pp)**, không phải %: tỷ trọng thẻ từ 75,3% xuống 67,5% là −7,8 pp (nếu ghi −10,4% người xem dễ đọc nhầm thành tỷ trọng giảm 10 điểm).

| Card | Callout (Data) | Label | Reference label: giá trị | Reference label: tiêu đề | Màu reference |
|---|---|---|---|---|---|
| K1 | `Card Trip Share` | Credit card | `Card Share Change (pp)` | vs same period last year | `#5F6B7A` |
| K2 | `Cash Trip Share` | Cash | `Cash Share Change (pp)` | vs same period last year | `#5F6B7A` |
| K3 | `Unknown Payment Share` | Unknown payment type | `Unknown Payment Share Change (pp)` | vs same period last year | `#5F6B7A` |
| K4 | `Avg Tip Rate` | Card tip rate | `Tip Rate Change (pp)` | vs same period last year | `#5F6B7A` |

Màu reference **trung tính** (khác trang 1, 2): tỷ trọng thẻ giảm hay tiền mặt giảm không phải tốt hay xấu, tô xanh/cam sẽ gán ý nghĩa không có thật (nguyên tắc 2: màu phải có mục đích). Mũi tên ▲▼ vẫn cho biết chiều.

Callout 28 Semibold, *Display units* None, 1 chữ số. Thêm vào K4 tooltip (*Tooltips* > `Tip per Trip`) và ghi chú trong subtitle V3: tỷ lệ boa chỉ tính trên chuyến thẻ (tiền boa tiền mặt không được ghi nhận).

**V1: Tỷ trọng số chuyến theo tháng (Line chart).**

| Ô | Field |
|---|---|
| X-axis | hierarchy `DimDate > Calendar` (bấm ⇊ một lần, mức `monthstart`) |
| Y-axis | `Payment Trip Share` |
| Legend | `DimPaymentType[paymenttypename]` |

1. *Filters on this visual*: `paymenttypename` chỉ chọn **Credit card, Cash, Unknown** (Dispute + No charge cộng lại 1,2–2,3% mỗi tháng, xem ở V2, V3; năm đường gần 0 làm rối trục).
2. Màu: Credit card `#1F5AA6`, Cash `#E69F00`, Unknown `#8A94A3` (xám = thiếu dữ liệu, đúng ngữ nghĩa); đường 2 px, không marker.
3. *X-axis*: Continuous, Title Off. *Y-axis*: Title Off, **Minimum 0** (tỷ trọng: 0 là gốc có ý nghĩa, giữ tỷ lệ thật giữa các đường), Maximum Auto; định dạng 0%.
4. *Gridlines*: ngang `#E6E9EE`. *Legend*: Top, Left.
5. *Title*: "Monthly share of trips by payment type"; *Subtitle*: "Unknown = no payment type recorded (code 0, also missing passenger count and rate code)".

**V2: Cơ cấu thanh toán theo quận (100% stacked bar chart).**

| Ô | Field |
|---|---|
| Y-axis | `DimLocation[borough]` |
| X-axis | `Trips` |
| Legend | `DimPaymentType[paymenttypename]` |
| Tooltips | `Payment Trip Share` |

1. *Filters on this visual*: `borough` chỉ chọn Manhattan, Queens, Brooklyn, Bronx (99,7% số chuyến).
2. Sắp xếp: ... > Sort axis > `Trips` giảm dần (Manhattan trên cùng).
3. Màu (thứ tự stack nhờ `paymentorder`): Credit card `#1F5AA6`, Cash `#E69F00`, Dispute `#56B4E9`, No charge `#009E73`, Unknown `#8A94A3`.
4. *Data labels* On chỉ cho series Credit card và Unknown (*Data labels > Apply settings to* từng series; tắt các series còn lại), 0%, chữ trắng. Hai đoạn này cùng gốc (0% và 100%) nên so được bằng chiều dài.
5. *X-axis*: Off (đã có nhãn %); *Y-axis*: Title Off. *Legend*: Top, Left.
6. *Title*: "Payment mix by borough (pickup)"; *Subtitle*: "Share of trips · Staten Island, EWR, Unknown, N/A hidden (0.3% of trips)".

**V3: Bảng tổng hợp theo hình thức (Table).**

| Thứ tự | Field | Tiêu đề cột | Định dạng |
|---:|---|---|---|
| 1 | `DimPaymentType[paymenttypename]` | Payment type | |
| 2 | `Trips` | Trips | Millions, 1 chữ số; **Data bars** min 0, `#6FA3D8` |
| 3 | `Payment Trip Share` | Trip Share | 1 chữ số |
| 4 | `Revenue` | Revenue | Currency, Millions, 1 chữ số; **Data bars** min 0 |
| 5 | `Avg Revenue per Trip` | Rev / Trip | Currency, 2 chữ số |
| 6 | `Tip per Trip` | Tip / Trip | Currency, 2 chữ số |

Sắp theo `Trips` giảm dần; *Totals* On; header nền `#F3F5F8`. *Title*: "Payment type summary"; *Subtitle*: "Cash tips are not recorded by the meter, so Tip / Trip for cash is $0".

### 7.4 Tương tác

- V2 → V1: Filter (bấm Brooklyn, V1 hiện tỷ trọng theo tháng của Brooklyn). V2 → V3: Filter.
- V3 → K1–K4: **None** (bấm "Cash" ở V3 sẽ lọc `Avg Tip Rate` của K4 về trống). K1–K3 vốn cố định hình thức nên không đổi.
- V1 → V2, V3: Filter theo tháng khi bấm một điểm (mặc định).

### 7.5 Đánh đổi

| Quyết định | Được | Mất |
|---|---|---|
| Đường tỷ trọng (V1) thay cho cột chồng 100% theo tháng (phác thảo ban đầu) | Ba đường cùng gốc 0, so được độ dốc từng hình thức (nguyên tắc 1: vị trí) | Không thấy tổng 100% trực tiếp; Dispute/No charge chuyển sang V2, V3 |
| Cột chồng 100% chỉ dùng ở V2 (4 quận) | So nhanh cơ cấu giữa quận; Credit card và Unknown cùng gốc | Đoạn giữa (Cash, Dispute) khó so chính xác; bù bằng tooltip |
| Card hiện thay đổi bằng pp, màu trung tính | Đúng đơn vị, không gán tốt/xấu | Kém "nổi bật" hơn xanh/cam |
| Giữ Unknown, không ẩn | Trung thực: 15,8% số chuyến, xu hướng tăng là phát hiện chính | Trang "kém đẹp" vì một nhóm xám lớn |

### 7.6 Đối chiếu số liệu

| Lựa chọn | K1 Credit card | K2 Cash | K3 Unknown | K4 Card tip rate |
|---|---|---|---|---|
| Không lọc | 71.2% (trống) | 11.4% (trống) | 15.8% (trống) | 21.9% (trống) |
| Năm 2024 | 75.3% (trống) | 13.3% (trống) | 9.8% (trống) | 21.9% (trống) |
| Năm 2025 | 67.5% · ▼ 7.8 pp | 9.7% · ▼ 3.6 pp | 21.1% · ▲ 11.3 pp | 21.8% · ▼ 0.1 pp |

V1 (Credit card / Cash / Unknown): 01/2024 79,2% / 14,7% / 4,7%; 06/2025 63,8% / 9,0% / 25,4%; 12/2025 61,2% / 9,1% / 28,5%.

V2 (Credit card / Cash / Unknown): Manhattan 72,5% / 11,2% / 14,8%; Queens 70,5% / 15,5% / 10,3%; **Brooklyn 32,9% / 2,9% / 63,5%**; **Bronx 40,8% / 3,1% / 55,3%**.

V3: Credit card 61.037.820 chuyến, 71,2%, 1.837,45 triệu USD, 30,10 USD/chuyến, boa 4,35 USD/chuyến; Unknown 13.525.379, 15,8%, 352,76 triệu, 26,08, 0,51; Cash 9.776.108, 11,4%, 245,46 triệu, 25,11, 0,00; Dispute 1.002.962, 1,2%; No charge 402.977, 0,5%.

Nhận xét để viết lên trang (tùy chọn): "Trips with no payment type recorded doubled in 2025 (9.8% → 21.1%) and dominate Brooklyn and the Bronx (55–64%). The card share drop is mostly this shift, not riders switching to cash."

---

## 8. Trang 4: Pickup & Dropoff Timing (A4)

**Câu hỏi:** A4 thời điểm đón và trả khách: giờ nào, ngày nào cao điểm; luồng đón/trả lệch nhau ở đâu.

**Mục tiêu đọc trong 5 giây:** cao điểm 18h, thứ Năm (KPI) → nhịp đón/trả trong ngày (trái) → quận nào là nơi đi, nơi đến theo giờ (phải) → nhịp theo ngày trong tuần (dưới).

**Đơn vị chung của trang: trung bình mỗi ngày** (`Avg Daily Pickups` = lượt đón / số ngày trong kỳ). Lý do: số ngày thứ Hai..Chủ nhật trong kỳ khác nhau (104–105), năm 2024 có 366 ngày; so tổng sẽ thiên lệch.

### 8.1 Bố cục

```text
0      200 216                     472 480        736 744        1000 1008       1264
┌───────┬──────────────────────────────────────────────────────────────────────────┐ 16
│ (thanh│ Pickup & Dropoff Timing                                                  │
│  bộ   │ When trips start and end, by hour and day of week · answers A4           │ 44
│  lọc) ├─────────────┬──────────────┬──────────────┬──────────────────────────────┤ 76
│       │ Peak pickup │ Peak dropoff │ Busiest day  │ Avg pickups per day          │
│       │ 18:00-19:00 │ 18:00-19:00  │ Thursday     │ 117,299                      │
│       │ 7.1% of ... │ 7.4% of ...  │ 127,686 /day │ ▲12.4% ...                   │ 172
│       ├─────────────────────────────────────────┬────────────────────────────────┤ 184
│       │ Avg pickups & dropoffs per day, by hour │ Net pickups by hour (V2)       │
│       │ (V1)        ╱‾‾‾╲                       │ Manhattan ▂▅▇▅ ▁  ▁▃▅▇         │
│       │       ___╱‾‾     ╲__  — Pickups         │ Queens      ▁▃▅▇▇▇▇▇▇▇         │
│       │ ‾‾╲__╱              — Dropoffs          │ Brooklyn  ▃▂▁ ▁ ▂▃▅▆▇▇         │
│       │ 0    4    8   12   16   20   23         │ 0     6    12    18    23      │ 484
│       ├─────────────────────────────────────────┴────────────────────────────────┤ 496
│       │ Avg pickups per day by day of week and hour (V3)                         │
│       │ Monday    ░ ░ ░ ░ ░ ░ ▒ ▓ ▓ ▓ ▓ ▓ ▓ ▓ ▓ ▓ ▓ █ █ ▓ ▓ ▓ ▒ ░                │
│       │ ...                                                                      │
│       │ Sunday    ▓ ▒ ▒ ░ ░ ░ ░ ░ ▒ ▒ ▓ ▓ ▓ ▓ ▓ ▓ ▓ ▓ ▓ ▓ ▒ ▒ ▒ ░                │ 704
└───────┴──────────────────────────────────────────────────────────────────────────┘
        216                                  856 872                           1264
```

| Thành phần | Visual | x | y | w | h |
|---|---|---:|---:|---:|---:|
| Tiêu đề / phụ đề | Text box | 216 | 16 / 44 | 1048 | 28 / 20 |
| K1–K4 | Card (new) | 216 / 480 / 744 / 1008 | 76 | 256 | 96 |
| V1 Đón/trả theo giờ | Line chart | 216 | 184 | 640 | 300 |
| V2 Chênh lệch đón − trả theo quận | Clustered column chart, small multiples | 872 | 184 | 392 | 300 |
| V3 Heatmap ngày × giờ | Matrix (highlight table) | 216 | 496 | 1048 | 208 |

### 8.2 Chuẩn bị

1. Dán lại `measures.dax` (thêm 14 measure, tổng 90) > Run > Update model with changes. Định dạng:
   - `Avg Daily Pickups`, `Avg Daily Dropoffs`, `Avg Daily Net Pickups`, `Busiest Day Avg Pickups`, `Avg Daily Pickups PY`: Whole number, có dấu phân cách.
   - `Peak Pickup Hour Share`, `Peak Dropoff Hour Share`: Percentage, 1 chữ số.
   - `Avg Daily Pickups YoY %`: Custom `▲ 0.0%;▼ 0.0%;0.0%`.
2. Kiểm tra `DimDate[dayname]` đã **Sort by column** `dayofweek` (powerbi.md mục 2.3; 1 = Monday … 7 = Sunday).
3. Duplicate trang 3, đổi tên `Pickup & Dropoff Timing`, xóa visual trừ thanh bộ lọc, tiêu đề, phụ đề, một card.

**Slicer quận trên trang này:** `Pickups (Borough)` / `Dropoffs (Borough)` áp lựa chọn quận vào cả hai vai trò: chọn Queens = lượt đón **tại** Queens và lượt trả **tại** Queens. Ghi rõ ở phụ đề V1.

### 8.3 Cấu hình từng visual

**Tiêu đề:** "Pickup & Dropoff Timing". Phụ đề: "When trips start and end, by hour and day of week · answers A4".

**K1–K4 (Card new):**

| Card | Callout (Data) | Cỡ | Label | Reference label: giá trị | Tiêu đề reference | Màu reference |
|---|---|---|---|---|---|---|
| K1 | `Peak Pickup Hour` | 20 | Peak pickup hour | `Peak Pickup Hour Share` | of pickups | `#5F6B7A` |
| K2 | `Peak Dropoff Hour` | 20 | Peak dropoff hour | `Peak Dropoff Hour Share` | of dropoffs | `#5F6B7A` |
| K3 | `Busiest Pickup Day` | 20 | Busiest day (pickups) | `Busiest Day Avg Pickups` | pickups per day | `#5F6B7A` |
| K4 | `Avg Daily Pickups` | 28 | Avg pickups per day | `Avg Daily Pickups YoY %` | vs same period last year | fx xanh/cam như trang 1 |

K4 dùng màu tăng/giảm vì lượng chuyến tăng là kết quả kinh doanh tốt (như trang 1); K1–K3 là thông tin mô tả, màu trung tính.

**V1: Trung bình lượt đón và trả mỗi ngày theo giờ (Line chart).**

| Ô | Field |
|---|---|
| X-axis | `HourlyActivity[hour]` |
| Y-axis | `Avg Daily Pickups`, `Avg Daily Dropoffs` |

1. *X-axis*: Type **Continuous** (0–23), Title Off, 9 pt.
2. *Y-axis*: Title Off, **Minimum 0** (đếm chuyến; 4h sáng gần chạm đáy, giữ 0 để thấy biên độ thật), Display units Thousands.
3. Màu: Avg Daily Pickups `#1F5AA6`, Avg Daily Dropoffs `#E69F00`, 2 px, không marker. Đổi tên series (Rename for this visual): "Pickups", "Dropoffs".
4. *Legend*: Top, Left. *Gridlines*: ngang `#E6E9EE`.
5. *Title*: "Average pickups and dropoffs per day, by hour"; *Subtitle*: "Borough filter applies to both: pickups in and dropoffs in the selected borough".

**V2: Chênh lệch đón − trả theo giờ, theo quận (Clustered column chart, small multiples).** Ba quận có độ lớn chênh lệch tương đương (±200–490 chuyến/ngày) nên **dùng chung trục Y** được.

| Ô | Field |
|---|---|
| X-axis | `HourlyActivity[hour]` |
| Y-axis | `Avg Daily Net Pickups` (đổi tên "Net pickups per day") |
| Small multiples | `HourlyActivity[borough]` |

1. *Filters on this visual*: `HourlyActivity[borough]` chỉ chọn Manhattan, Queens, Brooklyn.
2. *Small multiples > Layout*: Rows **3**, Columns **1**; *Title* (tên quận) 9 Semibold, căn trái.
3. *Columns > Color* > **fx** > Rules: value > 0 → `#1F5AA6` (đi nhiều hơn đến); value < 0 → `#C65A00` (đến nhiều hơn đi). Bảng màu phân kỳ có gốc 0.
4. *X-axis*: Type Categorical, nhãn chỉ ở panel dưới cùng (mặc định), 8 pt; Title Off. *Y-axis*: Title Off, 8 pt.
5. *Gridlines*: ngang `#E6E9EE`; giá trị 0 là đường gốc.
6. *Title*: "Net pickups per day by hour"; *Subtitle*: "Blue: more trips start than end · Orange: more trips end than start".

**V3: Heatmap trung bình lượt đón mỗi ngày theo thứ × giờ (Matrix).**

| Ô | Field |
|---|---|
| Rows | `DimDate[dayname]` |
| Columns | `HourlyActivity[hour]` |
| Values | `Avg Daily Pickups` |

1. Row/Column subtotals Off; Grid Off; Padding 2.
2. *Cell elements > Background color* > fx > Gradient: Lowest `#EAF1FA`, Center `#6FA3D8`, Highest `#123B70`.
3. *Font color* > fx > Rules: value >= 6000 → `#FFFFFF`; < 6000 → `#1F2933`.
4. Giá trị: Display units **Thousands**, 1 chữ số (9.6K), 8 pt, căn giữa. Cột dayname 96 px, cột giờ ~38 px.
5. *Title*: "Average pickups per day, by day of week and hour"; *Subtitle*: "Darker = busier · values in thousands".

### 8.4 Tương tác

- V3 → V1: Filter (bấm tên một ngày, V1 hiện nhịp giờ của ngày đó: thứ Bảy, CN có đỉnh nửa đêm).
- V3 → V2: Filter. V1 → V3: **None** (bấm một giờ ở V1 sẽ làm heatmap chỉ còn một cột).
- V2 → V1, V3: **None** (V2 cố định 3 quận; bấm một cột sẽ lọc theo quận + giờ, dễ nhầm với slicer).

### 8.5 Đánh đổi

| Quyết định | Được | Mất |
|---|---|---|
| Trung bình mỗi ngày thay cho tổng | So được giữa thứ trong tuần, giữa năm 366 và 365 ngày | Con số không cộng được thành tổng kỳ (tổng có ở trang 1) |
| Hai đường (V1) thay cho cột cụm 24 × 2 (phác thảo ban đầu) | Thấy rõ đường trả trễ hơn đường đón; ít mực hơn 48 cột | Khó đọc chính xác từng giờ (bù bằng tooltip) |
| V2 small multiples chung trục | So trực tiếp độ lớn đi/đến giữa 3 quận | Bronx, Staten Island, EWR không hiện (chênh lệch nhỏ hoặc mẫu nhỏ) |
| Heatmap thay cho 7 đường | 168 ô đọc trong một khung, thấy ngay khối "giờ làm việc" và "đêm cuối tuần" | Màu kém chính xác hơn vị trí; hiện số trong ô để bù |

### 8.6 Đối chiếu số liệu

| Lựa chọn | K1 Peak pickup | K2 Peak dropoff | K3 Busiest day | K4 Avg pickups/day |
|---|---|---|---|---|
| Không lọc | 18:00 - 19:00 · 7.1% | 18:00 - 19:00 · 7.4% | Thursday · 127,686 | 117,299 (trống) |
| Năm 2024 | 18:00 - 19:00 · 7.2% | 18:00 - 19:00 · 7.4% | Thursday · 121,542 | 110,444 (trống) |
| Năm 2025 | 18:00 - 19:00 · 7.1% | 18:00 - 19:00 · 7.3% | Thursday · 133,830 | 124,172 · ▲ 12.4% |
| Borough = Queens | 16:00 - 17:00 · 6.9% | 15:00 - 16:00 · 6.3% | **Sunday** · 12,550 | 11,032 |

V1 (không lọc, mỗi ngày): 18h đón 8.374 / trả 8.642; 4h đón 773 / trả 812; 7h đón 3.289 / trả 2.807.

V2 (mỗi ngày): Manhattan 19h −488, 7h +355; Queens 20h +388 (dương gần như suốt 6h–24h: sân bay là nơi xuất phát); Brooklyn 22h −270 (âm từ 9h sáng đến 4h sáng hôm sau: nơi về).

V3: ô cao nhất thứ Năm 18h 9,6K; thấp nhất thứ Ba 3h 0,2K. Thứ Bảy 1h 5,0K và Chủ nhật 1h 5,5K so với thứ Ba 1h 0,7K (đêm cuối tuần). Chủ nhật là ngày duy nhất đỉnh rơi vào 0h (6,8K).

Nhận xét để viết lên trang (tùy chọn): "Evening rush peaks at 6 pm on weekdays; weekend nights stay busy past 1 am. Queens is a net origin all day (airports), Brooklyn a net destination from 9 am through the night."


---

## 9. Trang 5: Trip Profile (A5, B1)

**Câu hỏi:** A5 phân bố chuyến theo nhóm hành khách × nhóm cự ly (lọc theo mã giá); B1 tỷ lệ boa và vận tốc trung bình theo mã giá.

**Mục tiêu đọc trong 5 giây:** đa số là chuyến ngắn, một khách (KPI, trái) → chuyến ngắn boa cao hơn (phải) → chuyến sân bay nhanh gấp đôi nhưng boa thấp hơn (dưới).

**Không dùng quãng đường trung bình** trên trang này: nhóm mã giá Unknown (17,3% số chuyến) có quãng đường trung bình 63,7 dặm ở nhóm "Over 5 miles" (Standard rate: 9,4 dặm), tức là có giá trị quãng đường bất thường; trung bình toàn kỳ 5,84 dặm (2025: 6,59) bị kéo lệch. Tỷ trọng theo nhóm cự ly bền vững hơn vì mỗi chuyến chỉ đếm một lần.

### 9.1 Bố cục

```text
0      200 216                     472 480        736 744        1000 1008       1264
┌───────┬──────────────────────────────────────────────────────────────────────────┐ 16
│ (thanh│ Trip Profile                                                             │
│  bộ   │ Who rides, how far, how fast and how they tip · answers A5, B1           │ 44
│  lọc) ├─────────────┬──────────────┬──────────────┬──────────────────────────────┤ 76
│       │ Short trips │ Solo rides   │ Avg speed    │ Avg trip duration            │
│       │ 54.6%       │ 79.0%        │ 10.9 mph     │ 17.5 min                     │
│       │ ▼ 2.1 pp ...│ ▲ 1.8 pp ... │ ▲ 1.1% ...   │ ▲ 0.1% ...                   │ 172
│       ├─────────────────────────────────┬────────────────────────────────────────┤ 184
│       │ Trips by passengers × distance  │ Card tip rate by trip distance  (V2)   │
│       │ (V1)   <2 mi  2-5 mi  >5 mi Tot │ 26%  ███                               │
│       │ 1 pax  38.2%  17.0%  10.7%  ... │ 22%  ███  ███                          │
│       │ 2-4     9.0%   4.3%   3.3%      │ 19%  ███  ███  ███                     │
│       │ 5+      0.5%   0.3%   0.1%      │      <2 mi 2-5 mi >5 mi                │
│       │ No cnt  6.8%   6.4%   3.4%      │                                        │ 484
│       ├─────────────────────────────────┴────────────────────────────────────────┤ 496
│       │ Rate code summary (V3)                                                   │
│       │ Rate code   Trips ███  Share  Card tip rate ███  Avg speed ███  Rev/Trip  │
│       │ Standard    67.2M      78.3%  23.7%              10.2 mph       $25.52    │ 704
└───────┴──────────────────────────────────────────────────────────────────────────┘
        216                          732 748                                   1264
```

| Thành phần | Visual | x | y | w | h |
|---|---|---:|---:|---:|---:|
| Tiêu đề / phụ đề | Text box | 216 | 16 / 44 | 1048 | 28 / 20 |
| K1–K4 | Card (new) | 216 / 480 / 744 / 1008 | 76 | 256 | 96 |
| V1 Nhóm khách × cự ly | Matrix (highlight table) | 216 | 184 | 516 | 300 |
| V2 Tỷ lệ boa theo cự ly | Clustered column chart | 748 | 184 | 516 | 300 |
| V3 Tổng hợp theo mã giá | Table | 216 | 496 | 1048 | 208 |

### 9.2 Chuẩn bị

1. **Truy vấn `DimPassengerGroup`:** dán lại `powerbi/queries/DimPassengerGroup.pq` (thêm `passengerorder`) > Close & Apply.
2. **Sort by column:** `DimPassengerGroup[passengergroupname]` theo `passengerorder` (1 passenger, 2-4, 5+, No passenger count); `DimDistanceGroup[distancegroupname]` theo `distancegroupsk` (Under 2, 2-5, Over 5). Ẩn `passengerorder`.
3. **Measure:** dán lại `measures.dax` (thêm 7 measure, tổng 97) > Run > Update model with changes. Định dạng:
   - `Short Trip Share`, `Solo Ride Share`, `Profile Trip Share`, `Profile Avg Tip Rate`: Percentage, 1 chữ số.
   - `Short Trip Share Change (pp)`, `Solo Ride Share Change (pp)`: Custom `▲ 0.0 "pp";▼ 0.0 "pp";0.0 "pp"`.
   - `Profile Avg Speed YoY %`, `Profile Avg Duration YoY %`: Custom `▲ 0.0%;▼ 0.0%;0.0%`.
   - `Profile Avg Speed (mph)`, `Profile Avg Duration (min)`: Decimal, 1 chữ số.
   - `Profile Avg Revenue per Trip`: Currency, 2 chữ số.
4. Duplicate trang 4, đổi tên `Trip Profile`, xóa visual trừ thanh bộ lọc, tiêu đề, phụ đề, một card.

**Lọc trên trang này:** `TripProfile` nối `DimMonth` (Year, Month lọc được) nhưng **không có khu vực**: slicer *Borough (pickup)* không tác động; ghi ở phụ đề trang. So sánh cùng kỳ không dùng `SAMEPERIODLASTYEAR` (cần `DimDate`) mà lùi `monthkey` đi 100 (xem chú thích trong `measures.dax`).

### 9.3 Cấu hình từng visual

**Tiêu đề:** "Trip Profile". Phụ đề: "Who rides, how far, how fast and how they tip · answers A5, B1 · borough filter does not apply".

**K1–K4 (Card new):** callout 28 Semibold; màu reference **trung tính** `#5F6B7A` cho cả bốn (chuyến ngắn hơn hay nhanh hơn không phải tốt/xấu).

| Card | Callout (Data) | Label | Reference label: giá trị | Tiêu đề reference |
|---|---|---|---|---|
| K1 | `Short Trip Share` | Short trips (under 2 mi) | `Short Trip Share Change (pp)` | vs same period last year |
| K2 | `Solo Ride Share` | Solo rides (known count) | `Solo Ride Share Change (pp)` | vs same period last year |
| K3 | `Profile Avg Speed (mph)` | Avg speed (mph) | `Profile Avg Speed YoY %` | vs same period last year |
| K4 | `Profile Avg Duration (min)` | Avg trip duration (min) | `Profile Avg Duration YoY %` | vs same period last year |

K2 tính trên chuyến **có** ghi nhận số khách (bỏ 16,5% No passenger count), nên nhãn ghi "(known count)".

**V1: Phân bố chuyến theo nhóm khách × cự ly (Matrix, highlight table).**

| Ô | Field |
|---|---|
| Rows | `DimPassengerGroup[passengergroupname]` |
| Columns | `DimDistanceGroup[distancegroupname]` |
| Values | `Profile Trip Share` (đổi tên "Share of trips") |
| Tooltips | `Profile Trips` |

1. *Row subtotals* On và *Column subtotals* On (tổng dòng, tổng cột = phân bố của từng chiều).
2. *Cell elements > Background color* > fx > Gradient hai màu: Lowest `#EAF1FA`, Highest `#1F5AA6`. Chỉ áp cho ô giá trị (*Apply to*: **Values only**), không tô ô tổng.
3. *Font color* > fx > Rules: value >= 0.15 → `#FFFFFF`; còn lại `#1F2933`.
4. Giá trị 1 chữ số, 10 pt, căn giữa; *Column headers* 9 Semibold; cột đầu 130 px, các cột còn lại ~90 px.
5. *Title*: "Share of trips by passengers and distance"; *Subtitle*: "% of all trips in selection · 'No passenger count' = not recorded (see Payment Methods)".

**V2: Tỷ lệ boa theo cự ly (Clustered column chart).** B1 hỏi về tỷ lệ boa; cự ly là yếu tố phân biệt rõ nhất.

| Ô | Field |
|---|---|
| X-axis | `DimDistanceGroup[distancegroupname]` |
| Y-axis | `Profile Avg Tip Rate` (đổi tên "Card tip rate") |
| Tooltips | `Profile Avg Speed (mph)`, `Profile Trips` |

1. Cột `#1F5AA6`; *Y-axis* **Minimum 0** (cột mã hóa bằng chiều dài), Title Off, định dạng 0%.
2. *Data labels* On, 1 chữ số, 10 pt; *Gridlines* Off (đã có nhãn).
3. *X-axis*: Title Off, 10 pt (ba nhãn ngắn, nằm ngang).
4. *Title*: "Card tip rate by trip distance"; *Subtitle*: "Tip ÷ fare on credit card trips · cash tips are not recorded".

**V3: Tổng hợp theo mã giá (Table).** Một bảng có data bar ở nhiều cột: mỗi dòng là một mã giá, các thanh trên cùng dòng thẳng hàng. Thay cho biểu đồ kết hợp hai trục Y (cột tỷ lệ boa + đường vận tốc) của phác thảo ban đầu.

| Thứ tự | Field | Tiêu đề cột | Định dạng |
|---:|---|---|---|
| 1 | `DimRateCode[ratecodename]` | Rate code | |
| 2 | `Profile Trips` | Trips | Millions, 1 chữ số; **Data bars** min 0 |
| 3 | `Profile Trip Share` | Share | 1 chữ số |
| 4 | `Profile Avg Tip Rate` | Card tip rate | 1 chữ số; **Data bars** min 0 |
| 5 | `Profile Avg Speed (mph)` | Avg speed (mph) | 1 chữ số; **Data bars** min 0 |
| 6 | `Profile Avg Revenue per Trip` | Rev / Trip | Currency, 2 chữ số |

1. *Filters on this visual*: `ratecodename` bỏ chọn **Group ride** (118 chuyến; tỷ lệ boa 267% do mẫu quá nhỏ).
2. Sắp theo `Trips` giảm dần; *Totals* On; header nền `#F3F5F8`; data bar `#6FA3D8`.
3. *Title*: "Rate code summary"; *Subtitle*: "Unknown rate code: 13.5M trips have no payment type; its 1.3M card trips record almost no tips · Group ride hidden (118 trips)".

### 9.4 Tương tác

- V1 → V2, V3, K1–K4: Filter (bấm ô "1 passenger × Over 5 miles": V3 cho thấy JFK chiếm phần lớn).
- V3 → V1, V2, K1–K4: Filter (bấm JFK: V1 dồn về cột Over 5 miles).
- V2 → V1: **None** (V1 đã có chiều cự ly; lọc sẽ chỉ còn một cột).

### 9.5 Đánh đổi

| Quyết định | Được | Mất |
|---|---|---|
| Bảng có data bar (V3) thay cho biểu đồ kết hợp hai trục Y | Không có hai thang đo chồng nhau gây hiểu sai tương quan (nguyên tắc 1) | Không thấy "đường" vận tốc; so bằng thanh trong cột |
| Tỷ trọng theo nhóm cự ly thay cho quãng đường trung bình | Không bị giá trị quãng đường bất thường kéo lệch | Không có con số "trung bình x dặm" |
| Giữ dòng No passenger count trong V1 | Trung thực: 16,5% chuyến; nhóm này có tỷ lệ chuyến dài cao hơn (59% trên 2 dặm so với 42–46%) | Bảng có một dòng "không thuộc nhóm nào" |
| Màu KPI trung tính | Không gán tốt/xấu cho thay đổi hành vi | Kém nổi bật |
| Ẩn Group ride ở V3 | Không có thanh 267% làm hỏng thang data bar | Mất 118 chuyến (ghi ở subtitle) |

### 9.6 Đối chiếu số liệu

| Lựa chọn | K1 Short trips | K2 Solo rides | K3 Avg speed | K4 Avg duration |
|---|---|---|---|---|
| Không lọc | 54.6% (trống) | 79.0% (trống) | 10.9 mph (trống) | 17.5 min (trống) |
| Năm 2024 | 55.7% (trống) | 78.1% (trống) | 10.9 (trống) | 17.5 (trống) |
| Năm 2025 | 53.6% · ▼ 2.1 pp | 79.9% · ▲ 1.8 pp | 11.0 · ▲ 1.1% | 17.5 · ▲ 0.1% |

V1 (không lọc, % mọi chuyến; Under 2 / 2-5 / Over 5): 1 passenger 38,2 / 17,0 / 10,7; 2-4 passengers 9,0 / 4,3 / 3,3; 5+ passengers 0,5 / 0,3 / 0,1; No passenger count 6,8 / 6,4 / 3,4. Tổng cột: 54,6 / 27,9 / 17,6.

V2: Under 2 miles 25,8%; 2-5 miles 21,7%; Over 5 miles 19,2% (vận tốc 8,2 / 10,6 / 19,8 mph).

V3 (chuyến · tỷ trọng · tỷ lệ boa · vận tốc · doanh thu/chuyến): Standard rate 67.164.261 · 78,3% · 23,7% · 10,2 · 25,52; Unknown 14.791.639 · 17,3% · 0,0% · 11,6 · 26,97; JFK 2.601.314 · 3,0% · 20,0% · 22,3 · 93,65; Negotiated fare 727.506 · 0,8% · 14,9% · 21,4 · 86,66; Newark 255.571 · 0,3% · 19,4% · 25,1 · 108,31; Nassau or Westchester 204.837 · 0,2% · 15,0% · 29,5 · 138,51.

Mã giá Unknown gồm 13,5 triệu chuyến không có hình thức thanh toán (trang 3) và 1,26 triệu chuyến thẻ (mã 99) gần như không ghi tiền boa (tổng 315 USD trên 43,4 triệu USD cước), nên tỷ lệ boa hiện 0,0%.

Nhận xét để viết lên trang (tùy chọn): "Most trips are short solo rides. Riders tip more on short trips (26% vs 19% over 5 miles); airport fares run twice as fast and earn about 4× the revenue per trip, but with a lower tip rate."

## 10. Trang 6: Routes & Map (A7, B5)

**Câu hỏi:** A7 Top N tuyến (khu vực đón → khu vực trả); B5 lượt đón/trả theo Taxi Zone trên bản đồ.

**Mục tiêu đọc trong 5 giây:** chuyến đi phân tán (10 tuyến đông nhất chỉ chiếm 3,7%) → bản đồ: taxi vàng xuất phát ở Manhattan và sân bay, kết thúc khắp thành phố → tuyến đông nhất là chặng ngắn trong Upper East Side, tuyến nhiều doanh thu nhất là chặng sân bay.

**Không dùng quãng đường trung bình** trên trang này. Ví dụ tuyến Upper East Side South → Upper East Side North: quãng đường trung bình mọi tháng khoảng 1,04 dặm, riêng 03/2025 là 12,07 dặm vì một chuyến có quãng đường bất thường. Trang dùng **thời gian trung bình** (`Route Avg Duration (min)`), ổn định theo tháng (7,1–8,6 phút).

**Màu bản đồ là tỷ lệ cân bằng đón/trả, không phải số chuyến.** Lượt đón theo khu vực lệch rất mạnh (trung vị 18 nghìn, lớn nhất 3,9 triệu): tô theo số chuyến thì gần như mọi khu vực ngoài Manhattan cùng một màu nhạt. Tỷ lệ `(trả − đón) / (trả + đón)` nằm trong [−1, +1], so được giữa khu vực lớn và nhỏ. Số chuyến tuyệt đối nằm ở tooltip.

### 10.1 Bố cục

```text
0      200 216                     472 480        736 744        1000 1008       1264
┌───────┬──────────────────────────────────────────────────────────────────────────┐ 16
│ (thanh│ Routes & Map                                                             │
│  bộ   │ Where trips start and end · answers A7, B5                               │ 44
│  lọc) ├─────────────┬──────────────┬──────────────┬──────────────────────────────┤ 76
│       │ Top 10      │ Cross-borough│ Airport      │ Top pickup zone              │
│       │ routes 3.7% │ trips 14.1%  │ pickups 7.4% │ Upper East Side South        │
│       │ of 56,336...│ ▲ 0.9 pp ... │ ▼ 0.9 pp ... │ 4.6% of pickups              │ 172
│       ├─────────────────────────────────┬────────────────────────────────────────┤ 184
│       │ Pickup vs drop-off balance (V1) │ Busiest routes (V2)                    │
│       │                                 │ Route              Trips ███  Min  $/T │
│       │      [Shape map Taxi Zone]      │ UES South → North  568.5K     7.8  15.79│ 440
│       │   cam = nhiều lượt đón hơn      ├────────────────────────────────────────┤ 448
│       │   xanh = nhiều lượt trả hơn     │ Highest-revenue routes (V3)            │
│       │                                 │ Route              Rev ███  Trips  $/T │
│       │                                 │ JFK → Outside NYC  $22.0M   170.2K ... │ 704
└───────┴─────────────────────────────────┴────────────────────────────────────────┘
        216                          732 748                                   1264
```

| Thành phần | Visual | x | y | w | h |
|---|---|---:|---:|---:|---:|
| Tiêu đề / phụ đề | Text box | 216 | 16 / 44 | 1048 | 28 / 20 |
| K1–K4 | Card (new) | 216 / 480 / 744 / 1008 | 76 | 256 | 96 |
| V1 Cân bằng đón/trả | Shape map | 216 | 184 | 516 | 520 |
| V2 Tuyến đông nhất | Table | 748 | 184 | 516 | 256 |
| V3 Tuyến nhiều doanh thu nhất | Table | 748 | 448 | 516 | 256 |

Bản đồ đặt bên trái và cao hết vùng dữ liệu: đây là visual chính của trang (nguyên tắc 6: thông tin quan trọng bên trái), và hình Taxi Zone cần chiều cao (New York trải dọc).

### 10.2 Chuẩn bị

1. **Bật Shape map:** File > Options and settings > Options > Preview features > **Shape map visual**, khởi động lại Power BI.
2. **Measure:** dán lại `measures.dax` (thêm 11 measure, tổng 108) > Run > Update model with changes. Định dạng:
   - `Top 10 Routes Share`, `Cross-Borough Trip Share`, `Airport Pickup Share`, `Top Pickup Zone Share`, `Route Trip Share`: Percentage, 1 chữ số.
   - `Cross-Borough Share Change (pp)`, `Airport Pickup Share Change (pp)`: Custom `▲ 0.0 "pp";▼ 0.0 "pp";0.0 "pp"`.
   - `Route Count`: Whole number, dấu phân cách hàng nghìn.
   - `Route Avg Duration (min)`: Decimal, 1 chữ số. `Route Avg Revenue per Trip`: Currency, 2 chữ số. `Route Revenue`: Currency.
   - `Zone Net Flow Ratio`: Custom `+0.00;-0.00;0.00`.
3. Duplicate trang 5, đổi tên `Routes & Map`, xóa visual trừ thanh bộ lọc, tiêu đề, phụ đề, một card.

**Lọc trên trang này:** `RoutesMonthly` nối `DimMonth` (Year, Month lọc được) và `DimLocation` qua `pickup_locationsk` (đang bật), nên slicer *Borough (pickup)* lọc **quận đón** ở K1–K3, V2, V3. Trên bản đồ, `Zone Dropoffs` bật quan hệ `dropoff_locationsk` bằng `USERELATIONSHIP`, nên chọn Manhattan thì bản đồ chỉ còn các khu vực Manhattan với cả lượt đón lẫn lượt trả tại đó.

### 10.3 Cấu hình từng visual

**Tiêu đề:** "Routes & Map". Phụ đề: "Where trips start and end · answers A7, B5 · borough filter = pickup borough".

**K1–K4 (Card new):** callout 28 Semibold (K4 là tên khu vực: callout **20**); màu reference trung tính `#5F6B7A`.

| Card | Callout (Data) | Label | Reference label: giá trị | Tiêu đề reference |
|---|---|---|---|---|
| K1 | `Top 10 Routes Share` | Top 10 routes' share of trips | `Route Count` | routes in selection |
| K2 | `Cross-Borough Trip Share` | Cross-borough trips | `Cross-Borough Share Change (pp)` | vs same period last year |
| K3 | `Airport Pickup Share` | Airport pickups (JFK, LGA, EWR) | `Airport Pickup Share Change (pp)` | vs same period last year |
| K4 | `Top Pickup Zone` | Top pickup zone | `Top Pickup Zone Share` | of pickups |

K1 cho biết mức tập trung: 10 tuyến đông nhất chỉ chiếm 3,7% trên 56.336 tuyến, nên bảng V2 là "đỉnh" của một phân bố đuôi dài, không đại diện cho phần lớn chuyến đi. K2 tính cả chuyến đi/đến Outside of NYC và Unknown.

**V1: Cân bằng đón/trả theo khu vực (Shape map).**

| Ô | Field |
|---|---|
| Location | `DimLocation[locationid]` |
| Color saturation | `Zone Net Flow Ratio` |
| Tooltips | `DimLocation[zone]`, `DimLocation[borough]`, `Zone Pickups`, `Zone Dropoffs`, `Zone Net Inflow` |

1. *Map settings* > Map type **Custom map** > Add map type: `powerbi/map_shapes/taxi_zones.topojson`; Projection **Mercator**. Mở *View map keys* để kiểm tra danh sách `LocationID` (xem `powerbi.md` mục 4 nếu bản đồ xám toàn bộ).
2. *Fill colors*: bật **Diverging**. Minimum **−1** `#C65A00` (cam đậm: chỉ có lượt đón), Center **0** `#F3F5F8`, Maximum **+1** `#1F5AA6` (xanh: chỉ có lượt trả). Đặt giá trị cố định (không để *Auto*) để thang không đổi khi lọc.
3. Màu khu vực không có dữ liệu (BLANK, dưới 1.000 lượt): xám `#E1E5EB`. Viền khu vực trắng, 0,5 px nếu có tùy chọn.
4. *Legend* Off (Shape map không có chú giải dải màu); giải thích bằng phụ đề.
5. *Title*: "Pickup vs drop-off balance by zone"; *Subtitle*: "Orange = more pickups than drop-offs · Blue = more drop-offs · Grey = under 1,000 trips or no data · hover for counts".

Đọc: 222/248 khu vực có đủ dữ liệu nghiêng về xanh (nhiều lượt trả hơn), vì taxi vàng chủ yếu đón ở Manhattan và sân bay. JFK (−0,63) và LaGuardia (−0,46) cam đậm nhất; Penn Station (−0,20) là điểm xuất phát rõ nhất trong Manhattan.

**V2: Tuyến đông nhất (Table, Top 10 theo số chuyến).** Tên tuyến dài ("Penn Station/Madison Sq West → Times Sq/Theatre District"), nên dùng bảng có data bar: chữ xuống dòng được, thanh vẫn so bằng chiều dài. Biểu đồ thanh ngang sẽ cắt nhãn trục.

| Thứ tự | Field | Tiêu đề cột | Định dạng |
|---:|---|---|---|
| 1 | `RoutesMonthly[route]` | Route | Word wrap On, rộng ~220 px |
| 2 | `Route Trips` | Trips | Thousands (K), 1 chữ số; **Data bars** `#6FA3D8`, min 0 |
| 3 | `Route Trip Share` | Share | 1 chữ số |
| 4 | `Route Avg Duration (min)` | Avg min | 1 chữ số |
| 5 | `Route Avg Revenue per Trip` | Rev / Trip | Currency, 2 chữ số |

1. *Filters on this visual*: `route` > Filter type **Top N** > Show items **Top 10** > By value `Route Trips` > Apply filter.
2. Sắp theo `Trips` giảm dần; *Totals* Off (tổng 10 dòng dễ bị đọc nhầm thành tổng mọi tuyến; con số đó có ở K1).
3. *Title*: "Busiest routes"; *Subtitle*: "Top 10 pickup → drop-off zone pairs by trips · mostly short hops inside the Upper East Side".

**V3: Tuyến nhiều doanh thu nhất (Table, Top 10 theo doanh thu).** Cùng cấu trúc với V2 để so hai danh sách theo hàng.

| Thứ tự | Field | Tiêu đề cột | Định dạng |
|---:|---|---|---|
| 1 | `RoutesMonthly[route]` | Route | Word wrap On, rộng ~220 px |
| 2 | `Route Revenue` | Revenue | Currency, Millions, 1 chữ số; **Data bars** `#6FA3D8`, min 0 |
| 3 | `Route Trips` | Trips | Thousands (K), 1 chữ số |
| 4 | `Route Avg Duration (min)` | Avg min | 1 chữ số |
| 5 | `Route Avg Revenue per Trip` | Rev / Trip | Currency, 2 chữ số |

1. *Filters on this visual*: `route` > **Top N** > Top 10 > By value `Route Revenue`.
2. Sắp theo `Revenue` giảm dần; *Totals* Off.
3. *Title*: "Highest-revenue routes"; *Subtitle*: "Top 10 by revenue · airport runs earn 5–8× more per trip than the busiest routes".

### 10.4 Tương tác

- V1 → V2, V3, K1–K4: Filter. Quan hệ pickup đang bật, nên bấm một khu vực trên bản đồ thì V2, V3 hiện các tuyến **xuất phát** từ khu vực đó (bấm JFK: JFK → Outside of NYC, JFK → Times Sq/Theatre District...).
- V2 → V1: Filter. Bản đồ chỉ còn hai khu vực của tuyến: điểm đón cam đậm (−1), điểm trả xanh (+1). Tuyến trong cùng một khu vực (UES South → UES South) hiện màu trung tính (0).
- V3 → V1: Filter (như trên).
- V2 ↔ V3: **None** (mỗi bảng có Top N riêng; lọc chéo làm bảng kia còn 0–1 dòng).
- V2, V3 → K1–K4: None (K1 "Top 10 share" mất nghĩa khi chỉ còn một tuyến).

### 10.5 Đánh đổi

| Quyết định | Được | Mất |
|---|---|---|
| Tô bản đồ theo tỷ lệ cân bằng đón/trả thay cho số chuyến | Khu vực nhỏ và lớn so được trên cùng thang; thang chia đôi cam/xanh an toàn cho người mù màu (nguyên tắc 3) | Không thấy độ lớn tuyệt đối trên bản đồ (có ở tooltip và K4); diện tích khu vực vẫn ảnh hưởng cảm nhận (JFK lớn nên nổi bật) |
| Ngưỡng 1.000 lượt mới tô màu | Không có khu vực tô đậm chỉ vì vài chuyến | 13 khu vực xám ở toàn kỳ; lọc một tháng thì nhiều khu vực ngoại ô xám hơn |
| Bảng có data bar thay cho biểu đồ thanh ngang | Tên tuyến dài xuống dòng, không bị cắt | Thanh ngắn hơn so với biểu đồ thanh toàn khung |
| Thời gian trung bình thay cho quãng đường trung bình | Không bị giá trị quãng đường bất thường kéo lệch | Không có con số dặm trên tuyến |
| Hai bảng Top 10 (số chuyến, doanh thu) thay cho một | Thấy ngay hai loại tuyến khác nhau: ngắn và đông / dài và đắt | Tốn chỗ; chỉ JFK → JFK và hai tuyến UES có mặt ở cả hai bảng |
| Tuyến theo tên khu vực | Đọc được | Corona (56, 57) và Governor's Island (103–105) bị gộp theo tên |

### 10.6 Đối chiếu số liệu

| Lựa chọn | K1 Top 10 share | K2 Cross-borough | K3 Airport pickups | K4 Top pickup zone |
|---|---|---|---|---|
| Không lọc | 3.7% · 56,336 routes | 14.1% (trống) | 7.4% (trống) | Upper East Side South · 4.6% |
| Năm 2024 | 3.9% · 50,201 | 13.6% (trống) | 7.9% (trống) | JFK Airport · 4.7% |
| Năm 2025 | 3.6% · 54,688 | 14.5% · ▲ 0.9 pp | 7.0% · ▼ 0.9 pp | Upper East Side South · 4.5% |

V2 (không lọc; chuyến · tỷ trọng · phút · doanh thu/chuyến): Upper East Side South → North 568.515 · 0,66% · 7,8 · 15,79; Upper East Side North → South 488.172 · 0,57% · 8,6 · 16,18; UES South → UES South 395.112 · 0,46% · 6,1 · 14,65; UES North → UES North 374.667 · 0,44% · 5,1 · 13,78; Midtown Center → UES South 267.715 · 0,31% · 10,4 · 18,12. Tuyến thứ 10: Upper West Side South → Lincoln Square East 201.889.

V3 (không lọc; doanh thu · chuyến · phút · doanh thu/chuyến): JFK Airport → Outside of NYC 22,04 triệu · 170.165 · 45,1 · 129,51; JFK → Times Sq/Theatre District 16,54 triệu · 173.745 · 61,6 · 95,21; LaGuardia → Times Sq/Theatre District 12,53 triệu · 156.517 · 42,3 · 80,05; JFK → Midtown South 9,40 triệu; UES South → North 8,98 triệu. Tổng 10 tuyến = 4,4% doanh thu.

V1 (tỷ lệ cân bằng, toàn kỳ): JFK −0,63; LaGuardia −0,46; Penn Station/Madison Sq West −0,20; Midtown Center −0,10; Upper East Side North +0,02; East Harlem North +0,38; Two Bridges/Seward Park +0,42. Mã 264 (Unknown) và 265 (Outside of NYC, +0,80) không có hình nên không hiện.

Nhận xét để viết lên trang (tùy chọn): "Trips are spread across 56K routes; the top 10 carry under 4%. The busiest are short Upper East Side hops (~8 min, ~$16), while airport runs earn 5–8× more per trip. Most zones receive more taxis than they send: pickups concentrate in Manhattan and at JFK/LaGuardia."

## 11. Trang 7: Trends & Comparisons (B2, B3, B4)

**Câu hỏi:**
- B2: doanh thu tháng 6 so với tháng 5, yếu tố nào đóng góp.
- B3: doanh thu tăng do số chuyến hay do doanh thu mỗi chuyến; trong mỗi chuyến, khoản nào thay đổi.
- B4: so sánh cùng kỳ năm trước theo tháng.

**Mục tiêu đọc trong 5 giây:**
- Doanh thu 2025 tăng 13,0%, gần bằng mức tăng số chuyến (12,1%). Tăng trưởng đến từ số chuyến, doanh thu mỗi chuyến chỉ tăng 0,8% (KPI).
- Tháng nào cũng tăng so với 2024 (V2).
- Trong mỗi chuyến, phí CBD mới (+0,55 USD) bù cho tiền boa và phụ phí ùn tắc giảm (V3).
- Tháng 6 thấp hơn tháng 5 chủ yếu vì Manhattan, và một phần chỉ vì tháng 6 ít hơn một ngày (V4, K4).

**Trang này cố định so sánh 2025 với 2024.** Mọi câu hỏi của trang là so sánh giữa hai kỳ: nếu theo slicer Year thì chọn 2024 sẽ không có kỳ trước, còn không chọn năm thì `HASONEVALUE` trả BLANK. Vì vậy:
- slicer Year **không hiển thị** trên trang này (bỏ đồng bộ);
- năm được gắn bằng bộ lọc từng visual;
- slicer Month và Borough vẫn có tác dụng.

### 11.1 Bố cục

```text
0      200 216                     472 480        736 744        1000 1008       1264
┌───────┬──────────────────────────────────────────────────────────────────────────┐ 16
│ (thanh│ Trends & Comparisons                                                     │
│  bộ   │ 2025 vs 2024 · answers B2, B3, B4                                        │ 44
│  lọc) ├─────────────┬──────────────┬──────────────┬──────────────────────────────┤ 76
│ Year: │ Revenue     │ Trips        │ Revenue per  │ June vs May revenue          │
│ fixed │ ▲ 13.0%     │ ▲ 12.1%      │ trip ▲ 0.8%  │ ▼ 4.4%                       │
│       │ $1.31bn ... │ 45.3M ...    │ $28.98 ...   │ per day ▼ 1.2%               │ 172
│       ├─────────────────────────────────┬────────────────────────────────────────┤ 184
│       │ Monthly revenue 2024 vs 2025    │ Growth vs same month last year (V2)    │
│       │ (V1, 2 đường)                   │ cột Revenue YoY % và Trips YoY %       │ 484
│       ├─────────────────────────────────┼────────────────────────────────────────┤ 496
│       │ What changed revenue per trip   │ June vs May revenue change by borough  │
│       │ (V3 waterfall)                  │ (V4, thanh ngang hai phía)             │ 704
└───────┴─────────────────────────────────┴────────────────────────────────────────┘
        216                          732 748                                   1264
```

| Thành phần | Visual | x | y | w | h |
|---|---|---:|---:|---:|---:|
| Tiêu đề / phụ đề | Text box | 216 | 16 / 44 | 1048 | 28 / 20 |
| K1–K4 | Card (new) | 216 / 480 / 744 / 1008 | 76 | 256 | 96 |
| V1 Doanh thu theo tháng, hai năm | Line chart | 216 | 184 | 516 | 300 |
| V2 Tăng trưởng cùng kỳ theo tháng | Clustered column chart | 748 | 184 | 516 | 300 |
| V3 Thay đổi doanh thu mỗi chuyến theo khoản | Waterfall chart | 216 | 496 | 516 | 208 |
| V4 Tháng 6 so với tháng 5 theo quận | Clustered bar chart | 748 | 496 | 516 | 208 |
| Ghi chú năm | Text box (thanh bộ lọc, chỗ slicer Year) | 16 | 76 | 168 | 76 |

### 11.2 Chuẩn bị

1. **Truy vấn `DimMonth`:** dán lại `powerbi/queries/DimMonth.pq` (thêm `monthshort` = Jan…Dec). Sort by column: `DimMonth[monthshort]` theo `month`.
2. **Truy vấn `RevenueComponent`:** New Source > Blank Query, tên `RevenueComponent`, dán `powerbi/queries/RevenueComponent.pq` > Close & Apply.
   - **Không tạo quan hệ** (Model view: bảng đứng riêng).
   - Sort by column: `component` theo `componentorder`; ẩn `componentorder`.
   - Phải tạo bảng này **trước** khi dán measure: `Component Amount` tham chiếu `RevenueComponent[component]`.
3. **Measure:** dán lại `measures.dax` (thêm 11 measure, tổng 119) > Run > Update model with changes. Định dạng:
   - `Revenue per Day June vs May %`: Custom `▲ 0.0%;▼ 0.0%;0.0%`.
   - `Revenue per Day May`, `Revenue per Day June`: Currency, 0 chữ số.
   - `Component per Trip`, `Component per Trip Change`: Currency, 2 chữ số. Có thể dùng Custom `+$0.00;-$0.00;$0.00` để hiện dấu.
   - `Congestion Surcharge`, `Airport Fee`, `CBD Congestion Fee`, `Other Surcharges`, `Unreconciled Amount`, `Component Amount`: Currency.
   - Nếu chưa đặt ở trang 1: `Revenue June vs May %` dùng Custom `▲ 0.0%;▼ 0.0%;0.0%`; `Revenue June vs May` dùng Currency.
4. Duplicate trang 6, đổi tên `Trends & Comparisons`, xóa visual trừ thanh bộ lọc, tiêu đề, phụ đề, một card.
5. **Bỏ slicer Year trên trang này:** View > **Sync slicers** > chọn slicer Year > ở dòng `Trends & Comparisons` bỏ tích cả **Sync** và **Visible**. Xóa slicer Year nếu nó còn trên trang.
6. **Ghi chú năm:** đặt Text box vào chỗ trống (x 16, y 76, w 168, h 76):
   - dòng 1 "Year" (10 Semibold);
   - dòng 2 "Fixed on this page: 2025 vs 2024" (9, `#5F6B7A`).

**Bộ lọc năm từng visual** (*Filters on this visual* > kéo `DimMonth[year]` vào > Basic filtering):

| Visual | Year |
|---|---|
| K1–K4, V2, V3, V4 | **2025** |
| V1 | **2024** và **2025** (bỏ 2026, chỉ có ngày trả khách) |

### 11.3 Cấu hình từng visual

**Tiêu đề:** "Trends & Comparisons". Phụ đề: "2025 vs 2024 · answers B2, B3, B4 · Year slicer does not apply on this page".

**K1–K4 (Card new):** callout là **mức thay đổi** (đúng câu hỏi của trang), reference là giá trị tuyệt đối. Callout tô màu fx: > 0 `#1F5AA6`, < 0 `#C65A00`, như reference của trang 1. Reference màu `#5F6B7A`.

| Card | Callout (Data) | Label | Reference label: giá trị | Tiêu đề reference |
|---|---|---|---|---|
| K1 | `Revenue YoY %` | Revenue vs 2024 | `Revenue` | 2025 total |
| K2 | `Trips YoY %` | Trips vs 2024 | `Trips` | 2025 total |
| K3 | `Avg Revenue per Trip YoY %` | Revenue per trip vs 2024 | `Avg Revenue per Trip` | 2025 average |
| K4 | `Revenue June vs May %` | June vs May revenue (2025) | `Revenue per Day June vs May %` | per day |

K1 và K2 đặt cạnh nhau để trả lời B3 trước khi xem biểu đồ: doanh thu tăng gần bằng số chuyến, nên K3 chỉ +0,8%. K4: tháng 5 có 31 ngày, tháng 6 có 30, nên −4,4% tổng nhưng chỉ −1,2% mỗi ngày.

**V1: Doanh thu theo tháng, 2024 và 2025 (Line chart).** Biểu đồ đường cho phép trục không bắt đầu từ 0 (nguyên tắc 3). Hai năm dùng chung trục tháng nên so được theo vị trí.

| Ô | Field |
|---|---|
| X-axis | `DimMonth[monthshort]` (Jan…Dec, Sort by `month`) |
| Y-axis | `Revenue` |
| Legend | `DimMonth[year]` |
| Tooltips | `Trips`, `Avg Revenue per Trip` |

1. *Lines*: 2025 `#1F5AA6` 2,5 px; 2024 `#8A94A3` 1,5 px (năm so sánh là nền). *Markers* On, 4 px.
2. *X-axis*: Type **Categorical**, Title Off. Tên tháng 3 chữ (`monthshort`) để 12 nhãn nằm ngang trong 516 px, không xoay chữ (nguyên tắc 6).
3. *Y-axis*: Title Off, đơn vị Millions, *Gridlines* `#E6E9EE`.
4. *Legend*: Top left. Hoặc tắt Legend và dùng *Series labels* (đặt tên năm ở cuối đường) để không phải dò chú giải.
5. *Title*: "Monthly revenue, 2025 vs 2024"; *Subtitle*: "Pickup month · y-axis does not start at zero".

**V2: Tăng trưởng so với cùng tháng năm trước (Clustered column chart).** Đặt doanh thu và số chuyến cạnh nhau: hai cột gần bằng nhau thì tăng trưởng đến từ số chuyến; cột doanh thu cao hơn thì doanh thu mỗi chuyến tăng.

| Ô | Field |
|---|---|
| X-axis | `DimMonth[monthshort]` |
| Y-axis | `Revenue YoY %` (đổi tên "Revenue"), `Trips YoY %` (đổi tên "Trips") |
| Tooltips | `Revenue`, `Revenue PY` |

1. *Columns*: Revenue `#1F5AA6`, Trips `#E69F00` (cặp xanh/cam an toàn cho người mù màu).
2. *Y-axis*: **Minimum 0** (cột mã hóa bằng chiều dài; mọi tháng đều dương), định dạng 0%, Title Off.
3. *Data labels* Off (24 cột, nhãn chồng nhau); *Gridlines* `#E6E9EE`; số chính xác ở tooltip.
4. *Legend*: Top left.
5. *Title*: "Growth vs same month last year"; *Subtitle*: "2025 vs 2024 · revenue grows with trips; December stands out (+25.6% revenue, +17.0% trips)".

Nếu một tháng âm (khi lọc Borough nhỏ), trục vẫn bắt đầu từ 0 nhưng phải mở rộng xuống dưới: đặt *Minimum* về Auto. Power BI vẫn vẽ cột từ 0.

**V3: Khoản nào làm thay đổi doanh thu mỗi chuyến (Waterfall chart).** Waterfall mã hóa bằng chiều dài và vị trí trên cùng một trục. Cột cuối (Total) bằng thay đổi của `Avg Revenue per Trip`, nên khớp với K3.

| Ô | Field |
|---|---|
| Category | `RevenueComponent[component]` |
| Y-axis | `Component per Trip Change` |
| Tooltips | `Component per Trip` |

1. *Sentiment colors*: Increase `#1F5AA6`, Decrease `#C65A00`, Total `#5F6B7A`.
2. Sắp xếp: … > Sort axis > **component** (Ascending), theo thứ tự `componentorder`, không theo giá trị. Thứ tự cố định thì so được giữa các lần lọc.
3. *Data labels* On, định dạng `+$0.00;-$0.00`, 9 pt; *Y-axis* Title Off; *Gridlines* Off.
4. *X-axis*: nhãn 9 pt. Nếu nhãn dài bị xoay, nới chiều rộng hoặc rút tên trong `RevenueComponent.pq` ("Congestion", "Airport", "CBD fee", "Other"). Không để chữ xoay.
5. *Title*: "What changed revenue per trip (2025 vs 2024)"; *Subtitle*: "USD per trip · CBD congestion fee started Jan 2025 · 'Unreconciled' = total amount minus its parts in source data".

**V4: Tháng 6 so với tháng 5 theo quận (Clustered bar chart, hai phía).**

| Ô | Field |
|---|---|
| Y-axis | `DimLocation[borough]` |
| X-axis | `Revenue June vs May` |
| Tooltips | `Revenue May`, `Revenue June`, `Revenue June vs May %` |

1. *Bars* > fx > Rules: value < 0 `#C65A00`; value >= 0 `#1F5AA6`.
2. *X-axis*: Title Off, đơn vị Millions; đường 0 hiện rõ (*Gridlines* hoặc *Zero line* nếu có).
3. *Data labels* On, đơn vị Millions, 1 chữ số.
4. Sắp theo `Revenue June vs May` tăng dần: giảm nhiều nhất ở trên cùng.
5. *Filters on this visual*: `borough` bỏ **Unknown**, **N/A**, **EWR** (mỗi nhóm dưới 0,05 triệu USD, chỉ là nhiễu).
6. *Title*: "June vs May revenue change by pickup borough (2025)"; *Subtitle*: "June has one day fewer: −4.4% in total, −1.2% per day".

### 11.4 Tương tác

- Slicer Year: không có trên trang (đã bỏ đồng bộ).
- V1 → V2, V3, V4, K1–K4: **None**. V1 có trục tháng; bấm một điểm sẽ lọc theo tháng *và* năm 2024, mâu thuẫn với bộ lọc 2025 của các visual khác.
- V2 → V3, K1–K3: Filter (bấm tháng 12: waterfall hiện thay đổi doanh thu mỗi chuyến của riêng tháng 12). V2 → V1: Highlight. V2 → V4, K4: **None** (B2 luôn là tháng 5, 6).
- V3 → mọi visual: **None** (bảng `RevenueComponent` không có quan hệ, nên lọc không có tác dụng).
- V4 → V1, V2, V3, K1–K4: Filter (bấm Manhattan: cả trang chỉ còn Manhattan, như slicer Borough).

### 11.5 Đánh đổi

| Quyết định | Được | Mất |
|---|---|---|
| Cố định 2025 so với 2024, bỏ slicer Year trên trang | Mọi visual luôn có kỳ so sánh, không có ô trống | Không xem được tháng 6 so với tháng 5 của 2024 (−6,4%; mỗi ngày −3,2%: ghi ở mục 11.6) |
| Callout KPI là mức thay đổi, giá trị tuyệt đối ở reference | Đúng câu hỏi của trang; không lặp trang 1 | Người xem tìm tổng phải đọc dòng nhỏ |
| V1 hai đường chung trục, trục Y không từ 0 | Thấy rõ khoảng cách giữa hai năm và mùa vụ (giảm tháng 7, 8) | Độ dốc trông lớn hơn tỷ lệ thật; ghi ở phụ đề |
| Waterfall theo khoản trên mỗi chuyến thay cho đường từng khoản theo tháng | Trả lời trực tiếp "khoản nào"; tổng khớp K3 | Mất diễn biến theo tháng (bấm cột tháng ở V2 để xem từng tháng) |
| Giữ cột "Unreconciled" | Trung thực: các khoản trong nguồn không cộng đúng TotalAmount (2024 −0,29 USD/chuyến); tổng waterfall vẫn khớp | Có một cột khó giải thích; phải ghi ở phụ đề |
| V4 thay đổi tuyệt đối (USD) thay cho % | Thấy quận nào đóng góp nhiều nhất vào mức giảm | Quận nhỏ có % lớn (Brooklyn +17%) nhưng thanh ngắn; % ở tooltip |

### 11.6 Đối chiếu số liệu

KPI (không lọc Month, Borough):

| Card | Callout | Reference |
|---|---|---|
| K1 | ▲ 13.0% | $1.31bn (1.313,4 triệu) |
| K2 | ▲ 12.1% | 45.3M (45.322.899) |
| K3 | ▲ 0.8% | $28.98 (2024: $28.75) |
| K4 | ▼ 4.4% | ▼ 1.2% |

V2 (2025 so với 2024, doanh thu / số chuyến): T1 12,4 / 13,8; T2 11,7 / 14,3; T3 11,5 / 11,1; T4 8,8 / 8,5; T5 15,3 / 14,7; T6 17,8 / 14,4; T7 19,2 / 19,2; T8 10,5 / 11,8; T9 12,0 / 10,7; T10 7,5 / 7,5; T11 3,7 / 4,2; T12 25,6 / 17,0. Tháng 12/2025 có doanh thu mỗi chuyến 31,66 USD (2024: 29,49), cước mỗi chuyến 22,84 so với 20,55.

V3 (USD/chuyến, 2025 so với 2024): Fare +0,26; Tip −0,35; Tolls −0,05; Congestion surcharge −0,28; Airport fee −0,02; CBD congestion fee +0,55; Other surcharges −0,17; Unreconciled +0,30; **Total +0,23** (28,75 → 28,98). Tiền boa mỗi chuyến giảm (3,37 → 3,01) cùng lúc tỷ trọng thanh toán Unknown tăng từ 9,8% lên 21,1% (trang 3).

V4 (2025, triệu USD): Manhattan −4,93 (−5,5%); Queens −1,21 (−4,4%); Brooklyn +0,76 (+17,0%); Bronx +0,04 (+3,5%); Staten Island ~0. Tổng −5,42 triệu (123,32 → 117,90). Năm 2024: tổng −6,79 triệu (−6,4%; mỗi ngày −3,2%).

Theo mã giá (không có trên trang, dùng để giải thích B2 nếu được hỏi): năm 2025 Standard rate −7,8 triệu (−9,8%), còn Unknown **+3,4 triệu (+13,0%)**. Một phần chuyến chuyển sang nhóm thiếu mã giá, nên phân tích theo mã giá không cho thấy thay đổi hành vi thật.

Nhận xét để viết lên trang (tùy chọn): "Revenue grew 13% in 2025, almost entirely from more trips (+12%); revenue per trip rose only $0.23, as the new CBD congestion fee (+$0.55) offset lower recorded tips and congestion surcharges. June trails May mostly in Manhattan, and partly because June has one day fewer."
