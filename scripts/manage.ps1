#!/usr/bin/env pwsh

<#
.SYNOPSIS
    AI Arr Control Management Script for Windows PowerShell

.DESCRIPTION
    Helper script to easily start, stop, restart, and manage the AI Arr Control application.
    Provides simple commands for common operations without needing to remember CLI arguments.

.EXAMPLE
    .\manage.ps1 start
    .\manage.ps1 stop
    .\manage.ps1 restart
    .\manage.ps1 status
    .\manage.ps1 logs
    .\manage.ps1 health

.NOTES
    Requires Python 3.8+ and the AI Arr Control package to be installed.
#>

param(
    [Parameter(Position = 0)]
    [ValidateSet('start', 'stop', 'restart', 'status', 'logs', 'health', 'metrics', 'events', 'init-db', 'test', 'version', 'help')]
    [string]$Command = 'help',
    
    [Parameter(Position = 1)]
    [int]$Port = 8000,
    
    [string]$ServerHost = '127.0.0.1',
    
    [switch]$DetachMode = $false,
    
    [int]$LogLines = 50
)

# Color output helper
function Write-Success {
    param([string]$Message)
    Write-Host "[OK] " -ForegroundColor Green -NoNewline
    Write-Host $Message
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERR] " -ForegroundColor Red -NoNewline
    Write-Host $Message
}

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] " -ForegroundColor Blue -NoNewline
    Write-Host $Message
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARN] " -ForegroundColor Yellow -NoNewline
    Write-Host $Message
}

# Show help
function Show-Help {
    Write-Host @"
AI Arr Control Management Script - Windows
============================================

USAGE:
    .\manage.ps1 <command> [options]

COMMANDS:
    start              Start the AI Arr Control server
    stop               Stop the running server
    restart            Restart the server (stop + start)
    status             Check if server is running and get stats
    logs               Show recent application logs
    health             Quick health check of all services
    metrics            Show application metrics and uptime
    events             Show recent system events
    init-db            Initialize the database
    test               Run test suite
    version            Show application version
    help               Display this help message

OPTIONS:
    -Port <int>        Server port (default: 8000)
    -Host <string>     Server host (default: 127.0.0.1)
    -DetachMode        Run server in background
    -LogLines <int>    Number of log lines to show (default: 50)

EXAMPLES:
    # Start server on port 8000
    .\manage.ps1 start

    # Start server on custom port
    .\manage.ps1 start -Port 9000

    # Start in background
    .\manage.ps1 start -DetachMode

    # Stop server
    .\manage.ps1 stop

    # Restart server
    .\manage.ps1 restart

    # Check server status
    .\manage.ps1 status

    # View logs
    .\manage.ps1 logs -LogLines 100

    # Check service health
    .\manage.ps1 health

    # View metrics
    .\manage.ps1 metrics
"@
}

# Get server URL
function Get-ServerUrl {
    return "http://${ServerHost}:${Port}"
}

# Check if server is running
function Test-ServerRunning {
    try {
        $response = Invoke-WebRequest -Uri "$(Get-ServerUrl)/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        return $response.StatusCode -eq 200
    }
    catch {
        return $false
    }
}

# Start server
function Start-Server {
    Write-Info "Starting AI Arr Control server..."
    
    if (Test-ServerRunning) {
        Write-Warning "Server is already running on $(Get-ServerUrl)"
        return
    }
    
    $args = @("run", "--host", $ServerHost, "--port", $Port)
    
    if ($DetachMode) {
        $args += "--detach"
        Write-Info "Starting in detached mode..."
    }
    
    try {
        python -m tools.cli @args
        
        if ($DetachMode) {
            Start-Sleep -Seconds 3
            if (Test-ServerRunning) {
                Write-Success "Server started successfully on $(Get-ServerUrl)"
            }
            else {
                Write-Warning "Server may not have started properly. Check logs."
            }
        }
    }
    catch {
        Write-Error "Failed to start server: $_"
        exit 1
    }
}

