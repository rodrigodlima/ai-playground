# =============================================================================
# run_test.ps1
#
# Token benchmark runner for Windows native (PowerShell + Git Bash).
#
# Usage:
#   .\scripts\run_test.ps1 -Variant <variant>
#
# Variants:
#   lf          LF line endings, no BOM   (baseline)
#   crlf        CRLF line endings, no BOM
#   lf_bom      LF line endings, UTF-8 BOM
#   crlf_bom    CRLF line endings, UTF-8 BOM
#
# Prerequisites:
#   - claude CLI installed and in PATH (native Windows install)
#   - python or python3 in PATH
#   - Variants generated: python scripts\generate_variants.py
#
# Example:
#   .\scripts\run_test.ps1 -Variant lf
#   .\scripts\run_test.ps1 -Variant crlf_bom
# =============================================================================

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("lf", "crlf", "lf_bom", "crlf_bom")]
    [string]$Variant
)

$ErrorActionPreference = "Stop"

# ── Paths ─────────────────────────────────────────────────────────────────────
$ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir     = Split-Path -Parent $ScriptDir
$VariantsDir = Join-Path $RootDir "variants"
$ResultsDir  = Join-Path $RootDir "results"
$TestProject = Join-Path $RootDir "test_project"

# ── Validate variant file ─────────────────────────────────────────────────────
$VariantFile = Join-Path $VariantsDir "claude_$Variant.md"
if (-not (Test-Path $VariantFile)) {
    Write-Error "Variant file not found: $VariantFile`nRun first: python scripts\generate_variants.py"
    exit 1
}

# ── Python command (Windows may use 'python' instead of 'python3') ────────────
$PythonCmd = if (Get-Command python3 -ErrorAction SilentlyContinue) { "python3" } else { "python" }

# ── Metadata ──────────────────────────────────────────────────────────────────
$EnvName   = "windows_native"
$OsInfo    = [System.Environment]::OSVersion.VersionString
$Timestamp = (Get-Date -Format "yyyyMMddTHHmmssZ")
$ResultFile = Join-Path $ResultsDir "${EnvName}_${Variant}_${Timestamp}.json"

# File metadata
$FileInfo  = Get-Item $VariantFile
$FileBytes = $FileInfo.Length
$LineCount = (Get-Content $VariantFile -Raw).Split("`n").Count - 1

# Check BOM
$Bytes3    = [System.IO.File]::ReadAllBytes($VariantFile) | Select-Object -First 3
$HasBOM    = ($Bytes3[0] -eq 0xEF -and $Bytes3[1] -eq 0xBB -and $Bytes3[2] -eq 0xBF)

# Check CRLF
$RawContent = [System.IO.File]::ReadAllText($VariantFile)
$HasCRLF   = $RawContent.Contains("`r`n")

# Create dirs and copy variant
New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null
New-Item -ItemType Directory -Force -Path $TestProject | Out-Null
Copy-Item $VariantFile (Join-Path $TestProject "CLAUDE.md") -Force

Write-Host "========================================================"
Write-Host "  Claude Code Token Benchmark"
Write-Host "========================================================"
Write-Host "  Environment  : $EnvName"
Write-Host "  Variant      : $Variant"
Write-Host "  File size    : $FileBytes bytes"
Write-Host "  Lines        : $LineCount"
Write-Host "  Has BOM      : $HasBOM"
Write-Host "  Has CRLF     : $HasCRLF"
Write-Host "  Timestamp    : $Timestamp"
Write-Host "========================================================"
Write-Host ""

# ── Run claude and measure time ───────────────────────────────────────────────
$Prompt = "Respond with exactly one word: READY"

Write-Host "  Prompt : $Prompt"
Write-Host "  Running..."
Write-Host ""

# Capture timestamp before run (epoch seconds)
$BeforeTS = [int][double]::Parse((Get-Date -UFormat %s))

$StopWatch = [System.Diagnostics.Stopwatch]::StartNew()

Push-Location $TestProject
try {
    $ClaudeOutput = & claude --print $Prompt 2>&1
} finally {
    Pop-Location
}

$StopWatch.Stop()
$DurationSec = [math]::Round($StopWatch.Elapsed.TotalSeconds, 3)

Write-Host "  Claude output : $ClaudeOutput"
Write-Host "  Duration      : ${DurationSec}s"
Write-Host ""

# ── Parse token usage ─────────────────────────────────────────────────────────
Write-Host "  Parsing session token usage..."

$ParseScript = Join-Path $ScriptDir "parse_session.py"
$TokensJson  = & $PythonCmd $ParseScript --after $BeforeTS | Out-String

$Tokens = $TokensJson | ConvertFrom-Json

if ($Tokens.PSObject.Properties["error"]) {
    Write-Warning "Could not parse session file: $($Tokens.error)"
    $InputTokens  = 0; $OutputTokens = 0
    $CacheCreate  = 0; $CacheRead    = 0
    $TotalTokens  = 0; $SessionFile  = "unknown"
} else {
    $InputTokens  = $Tokens.input_tokens
    $OutputTokens = $Tokens.output_tokens
    $CacheCreate  = $Tokens.cache_creation_tokens
    $CacheRead    = $Tokens.cache_read_tokens
    $TotalTokens  = $Tokens.total_tokens
    $SessionFile  = $Tokens.session_file
}

Write-Host ""
Write-Host "  ┌─────────────────────────────────┐"
Write-Host "  │  Token Summary                  │"
Write-Host "  ├─────────────────────────────────┤"
Write-Host ("  │  {0,-20} : {1,8}  │" -f "Input tokens",   $InputTokens)
Write-Host ("  │  {0,-20} : {1,8}  │" -f "Output tokens",  $OutputTokens)
Write-Host ("  │  {0,-20} : {1,8}  │" -f "Cache creation", $CacheCreate)
Write-Host ("  │  {0,-20} : {1,8}  │" -f "Cache read",     $CacheRead)
Write-Host ("  │  {0,-20} : {1,8}  │" -f "Total",          $TotalTokens)
Write-Host "  └─────────────────────────────────┘"
Write-Host ""

# ── Save result ───────────────────────────────────────────────────────────────
$Result = [ordered]@{
    environment    = $EnvName
    os_info        = $OsInfo
    timestamp      = $Timestamp
    variant        = $Variant
    file_metadata  = [ordered]@{
        size_bytes = $FileBytes
        line_count = $LineCount
        has_bom    = $HasBOM
        has_crlf   = $HasCRLF
    }
    duration_seconds = $DurationSec
    claude_output    = "$ClaudeOutput"
    tokens           = [ordered]@{
        input          = $InputTokens
        output         = $OutputTokens
        cache_creation = $CacheCreate
        cache_read     = $CacheRead
        total          = $TotalTokens
    }
    session_file     = $SessionFile
}

$Result | ConvertTo-Json -Depth 5 | Set-Content $ResultFile -Encoding UTF8
Write-Host "  Result saved : $ResultFile"
Write-Host ""
Write-Host "  Next: run with another variant, then analyze:"
Write-Host "  python scripts\analyze_results.py"
