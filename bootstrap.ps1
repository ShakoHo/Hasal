function Add-EnvPath {
    # Get parameters
    param(
        [Parameter(Mandatory=$true)]
        [string] $Path,

        [ValidateSet('Machine', 'User', 'Session')]
        [string] $Container = 'Session'
    )
    
    # Do it for global Path (like SETX but no restriction over 1024 characters)
    if(!($env:Path -like "*$Path*")) {
        "[INFO] Adding $Path to system path!"
        reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /f /v Path /t REG_SZ /d "$env:Path;$Path;"
    } else {
        "[INFO] $Path is already in system path."
    }

    # Do it for current $env:Path
    if ($Container -ne 'Session') {
        $containerMapping = @{
            Machine = [EnvironmentVariableTarget]::Machine
            User = [EnvironmentVariableTarget]::User
        }
        $containerType = $containerMapping[$Container]

        $persistedPaths = [Environment]::GetEnvironmentVariable('Path', $containerType) -split ';'
        if ($persistedPaths -notcontains $Path) {
            $persistedPaths = $persistedPaths + $Path | where { $_ }
            [Environment]::SetEnvironmentVariable('Path', $persistedPaths -join ';', $containerType)
        }
    }

    $envPaths = $env:Path -split ';'
    if ($envPaths -notcontains $Path) {
        $envPaths = $envPaths + $Path | where { $_ }
        $env:Path = $envPaths -join ';'
    }
}

# back up the current environment variables
"$env:Path" | Out-File "Path-Backup-$(Get-Date -format yyyyMMddHHmmss).txt"

########################
#                      #
#  Install Chocolatey  #
#                      #
########################

# installation of Chocolatey package management
"[INFO] Installing Chocolatey"
If ($PSVersionTable.PSVersion.Major -Match "2") {
    iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
} Else {
    iwr https://chocolatey.org/install.ps1 -UseBasicParsing | iex
}
choco feature enable -n=allowGlobalConfirmation

########################
#                      #
#  Hasal Installation  #
#                      #
########################

# installation of tools
$tmp = & CMD /C curl --help >$null 2>&1
If ($lastexitcode -notmatch 0) {
    "[INFO] Installing Curl"
    choco install curl
    If ($lastexitcode -notmatch 0) {
        "[ERROR] There were problems when installing curl."
        Exit
    }
} Else {
    "[INFO] Curl found in current system. Not going to install it."
}

$tmp = & CMD /C git --help >$null 2>&1
If ($lastexitcode -notmatch 0) {
    "[INFO] Installing git"
    choco install git.install
    If ($lastexitcode -notmatch 0) {
        "[ERROR] There were problems when installing git."
        Exit
    }
    Add-EnvPath "C:\Program Files\Git\bin"
} Else {
    "[INFO] Git found in current system. Not going to install it."
}


# Install OBS Studio
If (Test-Path "C:\Program Files (x86)\obs-studio\bin\32bit\obs32.exe") {
    "[INFO] OBS had been installed."
} Else {
    "[INFO] Downloading OBS ..."
    pushd thirdParty
    If (Test-Path "OBS-Studio-18.0.1-Full.zip") {
        Remove-Item "OBS-Studio-18.0.1-Full.zip"
    }
    CMD /C curl -kLO https://github.com/jp9000/obs-studio/releases/download/18.0.1/OBS-Studio-18.0.1-Full.zip
    "[INFO] Installing OBS ..."
    Expand-Archive -LiteralPath OBS-Studio-18.0.1-Full.zip -DestinationPath "C:\Program Files (x86)\obs-studio"
    popd
    $FIRST_OBS = $TRUE
    "[INFO] OBS is installed."
}


# installation of Hasal prerequisite
$tmp = & CMD /C java -version >$null 2>&1
If ($lastexitcode -notmatch 0) {
    "[INFO] Installing Java 8 -version 8.0.144"
    choco install jre8
    If ($lastexitcode -notmatch 0) {
        "[ERROR] There were problems when installing jre8."
        Exit
    }
    $jre8 = cver jre8 -localonly | findstr jre8
    $version = $jre8.Split(' ')[1] -replace "(.*)\.(.*)", "`$1_`$2"
    Add-EnvPath "C:\Program Files\Java\jre1.$version\bin"
} Else {
    "[INFO] Java found in current system. Not going to install it."
}


$tmp = & CMD /C ffmpeg -help >$null 2>&1
If ($lastexitcode -notmatch 0) {
    "[INFO] Installing FFMPEG"
    choco install ffmpeg -version 3.2.2.20161219
    If ($lastexitcode -notmatch 0) {
        "[ERROR] There were problems when installing ffmpeg."
        Exit
    }
    Add-EnvPath "C:\ProgramData\chocolatey\lib\ffmpeg\tools\ffmpeg-3.2.2-win32-static\bin\"
} Else {
    "[INFO] FFMPEG found in current system. Not going to install it."
}

