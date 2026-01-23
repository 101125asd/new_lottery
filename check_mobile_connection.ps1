# 手机端连接诊断脚本

Write-Host "=== 手机端连接诊断 ===" -ForegroundColor Cyan
Write-Host ""

# 1. 检查服务状态
Write-Host "1. 检查服务状态..." -ForegroundColor Yellow

$frontendRunning = $false
$backendRunning = $false

$frontendPort = netstat -ano | findstr ":5173" | findstr "LISTENING"
if ($frontendPort) {
    Write-Host "  ✓ 前端服务正在运行（端口 5173）" -ForegroundColor Green
    $frontendRunning = $true
} else {
    Write-Host "  ✗ 前端服务未运行（端口 5173）" -ForegroundColor Red
    Write-Host "    请运行: cd frontend && npm run dev" -ForegroundColor Yellow
}

$backendPort = netstat -ano | findstr ":8000" | findstr "LISTENING"
if ($backendPort) {
    Write-Host "  ✓ 后端服务正在运行（端口 8000）" -ForegroundColor Green
    $backendRunning = $true
} else {
    Write-Host "  ✗ 后端服务未运行（端口 8000）" -ForegroundColor Red
    Write-Host "    请运行: cd backend && python main.py" -ForegroundColor Yellow
}

Write-Host ""

# 2. 获取 IP 地址
Write-Host "2. 检测网络 IP 地址..." -ForegroundColor Yellow

$ipAddresses = @()
$ipConfig = ipconfig | Select-String "IPv4"

foreach ($line in $ipConfig) {
    $ip = $line -replace ".*:\s*", ""
    if ($ip -match "^\d+\.\d+\.\d+\.\d+$") {
        $ipAddresses += $ip
        Write-Host "  发现 IP: $ip" -ForegroundColor Cyan
    }
}

Write-Host ""

# 3. 检查防火墙
Write-Host "3. 检查防火墙规则..." -ForegroundColor Yellow

$firewall5173 = netsh advfirewall firewall show rule name="Vite Dev Server" 2>$null
$firewall8000 = netsh advfirewall firewall show rule name="FastAPI Backend" 2>$null

if ($firewall5173) {
    Write-Host "  ✓ 端口 5173 防火墙规则已配置" -ForegroundColor Green
} else {
    Write-Host "  ⚠ 端口 5173 可能被防火墙阻止" -ForegroundColor Yellow
    Write-Host "    运行: powershell -ExecutionPolicy Bypass -File add_firewall_rules.ps1" -ForegroundColor Cyan
}

if ($firewall8000) {
    Write-Host "  ✓ 端口 8000 防火墙规则已配置" -ForegroundColor Green
} else {
    Write-Host "  ⚠ 端口 8000 可能被防火墙阻止" -ForegroundColor Yellow
    Write-Host "    运行: powershell -ExecutionPolicy Bypass -File add_firewall_rules.ps1" -ForegroundColor Cyan
}

Write-Host ""

# 4. 生成测试 URL
Write-Host "4. 手机端访问地址：" -ForegroundColor Yellow
Write-Host ""

if ($ipAddresses.Count -gt 0) {
    foreach ($ip in $ipAddresses) {
        Write-Host "  大屏页面: " -NoNewline
        Write-Host "http://$ip:5173/" -ForegroundColor Green
        Write-Host "  手机页面: " -NoNewline
        Write-Host "http://$ip:5173/mobile" -ForegroundColor Green
        Write-Host "  后端 API:  " -NoNewline
        Write-Host "http://$ip:8000/api/get-ip" -ForegroundColor Green
        Write-Host ""
    }
} else {
    Write-Host "  ⚠ 无法检测到 IP 地址" -ForegroundColor Yellow
    Write-Host "    请手动运行: ipconfig" -ForegroundColor Cyan
}

Write-Host ""

# 5. 测试建议
Write-Host "5. 测试步骤：" -ForegroundColor Yellow
Write-Host "  1. 确保手机和电脑连接到同一个 WiFi 网络" -ForegroundColor White
Write-Host "  2. 在手机浏览器中输入上述地址之一" -ForegroundColor White
Write-Host "  3. 如果无法连接，检查防火墙设置" -ForegroundColor White
Write-Host "  4. 如果页面加载但 WebSocket 失败，检查后端服务" -ForegroundColor White

Write-Host ""
Write-Host "=== 诊断完成 ===" -ForegroundColor Cyan

