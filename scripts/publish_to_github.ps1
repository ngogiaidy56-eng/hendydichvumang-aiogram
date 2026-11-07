$ErrorActionPreference = "Stop"
$Repository = "ngogiaidy56-eng/hendydichvumang-aiogram"
$RemoteUrl = "https://github.com/$Repository.git"

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw "GitHub CLI (gh) chưa được cài. Cài từ https://cli.github.com/ rồi chạy lại."
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git chưa được cài."
}

gh auth status
if ($LASTEXITCODE -ne 0) { throw "Chưa đăng nhập GitHub CLI. Chạy: gh auth login" }
gh repo view $Repository
if ($LASTEXITCODE -ne 0) { throw "Không truy cập được repository $Repository" }

if (-not (Test-Path ".git")) {
    git init
    if ($LASTEXITCODE -ne 0) { throw "git init thất bại." }
}
$CurrentRemote = git remote get-url origin 2>$null
if ($LASTEXITCODE -eq 0 -and $CurrentRemote) {
    if ($CurrentRemote -ne $RemoteUrl -and $CurrentRemote -ne "git@github.com:$Repository.git") {
        throw "Remote origin không khớp repository đích: $CurrentRemote"
    }
} else {
    git remote add origin $RemoteUrl
    if ($LASTEXITCODE -ne 0) { throw "Không thêm được remote origin." }
}

git add .
if ($LASTEXITCODE -ne 0) { throw "git add thất bại." }
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    git commit -m "Build Hendy Dịch Vụ Mạng aiogram v3"
    if ($LASTEXITCODE -ne 0) { throw "git commit thất bại." }
}
git branch -M main
if ($LASTEXITCODE -ne 0) { throw "Không chuyển được sang nhánh main." }
git ls-remote --exit-code --heads origin main *> $null
if ($LASTEXITCODE -eq 0) {
    git pull --rebase origin main
    if ($LASTEXITCODE -ne 0) { throw "Không đồng bộ được main hiện tại; hãy xử lý conflict trước khi push." }
}
git push -u origin main
if ($LASTEXITCODE -ne 0) { throw "git push thất bại." }
Write-Host "Đã push mã nguồn lên $RemoteUrl"
