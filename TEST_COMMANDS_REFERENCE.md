# UniLink E2E Test Commands Reference

Quick reference for running E2E tests in various configurations.

## Basic Commands

### Run All Tests (Verbose)
```bash
cd backend
.\venv\Scripts\python.exe -m pytest tests/test_calls_simple.py tests/test_e2e_workflows.py -v
```

### Run All Tests (Quiet)
```bash
.\venv\Scripts\python.exe -m pytest tests/ -q
```

### Run E2E Tests Only
```bash
.\venv\Scripts\python.exe -m pytest tests/test_e2e_workflows.py -v
```

### Run Unit Tests Only
```bash
.\venv\Scripts\python.exe -m pytest tests/test_calls_simple.py -v
```

## Test Selection

### Run Specific Test Class
```bash
.\venv\Scripts\python.exe -m pytest tests/test_e2e_workflows.py::TestCompleteUserJourney -v
```

### Run Specific Test Method
```bash
.\venv\Scripts\python.exe -m pytest tests/test_e2e_workflows.py::TestCompleteUserJourney::test_full_call_workflow -v
```

### Run Tests Matching Pattern
```bash
.\venv\Scripts\python.exe -m pytest tests/ -k "workflow" -v
```

### Run All Registration Tests
```bash
.\venv\Scripts\python.exe -m pytest tests/ -k "registration" -v
```

### Run All User Discovery Tests
```bash
.\venv\Scripts\python.exe -m pytest tests/ -k "discovery" -v
```

## Coverage Reports

### Coverage Summary
```bash
.\venv\Scripts\python.exe -m pytest tests/ --cov=app --cov-report=term-missing
```

