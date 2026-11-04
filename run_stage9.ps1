param(
    [string]$Repo = $PSScriptRoot,
    [ValidateSet('plan','apply','test','start','status','deploy','all')]
    [string]$Mode = 'all',
    [switch]$SkipPull,
    [switch]$SkipInstall,
    [switch]$NoPrompt,
    [ValidateSet('http','mock')]
    [string]$DataMode = 'http',
    [string]$Domain = '',
    [string]$PoId = 'PO-001'
)
$ErrorActionPreference = 'Stop'
$scriptPath = Join-Path $PSScriptRoot 'procureguard_stage9.py'
if (-not (Test-Path $scriptPath)) { throw 'procureguard_stage9.py harus berada di folder yang sama dengan run_stage9.ps1' }
$cmd = Get-Command 'py.exe' -ErrorAction SilentlyContinue
if ($cmd) {
    $pythonCmd = 'py.exe'
    $pyArgs = @('-3.11')
} else {
    $pythonCmd = 'python.exe'
    $pyArgs = @()
}
$argsForScript = @($scriptPath, '--repo', $Repo, '--mode', $Mode, '--data-mode', $DataMode, '--po-id', $PoId)
if ($SkipPull) { $argsForScript += '--skip-pull' }
if ($SkipInstall) { $argsForScript += '--skip-install' }
if ($NoPrompt) { $argsForScript += '--no-prompt' }
if ($Domain) { $argsForScript += @('--domain', $Domain) }
Write-Host 'ProcureGuard Stage 9: Git, Backend, Frontend, Agent URL, Integrasi, Vultr readiness' -ForegroundColor Cyan
& $pythonCmd @pyArgs @argsForScript
if ($LASTEXITCODE -ne 0) { throw "Stage 9 selesai dengan temuan FAIL; lihat LAPORAN_STAGE9.md (exit=$LASTEXITCODE)." }
