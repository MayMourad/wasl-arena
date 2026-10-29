param([string]$Docx, [string]$Pdf)
$w = New-Object -ComObject Word.Application; $w.Visible = $false
$d = $w.Documents.Open($Docx)
$d.Repaginate()
$pages = $d.ComputeStatistics(2)
$d.ExportAsFixedFormat($Pdf, 17)
$d.Close($false); $w.Quit()
"PAGES=$pages"
