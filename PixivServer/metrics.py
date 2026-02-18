from prometheus_client import Counter, Gauge, Histogram, Info

# --- Server info ---
SERVER_INFO = Info("pixivutil_server", "PixivUtil Server build info")

# --- DB stat metrics (periodic) ---
DB_MEMBERS = Gauge("pixivutil_db_members_total", "Members in pixiv_master_member")
DB_ARTWORKS = Gauge("pixivutil_db_artworks_total", "Artworks in pixiv_master_image")
DB_PAGES = Gauge("pixivutil_db_pages_total", "Pages in pixiv_manga_image")
DB_TAGS = Gauge("pixivutil_db_tags_total", "Tags in pixiv_master_tag")

# --- Disk metrics (periodic) ---
DISK_DOWNLOADS_BYTES = Gauge("pixivutil_disk_downloads_bytes", "Bytes used by downloads directory")
DISK_DATABASE_BYTES = Gauge("pixivutil_disk_database_bytes", "Bytes used by SQLite database file(s)")

# --- OS system metrics (periodic) ---
SYS_CPU_PERCENT = Gauge("pixivutil_cpu_usage_percent", "CPU usage percent")
SYS_MEM_USED_BYTES = Gauge("pixivutil_memory_used_bytes", "Memory used bytes")
SYS_MEM_TOTAL_BYTES = Gauge("pixivutil_memory_total_bytes", "Memory total bytes")
SYS_DISK_USED_BYTES = Gauge("pixivutil_sys_disk_used_bytes", "Host disk used bytes (root filesystem)")
SYS_DISK_TOTAL_BYTES = Gauge("pixivutil_sys_disk_total_bytes", "Host disk total bytes (root filesystem)")

# --- Worker queue metrics (periodic) ---
QUEUE_DEPTH = Gauge("pixivutil_queue_depth", "Number of messages pending in the task queue")

# --- Request metrics (per-request via middleware) ---
HTTP_REQUESTS_TOTAL = Counter(
    "pixivutil_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_class"],
)
HTTP_REQUEST_DURATION = Histogram(
    "pixivutil_http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
)
HTTP_REQUEST_SIZE = Histogram(
    "pixivutil_http_request_size_bytes",
    "HTTP request body size in bytes",
    ["method", "endpoint"],
    buckets=[64, 256, 1_024, 4_096, 16_384],
)
HTTP_RESPONSE_SIZE = Histogram(
    "pixivutil_http_response_size_bytes",
    "HTTP response body size in bytes",
    ["method", "endpoint"],
    buckets=[256, 1_024, 16_384, 65_536, 1_048_576],
)
