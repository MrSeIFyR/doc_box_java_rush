$CONTAINER_ID = docker compose ps -q db

if ([string]::IsNullOrWhiteSpace($CONTAINER_ID)) {
    Write-Host "ERROR: container 'db' not found. Run: docker compose up --build" -ForegroundColor Red
    exit 1
}

Write-Host "Container ID: $CONTAINER_ID" -ForegroundColor Cyan

$DB_NAME = "docbox_db"
$DB_USER = "postgres"
$BACKUP_DIR = ".\backups"

if (-not (Test-Path $BACKUP_DIR)) {
    New-Item -ItemType Directory -Path $BACKUP_DIR | Out-Null
}

$TIMESTAMP = Get-Date -Format "yyyy-MM-dd_HHmmss"
$BACKUP_FILE = "backup_${TIMESTAMP}.sql"
$BACKUP_PATH = Join-Path $BACKUP_DIR $BACKUP_FILE
$BACKUP_IN_CONTAINER = "/backups/${BACKUP_FILE}"

Write-Host "Creating backup..." -ForegroundColor Cyan

$env:PGPASSWORD = "password"

try {
    docker exec -t $CONTAINER_ID pg_dump -U $DB_USER -d $DB_NAME -f $BACKUP_IN_CONTAINER
} catch {
    Write-Host "ERROR: pg_dump failed: $_" -ForegroundColor Red
    exit 1
} finally {
    Remove-Item Env:\PGPASSWORD
}

if (Test-Path $BACKUP_PATH) {
    $sizeKB = [math]::Round((Get-Item $BACKUP_PATH).Length / 1KB, 1)
    Write-Host "SUCCESS: $BACKUP_PATH ($sizeKB KB)" -ForegroundColor Green
} else {
    Write-Host "ERROR: backup file not found on host: $BACKUP_PATH" -ForegroundColor Red
    Write-Host "Check: volume '- ./backups:/backups' in compose.yaml for service 'db'" -ForegroundColor Yellow
    exit 1
}
