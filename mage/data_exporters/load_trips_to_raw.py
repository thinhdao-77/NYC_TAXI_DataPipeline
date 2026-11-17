"""Nạp Yellow Taxi Trip Records (Parquet) vào DuckDB: raw.yellow_tripdata.

- Tự tải file còn thiếu từ nguồn TLC vào data/raw (retry, tải vào .tmp rồi mới đổi tên).
- Mỗi file nạp trong một transaction: xóa các dòng cũ của file đó rồi INSERT lại, nên chạy lại không trùng.
- Ghi log từng file vào control.etl_control; LSET tính từ log này.

Biến pipeline: file_name (tên file hoặc ALL), year, start_month, end_month, use_lset.
"""
import os
import re
import shutil
import time
import urllib.error
import urllib.request
from datetime import datetime

try:
    from mage.utils.duckdb_helpers import connect, init_schema, next_batch_id, write_log
except ImportError:  # khi Mage đặt thư mục project làm gốc import
    from utils.duckdb_helpers import connect, init_schema, next_batch_id, write_log

if 'data_exporter' not in globals():
    from mage_ai.data_preparation.decorators import data_exporter

RAW_DIR = os.environ.get('RAW_DATA_DIR', '/home/src/data/raw')
BASE_URL = 'https://d37ci6vzurychx.cloudfront.net/trip-data'
TABLE = 'raw.yellow_tripdata'
PIPELINE_NAME = 'ingest_yellow_trips'
FIRST_MONTH = '2024-01'
FILE_PATTERN = re.compile(r'yellow_tripdata_\d{4}-\d{2}\.parquet')

# Cột đích -> tên cột trong Parquet (so khớp không phân biệt hoa thường, vd Airport_fee).
TARGET = {
    'vendor_id': ('VendorID', 'INTEGER'),
    'tpep_pickup_datetime': ('tpep_pickup_datetime', 'TIMESTAMP'),
    'tpep_dropoff_datetime': ('tpep_dropoff_datetime', 'TIMESTAMP'),
    'passenger_count': ('passenger_count', 'BIGINT'),
    'trip_distance': ('trip_distance', 'DOUBLE'),
    'ratecode_id': ('RatecodeID', 'BIGINT'),
    'store_and_fwd_flag': ('store_and_fwd_flag', 'VARCHAR'),
    'pu_location_id': ('PULocationID', 'INTEGER'),
    'do_location_id': ('DOLocationID', 'INTEGER'),
    'payment_type': ('payment_type', 'BIGINT'),
    'fare_amount': ('fare_amount', 'DOUBLE'),
    'extra': ('extra', 'DOUBLE'),
    'mta_tax': ('mta_tax', 'DOUBLE'),
    'tip_amount': ('tip_amount', 'DOUBLE'),
    'tolls_amount': ('tolls_amount', 'DOUBLE'),
    'improvement_surcharge': ('improvement_surcharge', 'DOUBLE'),
    'total_amount': ('total_amount', 'DOUBLE'),
    'congestion_surcharge': ('congestion_surcharge', 'DOUBLE'),
    'airport_fee': ('airport_fee', 'DOUBLE'),
    'cbd_congestion_fee': ('cbd_congestion_fee', 'DOUBLE'),
}


def to_bool(v):
    return str(v).strip().lower() in ('1', 'true', 'yes', 'y')


def download_file_with_retry(file_name, max_retries=3):
    """Trả về (ok, lý do). Tải vào .tmp, đủ 100% mới đổi tên."""
    os.makedirs(RAW_DIR, exist_ok=True)
    target = os.path.join(RAW_DIR, file_name)
    if os.path.exists(target):
        return True, None
    tmp = target + '.tmp'
    url = f'{BASE_URL}/{file_name}'
    last = None
    for attempt in range(1, max_retries + 1):
        print(f'[DOWNLOAD] {file_name} (lần {attempt}/{max_retries})...')
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=120) as resp, open(tmp, 'wb') as out:
                shutil.copyfileobj(resp, out)
            os.replace(tmp, target)
            print(f'[DOWNLOAD OK] {file_name}')
            return True, None
        except urllib.error.HTTPError as e:
            if os.path.exists(tmp):
                os.remove(tmp)
            last = f'HTTP {e.code}: {e.reason}'
            if e.code in (403, 404):
                print(f'[DOWNLOAD] {file_name}: nguồn chưa có ({last})')
                return False, last
        except Exception as e:
            if os.path.exists(tmp):
                os.remove(tmp)
            last = str(e)
        print(f'[DOWNLOAD WARN] {file_name}: {last}')
        time.sleep(3 * (2 ** (attempt - 1)))
    return False, f'Tải thất bại sau {max_retries} lần: {last}'


