# Convierte el .docx a PDF automatizando Word.
#
# Se usa Word y no un motor propio porque los indices del documento son campos
# TOC: hay que abrirlos, actualizarlos y repaginar para que los numeros de pagina
# del PDF coincidan con los del .docx entregado. Se actualiza dos veces porque la
# primera pasada cambia la paginacion y deja los numeros del indice desfasados.

param(
    [Parameter(Mandatory = $true)][string]$Docx
)

$ErrorActionPreference = "Stop"
$Docx = (Resolve-Path $Docx).Path
$Pdf = [System.IO.Path]::ChangeExtension($Docx, ".pdf")

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0

try {
    $doc = $word.Documents.Open($Docx, $false, $false)

    foreach ($pasada in 1..2) {
        $doc.Fields.Update() | Out-Null
        foreach ($toc in $doc.TablesOfContents) { $toc.Update() | Out-Null }
        foreach ($tof in $doc.TablesOfFigures) { $tof.Update() | Out-Null }
        $doc.Repaginate()
    }

    $doc.Save()

    # 17 = wdExportFormatPDF, 0 = optimizar para impresion,
    # 1 = generar marcadores del PDF a partir de los titulos.
    $doc.ExportAsFixedFormat($Pdf, 17, $false, 0, 0, 0, 0, 0, $true, $true, 1)

    "Paginas: $($doc.ComputeStatistics(2))"
    $doc.Close(0)
}
finally {
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}

"PDF -> $Pdf"
