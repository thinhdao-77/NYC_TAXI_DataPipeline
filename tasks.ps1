<#
.SYNOPSIS
  Lệnh thường dùng của dự án. Chạy từ thư mục gốc repo.

.EXAMPLE
  .\tasks.ps1 up
  .\tasks.ps1 dbt-build
  .\tasks.ps1 profile 03_profile_by_vendor.sql
  .\tasks.ps1 qa smoke
#>
param(
    [Parameter(Position = 0)]
    [ValidateSet('help', 'up', 'down', 'ps', 'logs', 'shell', 'sql', 'download-raw',
                 'ingest-zones', 'ingest', 'profile', 'dbt-deps', 'dbt-run', 'dbt-test',
                 'dbt-build', 'qa', 'prune-branches')]
    [string]$Task = 'help',

    [Parameter(Position = 1)]
    [string]$Arg
)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
# PowerShell 5.1 mặc định pipe sang chương trình ngoài bằng ASCII, làm hỏng chữ có dấu
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)

# Chạy SQL (đọc từ stdin) trên file DuckDB trong container Mage, chế độ chỉ đọc.
# DuckDB chỉ cho một tiến trình ghi: lệnh sẽ lỗi nếu dbt/Mage đang ghi vào file.
$DuckDbQuery = "import duckdb, os, sys; con = duckdb.connect(os.environ['DUCKDB_PATH'], read_only=True); con.sql(sys.stdin.read()).show(max_rows=200)"
function Invoke-DuckDb([string]$Sql) {
    $Sql | docker compose exec -T mage python -c $DuckDbQuery
}

# Chạy pipeline Mage không cần giao diện. PowerShell 5.1 làm mất dấu " khi truyền cho
# chương trình ngoài, nên JSON phải escape thành \".
function Invoke-MagePipeline([string]$Pipeline, [string]$VarsJson) {
    $cmd = @('compose', 'exec', '-T', 'mage', 'mage', 'run', '/home/src/mage', $Pipeline)
    if ($VarsJson) { $cmd += @('--runtime-vars', ($VarsJson -replace '"', '\"')) }
    & docker @cmd
}

# dbt chạy trong container Mage
function Invoke-Dbt([string[]]$DbtArgs) {
    docker compose exec -T mage dbt @DbtArgs --project-dir /home/src/dbt --profiles-dir /home/src/dbt
}

switch ($Task) {
    'help' {
        Write-Output @'
Tasks:
  up | down | ps | logs [service]   Quản lý Docker Compose
  shell                             Mở bash trong container Mage
  sql "<câu SQL>"                   Truy vấn file DuckDB (chỉ đọc)
  download-raw                      Tải trước Parquet vào data/raw (tùy chọn)
  ingest-zones                      Nạp Taxi Zone Lookup vào raw.taxi_zone_lookup
  ingest [file | ALL | JSON]        Nạp chuyến đi vào raw.yellow_tripdata, mặc định ALL
                                    vd: ingest yellow_tripdata_2024-01.parquet
                                        ingest '{"file_name":"ALL","year":2024}'
  profile <file.sql>                Chạy một truy vấn trong sql/profiling
  dbt-deps | dbt-run | dbt-test | dbt-build [selector]
                                    Chạy dbt trong container Mage (vd: dbt-build dim_vendor)
  qa [smoke|deep|all]               Chạy runner QA chỉ đọc (mặc định smoke)
  prune-branches                    Xóa nhánh local mà nhánh remote đã bị xóa (sau khi merge PR)
'@
    }
    'up'           { docker compose up -d --build; docker compose ps }
    'down'         { docker compose down }
    'ps'           { docker compose ps }
    'logs'         { if ($Arg) { docker compose logs -f $Arg } else { docker compose logs -f } }
    'shell'        { docker compose exec mage bash }
    'sql' {
        if (-not $Arg) { throw 'Cần câu SQL, vd: .\tasks.ps1 sql "show all tables"' }
        Invoke-DuckDb $Arg
    }
    'download-raw' { powershell -ExecutionPolicy Bypass -File data\download_raw.ps1 }
    'ingest-zones' { Invoke-MagePipeline 'ingest_zone_lookup' $null }
    'ingest' {
        $vars = if (-not $Arg) { '{"file_name": "ALL"}' }
                elseif ($Arg.TrimStart().StartsWith('{')) { $Arg }
                else { '{"file_name": "' + $Arg + '"}' }
        Invoke-MagePipeline 'ingest_yellow_trips' $vars
    }
    'profile' {
        if (-not $Arg) { throw 'Cần tên file, vd: .\tasks.ps1 profile 03_profile_by_vendor.sql' }
        $file = Join-Path 'sql\profiling' $Arg
        if (-not (Test-Path $file)) { throw "Không tìm thấy $file" }
        Invoke-DuckDb ((Get-Content $file -Raw -Encoding UTF8))
    }
    'dbt-deps'  { Invoke-Dbt @('deps') }
    'dbt-run'   { if ($Arg) { Invoke-Dbt @('run', '--select', $Arg) } else { Invoke-Dbt @('run') } }
    'dbt-test'  { if ($Arg) { Invoke-Dbt @('test', '--select', $Arg) } else { Invoke-Dbt @('test') } }
    'dbt-build' { if ($Arg) { Invoke-Dbt @('build', '--select', $Arg) } else { Invoke-Dbt @('build') } }
    'qa' {
        $suite = if ($Arg) { $Arg } else { 'smoke' }
        python tests\run_quality_tests.py --suite $suite
    }
    'prune-branches' {
        git fetch --prune origin
        $current = git branch --show-current
        $gone = git branch -vv | Where-Object { $_ -match '\[origin/[^\]]+: gone\]' } |
            ForEach-Object { ($_.TrimStart('*', ' ') -split '\s+')[0] }
        if (-not $gone) { Write-Output 'Không có nhánh local nào cần dọn.'; return }
        foreach ($b in $gone) {
            if ($b -eq $current) { Write-Output "Bỏ qua $b (đang checkout; chuyển sang main trước)"; continue }
            # -d (không phải -D): git từ chối xóa nếu nhánh có commit chưa được merge
            git branch -d $b
        }
    }
}