def build_insert_sql(con, path):
    """SELECT khớp cột theo tên; cột không có trong file (vd cbd_congestion_fee năm 2024) thành NULL."""
    source_cols = {r[0].lower(): r[0] for r in
                   con.execute('SELECT column_name FROM (DESCRIBE SELECT * FROM read_parquet(?))',
                               [path]).fetchall()}
    select = []
    for target, (source, sql_type) in TARGET.items():
        actual = source_cols.get(source.lower())
        expr = f'CAST("{actual}" AS {sql_type})' if actual else f'CAST(NULL AS {sql_type})'
        select.append(f'{expr} AS {target}')
    cols = ', '.join(list(TARGET) + ['source_file_name', 'source_row_number', 'batch_id'])
    return (f'INSERT INTO {TABLE} ({cols}) '
            f'SELECT {", ".join(select)}, ? AS source_file_name, '
            f'file_row_number + 1 AS source_row_number, ? AS batch_id '
            f'FROM read_parquet(?, file_row_number = true)')


def load_one(con, file_name, cet=None):
    if not FILE_PATTERN.fullmatch(file_name):
        raise ValueError(f'Tên file không hợp lệ: {file_name!r} (yellow_tripdata_YYYY-MM.parquet)')
    started = datetime.now()
    cet = cet or started
    batch_id = next_batch_id(con)

    ok, reason = download_file_with_retry(file_name)
    if not ok:
        write_log(con, PIPELINE_NAME, batch_id, file_name, cet, None, 0, 'FAILED',
                  f'DOWNLOAD: {reason}', started)
        raise RuntimeError(f'{file_name}: {reason}')

    path = os.path.join(RAW_DIR, file_name)
    rows_read, loaded, status, err = None, 0, 'SUCCESS', None
    try:
        rows_read = con.execute('SELECT count(*) FROM read_parquet(?)', [path]).fetchone()[0]
        insert_sql = build_insert_sql(con, path)
        con.begin()
        con.execute(f'DELETE FROM {TABLE} WHERE source_file_name = ?', [file_name])
        loaded = con.execute(insert_sql, [file_name, batch_id, path]).fetchone()[0]
        con.commit()
    except Exception as e:
        status, err, loaded = 'FAILED', str(e)[:2000], 0
        try:
            con.rollback()
        except Exception:
            pass

    write_log(con, PIPELINE_NAME, batch_id, file_name, cet, rows_read, loaded, status, err, started)
    read_txt = f'{rows_read:,}' if rows_read is not None else '?'
    print(f'[{status}] {file_name} | đọc {read_txt} | nạp {loaded:,} | batch {batch_id} | {err or ""}')
    if status == 'FAILED':
        raise RuntimeError(err)


def get_lset_month(con):
    """LSET = tháng cuối của dãy tháng liên tục nạp thành công, tính từ FIRST_MONTH."""
    done = {r[0] for r in con.execute(
        'SELECT DISTINCT source_file_name FROM control.etl_control '
        "WHERE pipeline_name = ? AND status = 'SUCCESS' AND rows_read = rows_loaded",
        [PIPELINE_NAME]).fetchall()}
    y, m = map(int, FIRST_MONTH.split('-'))
    last = None
    while f'yellow_tripdata_{y}-{m:02d}.parquet' in done:
        last = f'{y}-{m:02d}'
        m += 1
        if m > 12:
            y, m = y + 1, 1
    return last, done


@data_exporter
def load_trips_to_raw(*args, **kwargs):
    file_name = kwargs.get('file_name')
    year = kwargs.get('year')
    start_month = kwargs.get('start_month')
    end_month = kwargs.get('end_month')
    use_lset = to_bool(kwargs.get('use_lset', False))
    cet = datetime.now()

    con = connect()
    try:
        init_schema(con)

        if file_name and file_name != 'ALL':
            load_one(con, file_name, cet=cet)
            return

        lset_month, done = get_lset_month(con)
        print(f'[ETL CONTROL] LSET (tháng dữ liệu liên tục cuối) = {lset_month} | CET = {cet}')

        months = [f'{y}-{m:02d}' for y in (2024, 2025) for m in range(1, 13)]
        if year:
            months = [m for m in months if m.startswith(str(year))]
        if use_lset and not (start_month or year) and lset_month:
            start_month = lset_month  # file cuối đã SUCCESS sẽ bị bỏ qua; tháng sau được nạp
        if start_month:
            months = [m for m in months if m >= str(start_month)]
        if end_month:
            months = [m for m in months if m <= str(end_month)]

        files = [f'yellow_tripdata_{m}.parquet' for m in months]
        print(f'Số file cần kiểm tra: {len(files)}')

        failed = []
        for f in files:
            if f in done:
                print(f'[SKIP] đã SUCCESS: {f}')
                continue
            try:
                load_one(con, f, cet=cet)
            except Exception as e:
                print(f'[FILE FAILED] {f}: {e}')
                failed.append(f)

        print(f'=== TỔNG KẾT: {len(files)} file | lỗi: {len(failed)} {failed}')
        if failed:
            raise RuntimeError(f'Còn {len(failed)} file chưa nạp được: {failed}')
    finally:
        con.close()