# Stop server
function Stop-Server {
    Write-Info "Stopping AI Arr Control server..."
    
    if (-not (Test-ServerRunning)) {
        Write-Warning "Server is not running"
        return
    }
    
    try {
        python -m tools.cli stop
        Start-Sleep -Seconds 2
        
        if (Test-ServerRunning) {
            Write-Warning "Server did not stop. Attempting force kill..."
            Get-Process python -ErrorAction SilentlyContinue | Where-Object {
                $_.CommandLine -match "uvicorn" -or $_.CommandLine -match "main:app"
            } | Stop-Process -Force
            Write-Success "Server stopped (forced)"
        }
        else {
            Write-Success "Server stopped successfully"
        }
    }
    catch {
        Write-Error "Error stopping server: $_"
        exit 1
    }
}

# Restart server
function Restart-Server {
    Write-Info "Restarting server..."
    Stop-Server
    Start-Sleep -Seconds 2
    Start-Server
    Write-Success "Server restart complete"
}

# Check status
function Check-Status {
    Write-Info "Checking server status..."
    Write-Host ""
    
    $running = Test-ServerRunning
    
    if ($running) {
        Write-Success "Server is RUNNING on $(Get-ServerUrl)"
        
        try {
            # Get health
            $health = (Invoke-WebRequest -Uri "$(Get-ServerUrl)/health" -UseBasicParsing).Content | ConvertFrom-Json
            Write-Host "  Status: $($health.status)" -ForegroundColor Green
            
            # Get startup status
            $startup = (Invoke-WebRequest -Uri "$(Get-ServerUrl)/startup-status" -UseBasicParsing).Content | ConvertFrom-Json
            Write-Host "  Startup Complete: $($startup.complete)"
            
            if ($startup.agents_run) {
                Write-Host "  Agents Initialized:"
                if ($startup.agents_run.health_check) { Write-Host "    - Health Check" -ForegroundColor Green }
                if ($startup.agents_run.autoheal) { Write-Host "    - Autoheal" -ForegroundColor Green }
                if ($startup.agents_run.discovery) { Write-Host "    - Discovery" -ForegroundColor Green }
            }
            
            # Get metrics
            $metrics = (Invoke-WebRequest -Uri "$(Get-ServerUrl)/metrics" -UseBasicParsing).Content | ConvertFrom-Json
            $uptime = [Math]::Round($metrics.uptime_seconds, 0)
            $ops = $metrics.total_operations
            $okCount = $metrics.successful
            $badCount = $metrics.failed
            Write-Host "  Uptime: $uptime seconds"
            $msg = "  Operations: $($ops) total ($($okCount) successful, $($badCount) failed)"
            Write-Host $msg
            
        }
        catch {
            Write-Warning "Could not retrieve detailed status"
        }
    }
    else {
        Write-Warning "Server is NOT RUNNING"
        Write-Host ""
        Write-Info "To start the server, run:"
        Write-Host "  .\manage.ps1 start"
    }
    
    Write-Host ""
}

# Show logs
function Show-Logs {
    $logFile = "ai_arr_control.log"
    
    if (-not (Test-Path $logFile)) {
        Write-Warning "Log file not found: $logFile"
        return
    }
    
    Write-Info "Last $LogLines lines of $logFile`n"
    Get-Content $logFile -Tail $LogLines
}

# Health check
function Health-Check {
    Write-Info "Performing health check..."
    Write-Host ""
    
    if (-not (Test-ServerRunning)) {
        Write-Error "Server is not running"
        return
    }
    
    try {
        $health = (Invoke-WebRequest -Uri "$(Get-ServerUrl)/health" -UseBasicParsing).Content | ConvertFrom-Json
        
        Write-Success "Server Health: $($health.status)"
        Write-Success "Service: $($health.service)"
        
        # Get detailed stats
        $stats = (Invoke-WebRequest -Uri "$(Get-ServerUrl)/stats/detailed" -UseBasicParsing).Content | ConvertFrom-Json
        
        Write-Host ""
        Write-Host "Service Status:" -ForegroundColor Cyan
        
        foreach ($service in @("radarr", "sonarr", "prowlarr")) {
            if ($stats.by_service.$service) {
                $svc = $stats.by_service.$service
                if ($svc.error) {
                    Write-Error "$($service.ToUpper()): $($svc.error)"
                }
                else {
                    Write-Success "$($service.ToUpper()): $($svc.total_indexers) indexers ($($svc.enabled) enabled, $($svc.disabled) disabled)"
                    Write-Host "  Health: $($svc.health_checks.success_rate_percent)% success rate"
                }
            }
        }
    }
    catch {
        Write-Error "Health check failed: $_"
    }
}

