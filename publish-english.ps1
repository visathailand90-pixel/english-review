param([switch]$Publish,[switch]$Approved,[string[]]$Files=@(),[string]$Message='Update English learning apps')
$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
function Invoke-Checked { param([string]$Exe,[string[]]$Arguments) & $Exe @Arguments; if($LASTEXITCODE -ne 0){throw "$Exe failed ($LASTEXITCODE)"} }
$origin = git remote get-url origin
if($LASTEXITCODE -ne 0 -or $origin -notin @('https://github.com/visathailand90-pixel/english-review.git','https://github.com/visathailand90-pixel/english-review')){throw 'Unexpected origin'}
if((git branch --show-current) -ne 'main'){throw 'Expected main'}
Invoke-Checked git @('fetch','origin')
if((git rev-parse HEAD) -ne (git rev-parse origin/main)){throw 'Local and remote HEAD differ. Review before publication.'}
if(git diff --cached --name-only){throw 'Existing staged changes: review first'}
Invoke-Checked python @('tools/build.py')
Invoke-Checked python @('tools/test_apps.py')
Invoke-Checked python @('tools/validate.py')
Invoke-Checked python @('tools/test_upgrade.py')
Invoke-Checked node @('tools/test_backend.mjs')
Invoke-Checked git @('diff','--check')
git status --short
git diff --stat
if(-not $Publish){Write-Host 'Checks passed; no commit or push performed.'; return}
if($Files.Count -eq 0){throw 'Supply explicit reviewed -Files; blanket staging is forbidden'}
foreach($f in $Files){
 if($f -match '(^|/|\\)(inbox|private|archive|reports|tasks|staging|\.git)(/|\\|$)' -or $f -match '(\.env|\.(zip|mp3|mp4|wav|m4a|txt|docx|pdf)$)' -or $f -match '(^[/\\]|\.\.)'){throw "Forbidden path: $f"}
 if($f -notmatch '^(index\.html|app-template\.html|sw\.js|README\.md|AGENTS\.md|\.gitignore|publish-english\.ps1|icon(-192)?\.png|manifest\.webmanifest|lesson-data/[a-zA-Z0-9]+\.json|(reader|words)/(index\.html|manifest\.webmanifest|bank\.json|bank\.js|context\.js)|tools/(build|test_apps|test_upgrade|validate)\.py|tools/test_backend\.mjs|backend/(worker\.mjs|portal\.mjs|contracts\.mjs|glossary\.mjs|schema\.sql|wrangler\.example\.toml|README\.md))$'){throw "Path outside public allowlist: $f"}
 if(-not (Test-Path -LiteralPath $f -PathType Leaf)){throw "Missing file: $f"}
}
$Files | ForEach-Object {Write-Host "Publish: $_"}
if(-not $Approved -and (Read-Host 'Reviewed diff for private information? Type PUBLISH') -cne 'PUBLISH'){throw 'Cancelled'}
Invoke-Checked git (@('add','--')+$Files)
Invoke-Checked git @('diff','--cached','--check')
Invoke-Checked git @('commit','-m',$Message)
Invoke-Checked git @('push','origin','main')
Write-Host 'Push complete. Verify Pages deployment and all three URLs before declaring success.'
