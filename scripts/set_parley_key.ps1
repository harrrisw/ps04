# Run from the terminal that will launch the pipeline. The key is never written
# into a file, command history, project configuration, or pipeline artifact.
$parleySecret = Read-Host 'Paste your MIT Parley API key (input hidden)' -AsSecureString
$parleyPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($parleySecret)
try {
    $env:PARLEY_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($parleyPointer)
}
finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($parleyPointer)
    $parleySecret.Dispose()
    Remove-Variable parleySecret, parleyPointer
}
if ([string]::IsNullOrWhiteSpace($env:PARLEY_API_KEY)) {
    throw 'No key entered. Run this helper again before starting the pipeline.'
}
Write-Host 'PARLEY_API_KEY is set for this terminal session. No API request has been made.'
