# Test Structure Migration

The test suite has been consolidated and reorganized for better maintainability.

## Old Structure (Removed)
- `cads/tests/` - Duplicate tests removed
- `visuals/tests/` - Duplicate tests removed

## New Structure
- `tests/` - Unified test suite
  - `database/` - Database connection and integrity tests
  - `pipeline/` - ML pipeline and data processing tests
  - `visualization/` - Frontend and visualization tests
  - `fixtures/` - Test data and utilities

## Running Tests
```bash
# Run all tests
python tests/run_tests.py --all

# Run specific test categories
python tests/run_tests.py --database
python tests/run_tests.py --pipeline
python tests/run_tests.py --visualization

# Run fast unit tests only
python tests/run_tests.py --unit

# Run specific test
python tests/run_tests.py --test tests/database/test_connection.py
```

## Test Configuration
- `pytest.ini` - Pytest configuration
- `tests/conftest.py` - Shared fixtures and configuration
- `tests/fixtures/` - Test data and helper utilities

## Benefits
- ✅ Eliminated duplicate tests
- ✅ Better organization by functionality
- ✅ Shared fixtures and utilities
- ✅ Proper pytest configuration
- ✅ Multiple test execution modes
- ✅ Better error handling and output
