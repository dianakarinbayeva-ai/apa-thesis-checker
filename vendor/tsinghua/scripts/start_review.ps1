param(
  [string]$Docx = "",
  [string]$Pdf = "",
  [string]$OutputDir = "guide_checker/output"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

$args = @(
  "-X", "utf8",
  "-m", "guide_checker.cli.run_full_review",
  "--output-dir", $OutputDir
)

if ($Docx) {
  $args += @("--docx", $Docx)
}

if ($Pdf) {
  $args += @("--pdf", $Pdf)
}

& python @args