# Show metrics
function Show-Metrics {
    Write-Info "Retrieving metrics..."
    Write-Host ""
    
    if (-not (Test-ServerRunning)) {
        Write-Error "Server is not running"
        return
    }
    
    try {
        $metrics = (Invoke-WebRequest -Uri "$(Get-ServerUrl)/metrics" -UseBasicParsing).Content | ConvertFrom-Json
        
        Write-Host "Application Metrics:" -ForegroundColor Cyan
        Write-Host "  Uptime: $([Math]::Round($metrics.uptime_seconds / 60, 2)) minutes"
        Write-Host "  Total Operations: $($metrics.total_operations)"
        Write-Host "  Successful: $($metrics.successful)"
        Write-Host "  Failed: $($metrics.failed)"
        Write-Host "  Success Rate: $($metrics.success_rate_percent)%"
    }
    catch {
        Write-Error "Could not retrieve metrics: $_"
    }
}

# Show events
function Show-Events {
    Write-Info "Retrieving recent events..."
    Write-Host ""
    
    if (-not (Test-ServerRunning)) {
        Write-Error "Server is not running"
        return
    }
    
    try {
        $events = (Invoke-WebRequest -Uri "$(Get-ServerUrl)/events?limit=10" -UseBasicParsing).Content | ConvertFrom-Json
        
        if ($events.events_count -eq 0) {
            Write-Warning "No recent events"
            return
        }
        
        Write-Host "Recent Events:" -ForegroundColor Cyan
        foreach ($event in $events.events) {
            $timestamp = [DateTime]::Parse($event.timestamp).ToString("yyyy-MM-dd HH:mm:ss")
            $color = switch ($event.severity) {
                "ERROR" { "Red" }
                "WARNING" { "Yellow" }
                "INFO" { "Green" }
                default { "White" }
            }
            Write-Host "  [$timestamp] $($event.event_type) - $($event.severity)" -ForegroundColor $color
        }
    }
    catch {
        Write-Error "Could not retrieve events: $_"
    }
}

# Initialize database
function Initialize-Database {
    Write-Info "Initializing database..."
    
    try {
        python -m tools.cli initdb
        Write-Success "Database initialized successfully"
    }
    catch {
        Write-Error "Failed to initialize database: $_"
        exit 1
    }
}

# Run tests
function Run-Tests {
    Write-Info "Running test suite..."
    Write-Host ""
    
    try {
        python -m tools.cli tests
        Write-Success "Tests completed"
    }
    catch {
        Write-Error "Tests failed: $_"
        exit 1
    }
}

# Show version
function Show-Version {
    try {
        python -m tools.cli version
    }
    catch {
        Write-Error "Could not determine version: $_"
        exit 1
    }
}

# Main command dispatcher
switch ($Command) {
    'start' {
        Start-Server
    }
    'stop' {
        Stop-Server
    }
    'restart' {
        Restart-Server
    }
    'status' {
        Check-Status
    }
    'logs' {
        Show-Logs
    }
    'health' {
        Health-Check
    }
    'metrics' {
        Show-Metrics
    }
    'events' {
        Show-Events
    }
    'init-db' {
        Initialize-Database
    }
    'test' {
        Run-Tests
    }
    'version' {
        Show-Version
    }
    'help' {
        Show-Help
    }
    default {
        Write-Error "Unknown command: $Command"
        Show-Help
        exit 1
    }
}
