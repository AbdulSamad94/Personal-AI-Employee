# post.ps1
# Load credentials from .env file
$envFile = Join-Path $PSScriptRoot "../.env"
Get-Content $envFile | ForEach-Object {
    if ($_ -match "^\s*([^#][^=]+)=(.+)$") {
        [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim())
    }
}

$token    = [System.Environment]::GetEnvironmentVariable("LINKEDIN_TOKEN")
$personId = [System.Environment]::GetEnvironmentVariable("LINKEDIN_PERSON_ID")

if (-not $token -or -not $personId) {
    Write-Host "ERROR: LINKEDIN_TOKEN or LINKEDIN_PERSON_ID not found in .env"
    exit 1
}

$headers = @{
    "Authorization"             = "Bearer $token"
    "Content-Type"              = "application/json"
    "X-Restli-Protocol-Version" = "2.0.0"
}

$body = "{
    `"author`": `"urn:li:person:$personId`",
    `"lifecycleState`": `"PUBLISHED`",
    `"specificContent`": {
        `"com.linkedin.ugc.ShareContent`": {
            `"shareCommentary`": {
                `"text`": `"Test post from my AI Employee! #buildinginpublic`"
            },
            `"shareMediaCategory`": `"NONE`"
        }
    },
    `"visibility`": {
        `"com.linkedin.ugc.MemberNetworkVisibility`": `"PUBLIC`"
    }
}"

try {
    $r = Invoke-RestMethod `
        -Uri "https://api.linkedin.com/v2/ugcPosts" `
        -Method POST `
        -Headers $headers `
        -Body $body

    Write-Host "SUCCESS! Post ID:" $r.id
    Write-Host "Check your LinkedIn profile - post is live!"
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    $errorBody  = $_.ErrorDetails.Message
    Write-Host "Error $statusCode : $errorBody"
}