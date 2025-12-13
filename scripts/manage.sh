#!/bin/bash

#
# AI Arr Control Management Script for Linux/macOS
#
# Helper script to easily start, stop, restart, and manage the AI Arr Control application.
# Provides simple commands for common operations without needing to remember CLI arguments.
#
# USAGE:
#   ./manage.sh <command> [options]
#
# COMMANDS:
#   start       Start the AI Arr Control server
#   stop        Stop the running server
#   restart     Restart the server (stop + start)
#   status      Check if server is running and get stats
#   logs        Show recent application logs
#   health      Quick health check of all services
#   metrics     Show application metrics and uptime
#   events      Show recent system events
#   init-db     Initialize the database
#   test        Run test suite
#   version     Show application version
#   help        Display this help message
#

set -e

# Configuration
PORT="${PORT:-8000}"
HOST="${HOST:-127.0.0.1}"
LOG_FILE="${LOG_FILE:-ai_arr_control.log}"
LOG_LINES="${LOG_LINES:-50}"
DETACH_MODE=false

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Helper functions for colored output
success() {
    echo -e "${GREEN}✓${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Show help
show_help() {
    cat << 'EOF'
AI Arr Control Management Script - Linux/macOS
================================================

USAGE:
    ./manage.sh <command> [options]

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
    PORT=<int>         Server port (default: 8000)
    HOST=<string>      Server host (default: 127.0.0.1)
    DETACH_MODE=true   Run server in background

EXAMPLES:
    # Start server on port 8000
    ./manage.sh start

    # Start server on custom port
    PORT=9000 ./manage.sh start

    # Start in background
    DETACH_MODE=true ./manage.sh start

    # Stop server
    ./manage.sh stop

    # Restart server
    ./manage.sh restart

    # Check server status
    ./manage.sh status

    # View logs
    ./manage.sh logs

    # Check service health
    ./manage.sh health

    # View metrics
    ./manage.sh metrics
EOF
}

# Get server URL
get_server_url() {
    echo "http://${HOST}:${PORT}"
}

# Check if server is running
test_server_running() {
    if curl -s -m 5 "$(get_server_url)/health" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Start server
start_server() {
    info "Starting AI Arr Control server..."
    
    if test_server_running; then
        warning "Server is already running on $(get_server_url)"
        return 0
    fi
    
    local args="run --host $HOST --port $PORT"
    
    if [ "$DETACH_MODE" = "true" ]; then
        args="$args --detach"
        info "Starting in detached mode..."
    fi
    
    if python -m tools.cli $args; then
        if [ "$DETACH_MODE" = "true" ]; then
            sleep 3
            if test_server_running; then
                success "Server started successfully on $(get_server_url)"
            else
                warning "Server may not have started properly. Check logs."
            fi
        fi
    else
        error "Failed to start server"
        exit 1
    fi
}

# Stop server
stop_server() {
    info "Stopping AI Arr Control server..."
    
    if ! test_server_running; then
        warning "Server is not running"
        return 0
    fi
    
    if python -m tools.cli stop 2>/dev/null; then
        sleep 2
        if test_server_running; then
            warning "Server did not stop. Attempting force kill..."
            pkill -f "uvicorn.*main:app" 2>/dev/null || true
            pkill -f "python.*main:app" 2>/dev/null || true
            success "Server stopped (forced)"
        else
            success "Server stopped successfully"
        fi
    else
        error "Error stopping server"
        exit 1
    fi
}

# Restart server
restart_server() {
    info "Restarting server..."
    stop_server
    sleep 2
    start_server
    success "Server restart complete"
}

# Check status
check_status() {
    info "Checking server status..."
    echo ""
    
    if test_server_running; then
        success "Server is RUNNING on $(get_server_url)"
        echo ""
        
        # Get health
        if health_data=$(curl -s "$(get_server_url)/health"); then
            status=$(echo "$health_data" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
            echo -e "  Status: ${GREEN}$status${NC}"
        fi
        
        # Get startup status
        if startup_data=$(curl -s "$(get_server_url)/startup-status"); then
            complete=$(echo "$startup_data" | grep -o '"complete":[^,}]*' | cut -d':' -f2)
            echo "  Startup Complete: $complete"
            
            if echo "$startup_data" | grep -q '"health_check":true'; then
                echo "    ✓ Health Check"
            fi
            if echo "$startup_data" | grep -q '"autoheal":true'; then
                echo "    ✓ Autoheal"
            fi
            if echo "$startup_data" | grep -q '"discovery":true'; then
                echo "    ✓ Discovery"
            fi
        fi
        
        # Get metrics
        if metrics_data=$(curl -s "$(get_server_url)/metrics"); then
            uptime=$(echo "$metrics_data" | grep -o '"uptime_seconds":[0-9.]*' | cut -d':' -f2)
            operations=$(echo "$metrics_data" | grep -o '"total_operations":[0-9]*' | cut -d':' -f2)
            successful=$(echo "$metrics_data" | grep -o '"successful":[0-9]*' | cut -d':' -f2)
            failed=$(echo "$metrics_data" | grep -o '"failed":[0-9]*' | cut -d':' -f2)
            
            uptime_rounded=$(printf "%.0f" "$uptime")
            echo "  Uptime: $uptime_rounded seconds"
            echo "  Operations: $operations total ($successful successful, $failed failed)"
        fi
    else
        warning "Server is NOT RUNNING"
        echo ""
        info "To start the server, run:"
        echo "  ./manage.sh start"
    fi
    
    echo ""
}

# Show logs
show_logs() {
    if [ ! -f "$LOG_FILE" ]; then
        warning "Log file not found: $LOG_FILE"
        return
    fi
    
    info "Last $LOG_LINES lines of $LOG_FILE\n"
    tail -n $LOG_LINES "$LOG_FILE"
}

# Health check
health_check() {
    info "Performing health check..."
    echo ""
    
    if ! test_server_running; then
        error "Server is not running"
        return
    fi
    
    # Get health
    if health_data=$(curl -s "$(get_server_url)/health"); then
        status=$(echo "$health_data" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        service=$(echo "$health_data" | grep -o '"service":"[^"]*"' | cut -d'"' -f4)
        success "Server Health: $status"
        success "Service: $service"
    fi
    
    # Get detailed stats
    if stats_data=$(curl -s "$(get_server_url)/stats/detailed"); then
        echo ""
        echo -e "${CYAN}Service Status:${NC}"
        
        for service_name in radarr sonarr prowlarr; do
            if echo "$stats_data" | grep -q "\"$service_name\""; then
                total=$(echo "$stats_data" | grep -A 10 "\"$service_name\"" | grep -o '"total_indexers":[0-9]*' | cut -d':' -f2 | head -1)
                enabled=$(echo "$stats_data" | grep -A 10 "\"$service_name\"" | grep -o '"enabled":[0-9]*' | cut -d':' -f2 | head -1)
                disabled=$(echo "$stats_data" | grep -A 10 "\"$service_name\"" | grep -o '"disabled":[0-9]*' | cut -d':' -f2 | head -1)
                
                if [ ! -z "$total" ]; then
                    success "${service_name^^}: $total indexers ($enabled enabled, $disabled disabled)"
                fi
            fi
        done
    fi
}

# Show metrics
show_metrics() {
    info "Retrieving metrics..."
    echo ""
    
    if ! test_server_running; then
        error "Server is not running"
        return
    fi
    
    if metrics_data=$(curl -s "$(get_server_url)/metrics"); then
        uptime=$(echo "$metrics_data" | grep -o '"uptime_seconds":[0-9.]*' | cut -d':' -f2)
        operations=$(echo "$metrics_data" | grep -o '"total_operations":[0-9]*' | cut -d':' -f2)
        successful=$(echo "$metrics_data" | grep -o '"successful":[0-9]*' | cut -d':' -f2)
        failed=$(echo "$metrics_data" | grep -o '"failed":[0-9]*' | cut -d':' -f2)
        success_rate=$(echo "$metrics_data" | grep -o '"success_rate_percent":[0-9.]*' | cut -d':' -f2)
        
        uptime_minutes=$(echo "scale=2; $uptime / 60" | bc)
        
        echo -e "${CYAN}Application Metrics:${NC}"
        echo "  Uptime: $uptime_minutes minutes"
        echo "  Total Operations: $operations"
        echo "  Successful: $successful"
        echo "  Failed: $failed"
        echo "  Success Rate: $success_rate%"
    fi
}

# Show events
show_events() {
    info "Retrieving recent events..."
    echo ""
    
    if ! test_server_running; then
        error "Server is not running"
        return
    fi
    
    if events_data=$(curl -s "$(get_server_url)/events?limit=10"); then
        count=$(echo "$events_data" | grep -o '"events_count":[0-9]*' | cut -d':' -f2)
        
        if [ "$count" -eq 0 ]; then
            warning "No recent events"
            return
        fi
        
        echo -e "${CYAN}Recent Events:${NC}"
        # Simple event display - could be enhanced
        echo "$events_data" | head -20
    fi
}

# Initialize database
init_database() {
    info "Initializing database..."
    
    if python -m tools.cli initdb; then
        success "Database initialized successfully"
    else
        error "Failed to initialize database"
        exit 1
    fi
}

# Run tests
run_tests() {
    info "Running test suite..."
    echo ""
    
    if python -m tools.cli tests; then
        success "Tests completed"
    else
        error "Tests failed"
        exit 1
    fi
}

# Show version
show_version() {
    python -m tools.cli version
}

# Parse command
COMMAND="${1:-help}"

# Parse additional options
while [ $# -gt 0 ]; do
    case $1 in
        PORT=*)
            PORT="${1#PORT=}"
            ;;
        HOST=*)
            HOST="${1#HOST=}"
            ;;
        DETACH_MODE=*)
            DETACH_MODE="${1#DETACH_MODE=}"
            ;;
        LOG_LINES=*)
            LOG_LINES="${1#LOG_LINES=}"
            ;;
    esac
    shift
done

# Execute command
case "$COMMAND" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    status)
        check_status
        ;;
    logs)
        show_logs
        ;;
    health)
        health_check
        ;;
    metrics)
        show_metrics
        ;;
    events)
        show_events
        ;;
    init-db)
        init_database
        ;;
    test)
        run_tests
        ;;
    version)
        show_version
        ;;
    help)
        show_help
        ;;
    *)
        error "Unknown command: $COMMAND"
        echo ""
        show_help
        exit 1
        ;;
esac
