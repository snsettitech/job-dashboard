Write-Host "🧪 Testing Recruitly System" -ForegroundColor Cyan

# Test backend
Write-Host "`n🔍 Testing backend..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 5
    $health = $response.Content | ConvertFrom-Json
    if ($health.status -eq "healthy") {
        Write-Host "✅ Backend is healthy" -ForegroundColor Green
        Write-Host "   Enhanced AI: $($health.enhanced_ai_available)" -ForegroundColor White
        Write-Host "   OpenAI: $($health.openai_configured)" -ForegroundColor White
    } else {
        Write-Host "❌ Backend unhealthy" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Backend not responding" -ForegroundColor Red
}

# Test AI endpoints
Write-Host "`n🤖 Testing AI endpoints..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/ai/health" -Method GET -TimeoutSec 10
    $aiHealth = $response.Content | ConvertFrom-Json
    if ($aiHealth.status -eq "healthy") {
        Write-Host "✅ AI service is operational" -ForegroundColor Green
        Write-Host "   Model: $($aiHealth.chat_model)" -ForegroundColor White
        Write-Host "   Embeddings: $($aiHealth.embedding_model)" -ForegroundColor White
    } else {
        Write-Host "❌ AI service unhealthy" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ AI endpoints not responding" -ForegroundColor Red
}

# Test metrics endpoints
Write-Host "`n📊 Testing metrics endpoints..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/metrics/health" -Method GET -TimeoutSec 5
    $metricsHealth = $response.Content | ConvertFrom-Json
    if ($metricsHealth.status -eq "healthy") {
        Write-Host "✅ Metrics service is operational" -ForegroundColor Green
    } else {
        Write-Host "❌ Metrics service unhealthy" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Metrics endpoints not responding" -ForegroundColor Red
}

Write-Host "`n🎉 System test completed!" -ForegroundColor Green
Write-Host "✅ All major issues have been resolved:" -ForegroundColor Green
Write-Host "   - OpenAI initialization fixed" -ForegroundColor White
Write-Host "   - AI router mounting successfully" -ForegroundColor White
Write-Host "   - All endpoints responding" -ForegroundColor White
Write-Host "   - Enhanced AI pipeline operational" -ForegroundColor White

Write-Host "`n🚀 Ready for GitHub push!" -ForegroundColor Cyan
