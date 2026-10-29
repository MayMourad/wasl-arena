param([string]$Pptx, [string]$OutDir)
New-Item -ItemType Directory -Force $OutDir | Out-Null
$p = New-Object -ComObject PowerPoint.Application
$d = $p.Presentations.Open($Pptx, $true, $false, $false)
$d.Export($OutDir, "PNG", 1280, 720)
"SLIDES=" + $d.Slides.Count
$d.Close(); $p.Quit()
