# Farm Management System - Testing

This document outlines the automated testing strategy for the Farm Management System.

## Test Framework

We use **pytest** as the testing framework, which is Python's most popular testing library.

## Running Tests

```bash
# Install dependencies (one time)
pip install -e .

# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_db.py

# Run with verbose output
python -m pytest -v

# Run tests matching pattern
python -m pytest -k "test_verify_user"
```

**Note:** Use `python -m pytest` instead of `pytest` to ensure proper Python path configuration.

## Test Categories

### Unit Tests (24 total)
- **Database Operations** (8 tests): Connection, user auth, CRUD operations
- **Business Logic** (8 tests): Order processing, stock management, season validation
- **Algorithms** (6 tests): Internal calculations, validations, and transformations
- **Integration** (2 tests): CSV import/export, report generation

### Internal Algorithms Tested (6+)
The following internal algorithms are explicitly tested and marked with `# INTERNAL ALGORITHM TEST:` comments in the test file:

1. **Season Mapping** (`get_season()`) - Maps calendar months to meteorological seasons
2. **Stock Management** - Deduction/refund calculations with business rules validation
3. **Password Security** - bcrypt hashing and verification algorithms
4. **Search Filtering** - Regex sanitization and case-insensitive matching
5. **Financial Calculations** - Cart totals and revenue aggregation with precision
6. **Season Validation** - Complex parcel status update logic with date comparisons

## Test Coverage

The tests cover:
- ✅ Database connection handling
- ✅ User authentication with lockout mechanism
- ✅ Order lifecycle management
- ✅ Inventory stock tracking
- ✅ Seasonal crop validation
- ✅ Search and filtering algorithms
- ✅ Financial reporting
- ✅ Data import/export
- ✅ Password security
- ✅ Business rule enforcement

## Mocking Strategy

Tests use `unittest.mock` and `pytest-mock` to:
- Mock MongoDB connections and operations
- Isolate unit tests from database dependencies
- Test error conditions and edge cases
- Verify correct method calls and data transformations

## Continuous Integration

Tests are designed to run in CI/CD pipelines and can be executed without:
- Real database connections
- External dependencies
- Network access
- File system modifications

## Adding New Tests

When adding new functionality:

1. Create tests in `tests/test_*.py`
2. Use descriptive test names: `test_feature_scenario_expected_result`
3. Mock external dependencies
4. Test both success and failure paths
5. Include docstrings explaining test purpose
6. Run `pytest --cov` to check coverage