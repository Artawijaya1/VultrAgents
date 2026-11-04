param(
    [Parameter(Mandatory=$true)][string]$RepoRoot
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path $RepoRoot).Path
$target = Join-Path $repo 'Agents'
if (-not (Test-Path $target -PathType Container)) {
    throw "Folder Agents tidak ditemukan pada $repo. Pastikan RepoRoot adalah root VultrAgents."
}
$source = Join-Path $PSScriptRoot 'Agents'
if (-not (Test-Path $source -PathType Container)) {
    throw "Folder paket Agents tidak ditemukan di lokasi script."
}
$files = Get-ChildItem $source -Recurse -File
$created = 0
$skipped = 0
foreach ($file in $files) {
    $relative = $file.FullName.Substring($source.Length).TrimStart('\','/')
    $dest = Join-Path $target $relative
    if (Test-Path $dest) {
        Write-Host "SKIP (existing): Agents/$relative" -ForegroundColor Yellow
        $skipped++
        continue
    }
    New-Item -Force -ItemType Directory (Split-Path $dest -Parent) | Out-Null
    Copy-Item $file.FullName $dest
    Write-Host "CREATED: Agents/$relative" -ForegroundColor Green
    $created++
}
Write-Host "Selesai. Baru: $created, dilewati: $skipped. Tidak ada file existing yang ditimpa."
Write-Host "Berikutnya: cd `"$target`"; python -m unittest discover -s tests -v"
