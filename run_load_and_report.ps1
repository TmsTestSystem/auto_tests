Param(
  [int]$Users = 100,
  [int]$SpawnRate = 50,
  [int]$DurationSec = 60
)

$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

# Create timestamped reports directory
$ts = Get-Date -Format 'yyyyMMdd_HHmmss'
$out = Join-Path $here "reports\$ts"
New-Item -ItemType Directory -Path $out -Force | Out-Null

# Optional: base URL can be overridden via environment, otherwise locustfile default is used
# $env:BASE_URL = $env:BASE_URL

# Run Locust and save its HTML report into the same folder
locust -f locustfile.py --headless -u $Users -r $SpawnRate -t ${DurationSec}s --only-summary --html (Join-Path $out 'locust_report.html')

# Generate our HTML+CSV report into the same folder
$env:REPORT_DIR = $out
python .\compare_jobs_vs_events.py | Out-Host

Write-Host "Done. Reports: $out" -ForegroundColor Green

