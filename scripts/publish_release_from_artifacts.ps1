param(
    [string]$Owner = "OmniSwarmV1",
    [string]$Repo = "omni-swarm",
    [string]$Tag = "v0.1"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-GitHubBasicHeaders {
    $req = "protocol=https`nhost=github.com`n`n"
    $res = $req | git credential fill
    $userLine = ($res -split "`n" | Where-Object { $_ -like "username=*" } | Select-Object -First 1)
    $passLine = ($res -split "`n" | Where-Object { $_ -like "password=*" } | Select-Object -First 1)
    if (-not $userLine -or -not $passLine) {
        throw "GitHub credentials not found in git credential store."
    }

    $user = $userLine.Substring(9)
    $pass = $passLine.Substring(9)
    $pair = "${user}:${pass}"
    $basic = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($pair))

    $headers = @{
        Authorization = "Basic $basic"
        "User-Agent" = "omniswarm-cli"
        Accept = "application/vnd.github+json"
    }

    return @{
        Headers = $headers
        Basic = $basic
    }
}

function Download-Artifacts {
    param(
        [hashtable]$Headers,
        [string]$TempRoot
    )

    $artifacts = @(
        @{
            Name = "omni-swarm-node-macos"
            Url = "https://api.github.com/repos/$Owner/$Repo/actions/artifacts/5578025729/zip"
            Out = "omni-swarm-node-macos"
        },
        @{
            Name = "omni-swarm-node-linux"
            Url = "https://api.github.com/repos/$Owner/$Repo/actions/artifacts/5578044957/zip"
            Out = "omni-swarm-node-linux"
        },
        @{
            Name = "omni-swarm-node-windows.exe"
            Url = "https://api.github.com/repos/$Owner/$Repo/actions/artifacts/5578059443/zip"
            Out = "omni-swarm-node-windows.exe"
        }
    )

    $assetFiles = @()
    foreach ($a in $artifacts) {
        $zipPath = Join-Path $TempRoot ($a.Name + ".zip")
        Invoke-WebRequest -Uri $a.Url -Headers $Headers -OutFile $zipPath

        $extractDir = Join-Path $TempRoot $a.Name
        Expand-Archive -Path $zipPath -DestinationPath $extractDir

        $candidate = Get-ChildItem -Recurse -Path $extractDir -File |
            Where-Object { $_.Name -eq "omni-swarm-node" -or $_.Name -eq "omni-swarm-node.exe" } |
            Select-Object -First 1

        if (-not $candidate) {
            throw "No binary found in artifact: $($a.Name)"
        }

        $destPath = Join-Path $TempRoot ("asset_" + $a.Out)
        Copy-Item -Path $candidate.FullName -Destination $destPath -Force
        $assetFiles += @{ Name = $a.Out; Path = $destPath }
    }

    $claimSource = Join-Path (Get-Location) "token/claim_flow.md"
    $claimDest = Join-Path $TempRoot "claim_guide.md"
    Copy-Item -Path $claimSource -Destination $claimDest -Force
    $assetFiles += @{ Name = "claim_guide.md"; Path = $claimDest }

    return ,$assetFiles
}

function Get-OrCreateRelease {
    param(
        [hashtable]$Headers
    )

    try {
        return Invoke-RestMethod -Uri "https://api.github.com/repos/$Owner/$Repo/releases/tags/$Tag" -Headers $Headers
    } catch {
        $body = @{
            tag_name = $Tag
            target_commitish = "main"
            name = "OmniSwarm v0.1 - Ilk AI Tarafindan Yayinlandi - 19 Subat 2026"
            body = "Local Core + IPFS Swarm + Self-Evolving + Royalty + Claimable Airdrop"
            draft = $false
            prerelease = $false
        } | ConvertTo-Json

        return Invoke-RestMethod -Method Post -Uri "https://api.github.com/repos/$Owner/$Repo/releases" -Headers $Headers -Body $body -ContentType "application/json"
    }
}

function Upload-Assets {
    param(
        [hashtable]$Headers,
        [string]$Basic,
        [object]$Release,
        [array]$AssetFiles
    )

    $uploadBase = ($Release.upload_url -replace "\{\?name,label\}", "")
    $existing = Invoke-RestMethod -Uri "https://api.github.com/repos/$Owner/$Repo/releases/$($Release.id)/assets" -Headers $Headers

    foreach ($f in $AssetFiles) {
        $match = $existing | Where-Object { $_.name -eq $f.Name } | Select-Object -First 1
        if ($match) {
            Invoke-RestMethod -Method Delete -Uri "https://api.github.com/repos/$Owner/$Repo/releases/assets/$($match.id)" -Headers $Headers | Out-Null
        }
    }

    foreach ($f in $AssetFiles) {
        $uploadUrl = "${uploadBase}?name=$([Uri]::EscapeDataString($f.Name))"
        $bytes = [System.IO.File]::ReadAllBytes($f.Path)
        Invoke-RestMethod -Method Post -Uri $uploadUrl -Headers @{
            Authorization = "Basic $Basic"
            "User-Agent" = "omniswarm-cli"
            Accept = "application/vnd.github+json"
            "Content-Type" = "application/octet-stream"
        } -Body $bytes | Out-Null
    }
}

$auth = Get-GitHubBasicHeaders
$tmpRoot = Join-Path $env:TEMP ("omni_release_assets_" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tmpRoot | Out-Null

$assetFiles = Download-Artifacts -Headers $auth.Headers -TempRoot $tmpRoot
$release = Get-OrCreateRelease -Headers $auth.Headers
Upload-Assets -Headers $auth.Headers -Basic $auth.Basic -Release $release -AssetFiles $assetFiles

$finalRelease = Invoke-RestMethod -Uri "https://api.github.com/repos/$Owner/$Repo/releases/tags/$Tag" -Headers $auth.Headers
Write-Output ("release_url=" + $finalRelease.html_url)
foreach ($asset in $finalRelease.assets) {
    Write-Output ("asset=" + $asset.name + " -> " + $asset.browser_download_url)
}
