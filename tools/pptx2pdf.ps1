param([string]$Pptx, [string]$Pdf)
$p = New-Object -ComObject PowerPoint.Application
$d = $p.Presentations.Open($Pptx, $true, $false, $false)
$d.SaveAs($Pdf, 32)   # ppSaveAsPDF
"SLIDES=" + $d.Slides.Count
$d.Close(); $p.Quit()
