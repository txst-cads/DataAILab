# CADS Research Visualization System - Test Suite

This directory contains the consolidated and enhanced test suite for the CADS Research Visualization System.

## Test Structure

```
tests/
├── conftest.py              # Pytest configuration and shared fixtures
├── fixtures/                # Test data and utilities
│   ├── sample_data.json     # Sample test data
│   └── test_helpers.py      # Test utility functions
├── database/                # Database tests
│   ├── test_connection.py   # Database connectivity tests
│   └── test_data_integrity.py # Data integrity and validation tests
├── pipeline/                # ML pipeline tests
│   ├── test_data_processing.py # Data processing tests
│   └── test_full_pipeline.py   # End-to-end pipeline tests
├── visualization/           # Frontend visualization tests
│   ├── test_html_structure.py  # HTML structure and components
│   ├── test_rendering.py       # Data visualization format tests
│   ├── test_interactions.py    # UI interaction tests
│   └── test_data_loading.py    # Data loading and format tests
├── test_project_structure.py   # Project structure validation
├── run_tests.py            # Test runner script
└── cleanup_old_tests.py    # Cleanup script for migration
```

## Running Tests

### Quick Start
```bash
# Run fast unit tests (recommended for development)
python3 tests/run_tests.py --unit

# Run all tests
python3 tests/run_tests.py --all

# List available test categories
python3 tests/run_tests.py --list
```

### Test Categories

#### Database Tests
```bash
python3 tests/run_tests.py --database
```
- Database connection and authentication
- Data integrity and consistency
- Query performance
- Referential integrity

#### Pipeline Tests
```bash
python3 tests/run_tests.py --pipeline
```
- Data processing functionality
- ML pipeline execution
- Embedding generation and parsing
- Error handling and validation

#### Visualization Tests
```bash
python3 tests/run_tests.py --visualization
```
- HTML structure and components
- Data visualization format
- UI interactions and accessibility
- Data loading and performance

#### Integration Tests
```bash
python3 tests/run_tests.py --integration
```
- End-to-end pipeline execution
- Full system integration
- Performance testing

### Specific Tests
```bash
# Run specific test file
python3 tests/run_tests.py --test tests/database/test_connection.py

# Run specific test method
python3 tests/run_tests.py --test tests/database/test_connection.py::TestDatabaseConnection::test_database_connection_success
```

## Test Configuration

### Pytest Configuration
- Configuration file: `pytest.ini`
- Markers for test categorization (database, slow, integration, visualization)
- Minimal output for CI/CD compatibility

### Environment Setup
Tests automatically handle missing dependencies and database connections:
- Database tests skip if `DATABASE_URL` not configured
- ML tests skip if dependencies (umap, hdbscan) not installed
- Visualization tests work with mock data when files not available

### Test Fixtures
- Shared fixtures in `tests/conftest.py`
- Sample data in `tests/fixtures/sample_data.json`
- Test utilities in `tests/fixtures/test_helpers.py`

## Test Features

### Comprehensive Coverage
- ✅ Database connectivity and integrity
- ✅ ML pipeline functionality
- ✅ Data processing and validation
- ✅ Frontend structure and interactions
- ✅ Error handling and edge cases
- ✅ Performance characteristics

### Best Practices
- ✅ Minimal output for CI/CD
- ✅ Proper test isolation
- ✅ Mock data for offline testing
- ✅ Graceful handling of missing dependencies
- ✅ Clear test categorization
- ✅ Comprehensive fixtures and utilities

### Test Organization
- ✅ Eliminated duplicate tests
- ✅ Logical grouping by functionality
- ✅ Shared utilities and fixtures
- ✅ Consistent naming conventions
- ✅ Proper pytest configuration

## Migration from Old Structure

The test suite has been consolidated from fragmented tests across:
- `cads/tests/` (removed duplicates)
- `visuals/tests/` (removed duplicates)
- `scripts/test_*.py` (preserved unique functionality)

### Benefits of New Structure
1. **No Duplication**: Eliminated 25+ duplicate test files
2. **Better Organization**: Tests grouped by functionality
3. **Shared Resources**: Common fixtures and utilities
4. **Multiple Execution Modes**: Unit, integration, category-specific
5. **CI/CD Ready**: Minimal output and proper error handling
6. **Maintainable**: Clear structure and documentation

## Development Workflow

### Adding New Tests
1. Choose appropriate directory (`database/`, `pipeline/`, `visualization/`)
2. Use existing fixtures from `tests/fixtures/`
3. Follow naming convention: `test_*.py`
4. Add appropriate pytest markers
5. Update this README if adding new categories

### Test Development Guidelines
- Use descriptive test names
- Include docstrings for test methods
- Handle missing dependencies gracefully
- Use appropriate pytest markers
- Keep tests focused and isolated
- Use shared fixtures when possible

## Troubleshooting

### Common Issues
1. **Database tests failing**: Check `DATABASE_URL` in `.env`
2. **ML tests skipped**: Install ML dependencies (`pip install umap-learn hdbscan`)
3. **Import errors**: Ensure project root is in Python path
4. **Slow tests**: Use `--unit` flag to skip slow integration tests

### Debug Mode
```bash
# Run with verbose output
python3 -m pytest tests/ -v

# Run with full traceback
python3 -m pytest tests/ --tb=long

# Run specific failing test with debug info
python3 -m pytest tests/path/to/test.py::test_name -v --tb=long
```

## CI/CD Integration

The test suite is designed for CI/CD integration:
- Minimal output by default (`-q --tb=short`)
- Proper exit codes for success/failure
- Graceful handling of missing dependencies
- Fast unit tests for quick feedback
- Comprehensive integration tests for full validation

### GitHub Actions Integration
```yaml
- name: Run Unit Tests
  run: python3 tests/run_tests.py --unit

- name: Run Database Tests
  run: python3 tests/run_tests.py --database
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}

- name: Run Full Test Suite
  run: python3 tests/run_tests.py --all
```

## Contributing

When contributing to the test suite:
1. Follow existing patterns and conventions
2. Add tests for new functionality
3. Update documentation as needed
4. Ensure tests pass in isolation
5. Use appropriate test markers
6. Consider both positive and negative test cases