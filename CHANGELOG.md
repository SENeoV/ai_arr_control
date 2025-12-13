# Changelog

All notable changes to AI Arr Control are documented in this file.

## [0.4.0] - 2025-01-13

### Major Changes
- **New**: Complete refactor to production-grade quality and reliability
- **New**: Pydantic v2 request/response schemas for all API endpoints
- **New**: Comprehensive error handling and resilience patterns
- **New**: Structured metrics and event logging system
- **New**: Monitoring endpoints for observability
- **New**: Retry logic with exponential backoff for service calls
- **New**: CLI registration in pyproject.toml for proper entry points
- **New**: Enhanced test coverage with agent and endpoint tests
- **New**: Circuit breaker pattern utilities for resilience

### Features Added
- `/metrics` endpoint - Application health metrics and statistics
- `/events` endpoint - Audit log of recent system events
- CLI tool registration - Use `ai-arr-control` command after installation
- Configuration validation at startup - Comprehensive validation of settings
- Event logging - Structured audit trail for all operations
- Response validation - Type-safe API responses via Pydantic models
- Retry decorators - Automatic retry logic for failed requests
- Database path creation - Automatic creation of db/ directory if needed

### Improvements
- **Code Quality**:
  - Eliminated duplicate validation logic in endpoints
  - Unified helper function for service and indexer validation
  - Consistent error handling across all endpoints
  - Improved docstrings and type hints
  
- **Error Handling**:
  - Added response type validation in services
  - Better error messages with context
  - Graceful degradation on service failures
  - Proper exception re-raising vs. swallowing
  
- **API**:
  - All endpoints now return Pydantic models
  - Consistent response schema across endpoints
  - Better error responses with detail field
  - Added response models to all endpoint signatures
  
- **Logging**:
  - Added event logging for audit trail
  - Metrics collection for uptime and operation counts
  - Better structured logging with context

- **Documentation**:
  - Complete rewrite of README.md
  - Added comprehensive API documentation
  - Added troubleshooting section
  - Added examples and use cases
  - Added architecture documentation
  - Added performance considerations

- **Tests**:
  - Enhanced test_main.py with 10+ new tests
  - Comprehensive agent tests
  - Service validation tests
  - Error condition tests

### Fixed
- Duplicate validation in disable/enable endpoints
- Missing service validation in control agent
- Missing response type checking in services
- Incomplete configuration validation

### Security
- Better API key validation at startup
- Configuration validation prevents common errors
- Proper timeout handling on HTTP requests
- Graceful shutdown on errors

### Dependencies
- Added `click>=8.0` for CLI framework
- All dependencies remain compatible with Python 3.11+

### Migration Notes
- Configuration validation is now stricter - ensure .env is correct
- API responses now use Pydantic models - compatible with existing JSON consumers
- CLI is now registered - can use `ai-arr-control` command after `pip install -e .`

### Known Limitations
- Prowlarr indexer testing may not work on all versions (API endpoint varies)
- Discovery feature requires manual URL configuration
- Database retention is indefinite (consider archiving old records)

### Performance
- Retry logic may add ~1-3 seconds to failed requests
- Event logging has minimal overhead (written to file)
- Metrics collection uses in-memory counters (negligible impact)

### Deprecated
- None

### Removed
- None

---

## [0.3.0] - Previous Release

See git history for changes in previous versions.
