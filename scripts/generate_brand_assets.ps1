Add-Type -AssemblyName System.Drawing

$root = Split-Path -Parent $PSScriptRoot
$assets = Join-Path $root 'assets'
New-Item -ItemType Directory -Force -Path $assets | Out-Null

function New-LogoBitmap([int]$size) {
    $bitmap = [System.Drawing.Bitmap]::new($size, $size)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $graphics.Clear([System.Drawing.ColorTranslator]::FromHtml('#122D00'))
    $scale = $size / 64.0
    $lime = [System.Drawing.ColorTranslator]::FromHtml('#B5E000')
    $cream = [System.Drawing.ColorTranslator]::FromHtml('#ECEFCE')
    $ring = [System.Drawing.Pen]::new($lime, 4 * $scale)
    $ring.Alignment = [System.Drawing.Drawing2D.PenAlignment]::Inset
    $graphics.DrawEllipse($ring, 8 * $scale, 8 * $scale, 48 * $scale, 48 * $scale)
    $points = @(
        [System.Drawing.PointF]::new(32*$scale,19.2*$scale),
        [System.Drawing.PointF]::new(42.1*$scale,26.5*$scale),
        [System.Drawing.PointF]::new(38.2*$scale,38.4*$scale),
        [System.Drawing.PointF]::new(25.8*$scale,38.4*$scale),
        [System.Drawing.PointF]::new(21.9*$scale,26.5*$scale)
    )
    $brush = [System.Drawing.SolidBrush]::new($lime)
    $graphics.FillPolygon($brush, $points)
    $seam = [System.Drawing.Pen]::new($cream, [Math]::Max(1.2, 2.7*$scale))
    $seam.StartCap = $seam.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
    $ends = @(@(32,12.2),@(48.9,24.5),@(42.6,44.5),@(21.4,44.5),@(15.1,24.5))
    for ($i=0; $i -lt 5; $i++) {
        $graphics.DrawLine($seam, $points[$i], [System.Drawing.PointF]::new($ends[$i][0]*$scale,$ends[$i][1]*$scale))
    }
    $ring.Dispose(); $seam.Dispose(); $brush.Dispose(); $graphics.Dispose()
    return $bitmap
}

foreach ($item in @(@(32,'favicon-32.png'),@(180,'apple-touch-icon.png'),@(192,'icon-192.png'),@(512,'icon-512.png'))) {
    $image = New-LogoBitmap $item[0]
    $image.Save((Join-Path $root $item[1]), [System.Drawing.Imaging.ImageFormat]::Png)
    $image.Dispose()
}

# ICO compatível com navegadores antigos, contendo a versão PNG de 32 px.
$png = [System.IO.File]::ReadAllBytes((Join-Path $root 'favicon-32.png'))
$stream = [System.IO.File]::Create((Join-Path $root 'favicon.ico'))
$writer = [System.IO.BinaryWriter]::new($stream)
$writer.Write([uint16]0); $writer.Write([uint16]1); $writer.Write([uint16]1)
$writer.Write([byte]32); $writer.Write([byte]32); $writer.Write([byte]0); $writer.Write([byte]0)
$writer.Write([uint16]1); $writer.Write([uint16]32); $writer.Write([uint32]$png.Length); $writer.Write([uint32]22)
$writer.Write($png); $writer.Dispose(); $stream.Dispose()

$social = [System.Drawing.Bitmap]::new(1200, 630)
$g = [System.Drawing.Graphics]::FromImage($social)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.Clear([System.Drawing.ColorTranslator]::FromHtml('#122D00'))
$linePen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(18,255,255,255), 2)
$g.DrawLine($linePen, 600, 0, 600, 630); $g.DrawEllipse($linePen, 455, 170, 290, 290)
$mark = New-LogoBitmap 250
$g.DrawImage($mark, 108, 190, 250, 250)
$white = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::White)
$limeBrush = [System.Drawing.SolidBrush]::new([System.Drawing.ColorTranslator]::FromHtml('#B5E000'))
$creamBrush = [System.Drawing.SolidBrush]::new([System.Drawing.ColorTranslator]::FromHtml('#ECEFCE'))
$fontFamily = [System.Drawing.FontFamily]::GenericSansSerif
$titleFont = [System.Drawing.Font]::new($fontFamily, 76, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
$subFont = [System.Drawing.Font]::new($fontFamily, 30, [System.Drawing.FontStyle]::Regular, [System.Drawing.GraphicsUnit]::Pixel)
$g.DrawString('golguess', $titleFont, $white, 414, 228)
$g.DrawString('.', $titleFont, $limeBrush, 748, 228)
$g.DrawString('DESAFIO DIÁRIO DE FUTEBOL', $subFont, $creamBrush, 419, 328)
$social.Save((Join-Path $assets 'golguess-social.png'), [System.Drawing.Imaging.ImageFormat]::Png)
$linePen.Dispose(); $mark.Dispose(); $white.Dispose(); $limeBrush.Dispose(); $creamBrush.Dispose(); $titleFont.Dispose(); $subFont.Dispose(); $g.Dispose(); $social.Dispose()

Write-Output 'Brand assets generated.'