$tmp = & CMD /C conda -help >$null 2>&1
If ($lastexitcode -notmatch 0) {
    "[INFO] Installing MiniConda"
    choco install miniconda
    If ($lastexitcode -notmatch 0) {
        "[ERROR] There were problems when installing miniconda."
        Exit
    }
} Else {
    "[INFO] MiniConda found in current system. Not going to install it."
}

If (Test-Path C:\Miniconda2\) {
    $CondaPath="C:\Miniconda2"
} ElseIf (Test-Path "C:\Program Files\Miniconda2\") {
    $CondaPath="C:\Program Files\Miniconda2"
} Else {
    $CondaPath="C:\ProgramData\Miniconda2"
}

Add-EnvPath "$CondaPath\Scripts\"
Add-EnvPath "$CondaPath\"

"[INFO] Downloading VCForPython27.msi"
CMD /C curl -kLO https://download.microsoft.com/download/7/9/6/796EF2E4-801B-4FC4-AB28-B59FBF6D907B/VCForPython27.msi
"[INFO] Installing VCForPython27.msi"
msiexec /i VCForPython27.msi /qn /quiet /norestart
If ($lastexitcode -notmatch 0) {
    "[ERROR] There were problems when installing VCForPython27.msi"
    Exit
}
"[INFO] Removing VCForPython27.msi"
If (Test-Path "VCForPython27.msi") {
    Remove-Item VCForPython27.msi
}


# installation of browsers
"[INFO] Installing Chrome"
choco install googlechrome
If ($lastexitcode -notmatch 0) {
    "[ERROR] There were problems when installing Chrome"
    Exit
}

If (Test-Path "C:\Program Files\Google\Chrome\Application\") {
    Add-EnvPath "C:\Program Files\Google\Chrome\Application\"
} ElseIf (Test-Path "C:\Program Files (x86)\Google\Chrome\Application\") {
    Add-EnvPath "C:\Program Files (x86)\Google\Chrome\Application\"
}

"[INFO] Installing Firefox"
choco install firefox -y
If ($lastexitcode -notmatch 0) {
    "[ERROR] There were problems when installing Firefox"
    Exit
}

If (Test-Path "C:\Program Files\Mozilla Firefox") {
    Add-EnvPath "C:\Program Files\Mozilla Firefox"
} ElseIf (Test-Path "C:\Program Files (x86)\Mozilla Firefox") {
    Add-EnvPath "C:\Program Files (x86)\Mozilla Firefox"
}

# installation of sikuli
"[INFO] Installing SikuliX 1.1.0"
choco install sikulix
If ($lastexitcode -notmatch 0) {
    "[ERROR] There were problems when installing SikuliX"
    Exit
}

########################
#                      #
#     Hasal Setup      #
#                      #
########################

"[INFO] Creating Miniconda virtualenv (It might take some time to finish.)"
conda config --set always_yes yes --set changeps1 no
conda install psutil
conda create -q -n env-python python=2.7 numpy scipy nose pywin32 pip matplotlib==1.5.3 runipy==0.1.5

Copy-Item C:\ProgramData\chocolatey\lib\sikulix\content\* .\thirdParty\
Copy-Item .\scripts\runsikuli* .\thirdParty\

CMD /C "$CondaPath\envs\env-python\Scripts\pip" install mitmproxy
CMD /C "$CondaPath\envs\env-python\Scripts\pip" install thirdParty\opencv_python-2.4.13-cp27-cp27m-win32.whl
CMD /C "$CondaPath\envs\env-python\Scripts\pip" install thirdParty\opencv_python-2.4.13.2-cp27-cp27m-win_amd64.whl
CMD /C "$CondaPath\envs\env-python\Scripts\pip" install -r requirements.txt
CMD /C "$CondaPath\envs\env-python\Scripts\pip" install -r ejenti\requirements.txt
CMD /C certutil -p "" thirdParty\mitmproxy-ca-cert.p12
CMD /C "$CondaPath\envs\env-python\python" setup.py install
CMD /C "$CondaPath\envs\env-python\python" scripts\cv2_checker.py


########################
#                      #
#   User Interactions  #
#                      #
########################

# OBS License Agreement
IF ($FIRST_OBS) {
    If (Test-Path "C:\Program Files (x86)\obs-studio\bin\32bit\obs32.exe") {
        pushd "C:\Program Files (x86)\obs-studio\bin\32bit\"
        "[INFO] Launching OBS for License Agreement."
        ""
        "[INFO] If there is error message about missing MSVCP120.dll,"
        "[INFO] please install Visual C++ Redistributable Packages from https://www.microsoft.com/en-us/download/details.aspx?id=40784"
        "[INFO] ** Please CLOSE OBS after accepting License Agreement **"
        CMD /C obs32.exe
        popd
    } ELSE {
        "[WARN] Can not find OBS binary file."
    }
}

"[INFO] You will need to restart the computer so that the PATH will be effective"