### HTML Coverage Report
```bash
.\venv\Scripts\python.exe -m pytest tests/ --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

### Coverage for Specific Module
```bash
.\venv\Scripts\python.exe -m pytest tests/ --cov=app.utils.call_service --cov-report=term
```

## Detailed Output

### Show Print Statements
```bash
.\venv\Scripts\python.exe -m pytest tests/ -v -s
```

### Show Local Variables on Failure
```bash
.\venv\Scripts\python.exe -m pytest tests/ -v -l
```

### Full Traceback
```bash
.\venv\Scripts\python.exe -m pytest tests/ --tb=long
```

### Short Traceback (default)
```bash
.\venv\Scripts\python.exe -m pytest tests/ --tb=short
```

## Performance Testing

### Show Slowest Tests
```bash
.\venv\Scripts\python.exe -m pytest tests/ --durations=10
```

### Exit on First Failure
```bash
.\venv\Scripts\python.exe -m pytest tests/ -x
```

### Stop After N Failures
```bash
.\venv\Scripts\python.exe -m pytest tests/ --maxfail=3
```

### Last Failed Tests (requires first run)
```bash
.\venv\Scripts\python.exe -m pytest tests/ --lf
```

## Parallel Execution

### Install pytest-xdist
```bash
.\venv\Scripts\pip install pytest-xdist
```

### Run Tests in Parallel (Auto CPU Count)
```bash
.\venv\Scripts\python.exe -m pytest tests/ -n auto
```

### Run Tests in Parallel (4 workers)
```bash
.\venv\Scripts\python.exe -m pytest tests/ -n 4
```

## Debugging

### Debug Mode (detailed output)
```bash
.\venv\Scripts\python.exe -m pytest tests/ -v --tb=long -s
```

### Stop on First Failure with PDB
```bash
.\venv\Scripts\python.exe -m pytest tests/ -x --pdb
```

### Post-Mortem Debug on Failure
```bash
.\venv\Scripts\python.exe -m pytest tests/ --pdb-trace
```

## Markers and Tags

### Run Only Tests with Specific Mark
```bash
.\venv\Scripts\python.exe -m pytest tests/ -m "slow" -v
```

### Skip Tests with Specific Mark
```bash
.\venv\Scripts\python.exe -m pytest tests/ -m "not slow" -v
```

## Output Formats

### JUnit XML (for CI/CD)
```bash
.\venv\Scripts\python.exe -m pytest tests/ --junit-xml=test-results.xml
```

### JSON Report
```bash
.\venv\Scripts\python.exe -m pytest tests/ --json-report --json-report-file=report.json
```

### HTML Report
```bash
.\venv\Scripts\pip install pytest-html
.\venv\Scripts\python.exe -m pytest tests/ --html=report.html
```

## Complex Scenarios

### Run All Tests with Full Report
```bash
.\venv\Scripts\python.exe -m pytest tests/ -v --cov=app --cov-report=html --durations=10
```

### CI/CD Integration Run
```bash
.\venv\Scripts\python.exe -m pytest tests/ -v --junit-xml=test-results.xml --cov=app --cov-report=term-missing
```

### Development Watch Mode
```bash
.\venv\Scripts\pip install pytest-watch
.\venv\Scripts\ptw tests/ -- -v -s
```

### Continuous Running (pytest-repeat)
```bash
.\venv\Scripts\pip install pytest-repeat
.\venv\Scripts\python.exe -m pytest tests/ --count=5
```

## Individual Test Classes

### All Registration Tests
```bash
.\venv\Scripts\python.exe -m pytest tests/test_e2e_workflows.py::TestUserRegistrationFlow -v
```

### All Login Tests
```bash
.\venv\Scripts\python.exe -m pytest tests/test_e2e_workflows.py::TestUserLoginFlow -v
```

### All Discovery Tests
```bash
.\venv\Scripts\python.exe -m pytest tests/test_e2e_workflows.py::TestUserDiscoveryFlow -v
```

### All Call Initiation Tests
```bash
.\venv\Scripts\python.exe -m pytest tests/test_e2e_workflows.py::TestCallInitiationFlow -v
```

### All Complete Journey Tests
```bash
.\venv\Scripts\python.exe -m pytest tests/test_e2e_workflows.py::TestCompleteUserJourney -v
```

### All Call History Tests
```bash
.\venv\Scripts\python.exe -m pytest tests/test_e2e_workflows.py::TestCallHistory -v
```

## Setup and Teardown

### Show Test Setup/Teardown
```bash
.\venv\Scripts\python.exe -m pytest tests/ -v --setup-show
```

### Show Only Setup
```bash
.\venv\Scripts\python.exe -m pytest tests/ -v --setup-only
```

### Show Only Tests
```bash
.\venv\Scripts\python.exe -m pytest tests/ --collect-only
```

## Troubleshooting Commands

### Verify Virtual Environment
```bash
.\venv\Scripts\python.exe -m pip list
```

### Install Test Dependencies
```bash
.\venv\Scripts\pip install -r requirements-dev.txt
```

### Check Python Version
```bash
.\venv\Scripts\python.exe --version
```

### Run Single Test for Debugging
```bash
.\venv\Scripts\python.exe -m pytest tests/test_e2e_workflows.py::TestUserRegistrationFlow::test_user_registration -v -s
```

## Quick Aliases (Add to profile)

```powershell
# In $PROFILE
function pytest_all { & ".\venv\Scripts\python.exe" -m pytest tests/ -v }
function pytest_coverage { & ".\venv\Scripts\python.exe" -m pytest tests/ --cov=app --cov-report=html }
function pytest_fast { & ".\venv\Scripts\python.exe" -m pytest tests/ -n auto }
function pytest_debug { & ".\venv\Scripts\python.exe" -m pytest tests/ -v -s --tb=long }
```

Usage:
```bash
pytest_all
pytest_coverage
pytest_fast
pytest_debug
```

## Expected Output

### Successful Run
```
============================= test session starts ==============================
platform win32 -- Python 3.12.5, pytest-9.0.2, pluggy-1.6.0
collected 26 items

tests/test_calls_simple.py::test_create_call PASSED                        [  3%]
tests/test_calls_simple.py::test_accept_call PASSED                        [  7%]
...
tests/test_e2e_workflows.py::TestCallHistory::test_call_duration_tracking PASSED [100%]

============================== 26 passed in 14.90s ==============================
```

## Common Issues & Solutions

### `ModuleNotFoundError: No module named 'pytest'`
```bash
.\venv\Scripts\pip install pytest pytest-asyncio
```

### `ImportError: No module named 'app'`
```bash
cd backend
.\venv\Scripts\python.exe -m pytest tests/ -v
```

### `FAILED: 0 passed, 1 error in 1.02s`
```bash
# Check virtual environment is activated
.\venv\Scripts\activate
# Or run Python directly from venv
.\venv\Scripts\python.exe -m pytest tests/ -v
```

### Tests Pass Locally But Fail in CI
```bash
# Run with same Python version as CI
.\venv\Scripts\python.exe --version  # Should be 3.12.5
```

## File Locations

- Test files: `backend/tests/`
- Main tests: `backend/tests/test_e2e_workflows.py`
- Unit tests: `backend/tests/test_calls_simple.py`
- Documentation: `backend/tests/E2E_TEST_DOCUMENTATION.md`
- README: `backend/tests/README.md`
- Coverage report: `backend/htmlcov/index.html` (after running coverage)

## More Information

- Full documentation: `backend/tests/E2E_TEST_DOCUMENTATION.md`
- Test README: `backend/tests/README.md`
- pytest docs: https://docs.pytest.org
- Coverage docs: https://coverage.readthedocs.io
