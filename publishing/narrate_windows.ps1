param([Parameter(Mandatory=$true)][string]$Manifest)
$ErrorActionPreference = 'Stop'
$jobs = Get-Content -LiteralPath $Manifest -Raw -Encoding UTF8 | ConvertFrom-Json
$narrator = New-Object -ComObject SAPI.SpVoice
try {
    $voices = $narrator.GetVoices()
    for ($i = 0; $i -lt $voices.Count; $i++) {
        if ($voices.Item($i).GetDescription() -like '*Zira*') {
            $narrator.Voice = $voices.Item($i)
            break
        }
    }
    $narrator.Rate = -1
    foreach ($job in $jobs) {
        if (Test-Path -LiteralPath $job.wav) { continue }
        $stream = New-Object -ComObject SAPI.SpFileStream
        try {
            $stream.Open($job.wav, 3, $false)
            $narrator.AudioOutputStream = $stream
            $narrator.Speak($job.text) | Out-Null
        }
        finally {
            $stream.Close()
            [System.Runtime.InteropServices.Marshal]::ReleaseComObject($stream) | Out-Null
        }
        Write-Output ('Narrated ' + [System.IO.Path]::GetFileName($job.wav))
    }
}
finally {
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($narrator) | Out-Null
}
