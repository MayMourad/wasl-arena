param([string]$Docx, [string]$OutDir)
Add-Type -AssemblyName System.Drawing
New-Item -ItemType Directory -Force $OutDir | Out-Null
$w = New-Object -ComObject Word.Application; $w.Visible = $true
$d = $w.Documents.Open($Docx); $d.Repaginate()
$n = $d.ComputeStatistics(2)
for ($i = 1; $i -le $n; $i++) {
  $pg = $d.ActiveWindow.ActivePane.Pages.Item($i)
  $bytes = $pg.EnhMetaFileBits
  $ms = New-Object IO.MemoryStream(,$bytes)
  $img = [System.Drawing.Image]::FromStream($ms)
  $bmp = New-Object System.Drawing.Bitmap 1000, 1414
  $g = [System.Drawing.Graphics]::FromImage($bmp); $g.Clear([System.Drawing.Color]::White)
  $g.InterpolationMode = 'HighQualityBicubic'; $g.DrawImage($img, 0, 0, 1000, 1414)
  $bmp.Save("$OutDir\p$i.png", [System.Drawing.Imaging.ImageFormat]::Png)
}
$d.Close($false); $w.Quit(); "PAGES=$n"
