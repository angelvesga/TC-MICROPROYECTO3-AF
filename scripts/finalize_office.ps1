# Abre los entregables con Microsoft Office para actualizar la tabla de contenido
# (Word) y recalcular las formulas (Excel). Opcionalmente exporta PDF de revisión.
# Uso: powershell -ExecutionPolicy Bypass -File scripts/finalize_office.ps1 [-PdfDir <carpeta>]
param([string]$PdfDir = "")
$root = Split-Path -Parent $PSScriptRoot

$word = New-Object -ComObject Word.Application
$word.Visible = $false; $word.DisplayAlerts = 0
foreach ($name in 'documento_tecnico', 'manual_usuario') {
    $doc = $word.Documents.Open("$root\output\word\$name.docx")
    $doc.Fields.Update() | Out-Null
    foreach ($toc in $doc.TablesOfContents) { $toc.Update() }
    $doc.Save()
    if ($PdfDir) { $doc.ExportAsFixedFormat("$PdfDir\$name.pdf", 17) }
    "$name.docx: " + $doc.ComputeStatistics(2) + " paginas"
    $doc.Close()
}
$word.Quit()

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false; $excel.DisplayAlerts = $false
$book = $excel.Workbooks.Open("$root\output\excel\matriz_pruebas.xlsx")
$excel.CalculateFull(); $book.Save()
if ($PdfDir) { $book.ExportAsFixedFormat(0, "$PdfDir\matriz.pdf") }
"matriz_pruebas.xlsx: recalculado"
$book.Close(); $excel.Quit()
