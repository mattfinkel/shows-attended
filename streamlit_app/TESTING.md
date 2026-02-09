# Testing Guide

This document explains how to run tests for the Shows Attended app.

## Test Coverage

The test suite covers:

### 1. **Authentication** (`TestAuthentication`)
- Password hashing (SHA-256)
- Login flow
- Session persistence
- No-password mode

### 2. **Database Connection** (`TestDatabaseConnection`)
- Connection to Turso database
- Table existence verification
- Schema validation (primary_band_id column)

### 3. **Band Grouping** (`TestBandGrouping`)
- Primary bands query
- Grouped statistics (rolling up aliases)
- Band alias relationships

### 4. **Venue Operations** (`TestVenueOperations`)
- Closed venue field
- Venue statistics
- Location data

### 5. **Statistics Queries** (`TestStatsQueries`)
- Shows by year
- Top bands with grouping
- Overall counts (shows, bands, venues)

### 6. **Sorting** (`TestSortingQueries`)
- Bands sorted by count (descending)
- Bands sorted alphabetically
- Venues sorted by count (descending)
- Venues sorted alphabetically

## Running Tests

### Prerequisites

```bash
pip install pytest
```

### Local Testing

```bash
# Set your Turso database token
export TURSO_TEST_DB_TOKEN="your-auth-token-here"

# Run all tests
pytest test_app.py -v

# Run specific test class
pytest test_app.py::TestBandGrouping -v

# Run specific test
pytest test_app.py::TestAuthentication::test_hash_password -v
```

### Environment Variables

- `TURSO_TEST_DB_URL` - Database URL (defaults to production)
- `TURSO_TEST_DB_TOKEN` - Authentication token (required for database tests)

If no token is provided, database-dependent tests will be skipped.

## Test Output

Successful output example:
```
test_app.py::TestAuthentication::test_hash_password PASSED
test_app.py::TestAuthentication::test_hash_consistency PASSED
test_app.py::TestDatabaseConnection::test_connection PASSED
test_app.py::TestBandGrouping::test_grouped_band_stats PASSED
...
```

## CI/CD Integration

Add to GitHub Actions workflow:

```yaml
- name: Run tests
  env:
    TURSO_TEST_DB_TOKEN: ${{ secrets.TURSO_AUTH_TOKEN }}
  run: |
    pip install -r requirements.txt
    pytest test_app.py -v
```

## Adding New Tests

When adding new features, add corresponding tests:

1. **Create a test class** for the feature area
2. **Use fixtures** for database connections
3. **Test edge cases** and error conditions
4. **Keep tests independent** - each test should work in isolation

Example:
```python
class TestNewFeature:
    @pytest.fixture
    def db_client(self):
        return create_client_sync(url=..., auth_token=...)

    def test_feature_works(self, db_client):
        result = db_client.execute("SELECT ...")
        assert result is not None
```

## Troubleshooting

**"No module named 'pytest'"**
- Run: `pip install pytest`

**"No database token provided" - tests skipped**
- Set `TURSO_TEST_DB_TOKEN` environment variable

**Connection errors**
- Verify you're not on VPN (blocks WebSocket)
- Check token is still valid: `turso db tokens validate`

## Test Philosophy

- **Fast**: Tests should run quickly (< 10 seconds total)
- **Isolated**: Each test is independent
- **Deterministic**: Same inputs = same outputs
- **Meaningful**: Tests verify actual functionality, not implementation details
