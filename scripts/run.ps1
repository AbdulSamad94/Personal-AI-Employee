$token = "YOUR_LINKEDIN_OAUTH_TOKEN"

$r = Invoke-RestMethod `
    -Uri "https://api.linkedin.com/v2/userinfo" `
    -Headers @{ Authorization = "Bearer $token" }

Write-Host "YOUR PERSON ID:" $r.sub