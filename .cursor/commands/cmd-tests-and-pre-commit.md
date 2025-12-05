# Run Tests and Pre-commit Checks

Comprehensive guide for running tests, fixing failures, and improving code coverage for both FastAPI backend and Vue frontend.

## Pre-commit Checks

### Steps:

1. **Activate the virtual environment** (if not already activated):
   - Check if `venv/bin/activate` exists in the project root
   - If it exists, activate it: `source venv/bin/activate`
   - If it doesn't exist, inform the user they need to run `./scripts/setup-pre-commit.sh` first

2. **Check if pre-commit is installed**:
   - Run `pre-commit --version` to verify installation
   - If not installed, inform the user to run: `pip install pre-commit` in the venv

3. **Run pre-commit checks**:
   - Execute: `pre-commit run --all-files`
   - Capture both stdout and stderr
   - Show the output to the user

4. **Interpret results**:
   - If all hooks pass: Inform the user that all checks passed
   - If hooks fail:
     - Identify which hooks failed (black, isort, flake8, prettier, eslint, etc.)
     - For auto-fixable hooks (black, isort, prettier): Suggest running them again to auto-fix
     - For linting hooks (flake8, eslint): Show the specific errors and suggest fixes
     - Provide commands to fix issues:
       - Python: `pre-commit run black isort --all-files` (auto-fixes)
       - Frontend: `cd frontend && docker-compose exec frontend npm run lint:fix` (auto-fixes ESLint issues)

5. **Auto-fix mode**:
   - run:
     - `pre-commit run black isort prettier autoflake --all-files` (these auto-fix)
     - Then show remaining issues that need manual fixes

## FastAPI Backend Tests

### Running All Tests

1. **Run all tests in Docker container**:
   ```bash
   docker compose exec backend pytest
   ```

2. **Run tests with coverage report**:
   ```bash
   docker compose exec backend pytest --cov=app --cov-report=term --cov-report=html
   ```

3. **Run specific test file**:
   ```bash
   docker compose exec backend pytest app/tests/test_security.py
   ```

4. **Run tests with verbose output**:
   ```bash
   docker compose exec backend pytest -v
   ```

5. **Run tests and show coverage in terminal**:
   ```bash
   docker compose exec backend pytest --cov=app --cov-report=term-missing
   ```

### Fixing Missing/Failing Tests

1. **Identify failing tests**:
   - Run: `docker compose exec backend pytest -v`
   - Review the output to identify which tests are failing
   - Check error messages and stack traces

2. **Fix test failures**:
   - Read the error message carefully
   - Check if it's a missing dependency, incorrect assertion, or code change
   - Update the test file accordingly
   - Re-run the specific test: `docker compose exec backend pytest app/tests/test_<name>.py::test_<function> -v`

3. **Add missing tests**:
   - Review `backend/app/tests/` directory structure
   - Identify modules without tests (check `backend/app/` for untested files)
   - Create new test files following the pattern: `test_<module_name>.py`
   - Use existing tests as templates (see `test_security.py`, `test_main.py`, etc.)

4. **Common test patterns**:
   - Mock database sessions: Use `AsyncMock` and `MagicMock` from `unittest.mock`
   - Mock authentication: Override `current_active_user` dependency
   - Test async endpoints: Use `@pytest.mark.asyncio` decorator
   - Use fixtures: Check `conftest.py` for available fixtures like `client`

### Increasing Code Coverage

1. **Check current coverage**:
   ```bash
   docker compose exec backend pytest --cov=app --cov-report=term-missing
   ```
   - Look for files with low coverage percentage
   - Check the "Missing" column to see which lines aren't covered

2. **Generate HTML coverage report**:
   ```bash
   docker compose exec backend pytest --cov=app --cov-report=html
   ```
   - Open `backend/htmlcov/index.html` in a browser
   - Click on files to see which lines are not covered

3. **Target low-coverage areas**:
   - Focus on files with < 80% coverage
   - Add tests for:
     - Error handling paths
     - Edge cases
     - Different input validations
     - All branches in if/else statements

4. **Coverage goals**:
   - Aim for at least 80% overall coverage
   - Critical paths (auth, security, business logic) should be 90%+
   - Configuration and utilities can be lower (60-70%)

5. **Exclude patterns** (already configured in `pytest.ini`):
   - Test files themselves
   - Migration files
   - `__pycache__` directories

## Vue Frontend Tests

### Running All Tests

1. **Run all tests in Docker container**:
   ```bash
   docker compose exec frontend npm test
   ```

2. **Run tests in watch mode** (for development):
   ```bash
   docker compose exec frontend npm run test:watch
   ```

3. **Run tests with coverage**:
   ```bash
   docker compose exec frontend npm run test:coverage
   ```

4. **Run tests with UI** (interactive):
   ```bash
   docker compose exec frontend npm run test:ui
   ```

### Fixing Missing/Failing Tests

1. **Identify failing tests**:
   - Run: `docker compose exec frontend npm test`
   - Review the output to see which tests fail
   - Check error messages and component issues

2. **Fix test failures**:
   - Read error messages carefully
   - Check if it's a missing import, incorrect assertion, or component change
   - Update the test file in `frontend/src/tests/`
   - Re-run tests: `docker compose exec frontend npm test`

3. **Add missing tests**:
   - Review `frontend/src/tests/` directory
   - Identify components without tests (check `frontend/src/views/` and `frontend/src/components/`)
   - Create test files following the pattern: `*.test.js` or `*.spec.js`
   - Use existing tests as templates

4. **Common test patterns**:
   - Use `@vue/test-utils` for component testing
   - Use `@testing-library/vue` for user-centric testing
   - Mock API calls: Use `vi.mock()` or `jest.mock()`
   - Test user interactions: Use `fireEvent` or `userEvent`

### Increasing Code Coverage

1. **Check current coverage**:
   ```bash
   docker compose exec frontend npm run test:coverage
   ```
   - Review the terminal output for coverage percentages
   - Check `frontend/coverage/` directory for HTML reports

2. **View HTML coverage report**:
   - After running `npm run test:coverage`
   - Open `frontend/coverage/index.html` in a browser
   - Navigate through files to see uncovered lines

3. **Target low-coverage areas**:
   - Focus on components with < 80% coverage
   - Add tests for:
     - Component rendering
     - User interactions (clicks, form submissions)
     - Conditional rendering (v-if, v-show)
     - Event handlers
     - Computed properties
     - Methods

4. **Coverage goals** (configured in `vite.config.js`):
   - Statements: 80%
   - Branches: 75%
   - Functions: 80%
   - Lines: 80%

5. **Exclude patterns** (already configured in `vite.config.js`):
   - Test files
   - Config files
   - `node_modules/`
   - `dist/`
   - `main.js`, `router.js`, `style.css`

## Test Workflow

### Complete Test Suite Run

1. **Backend tests**:
   ```bash
   docker compose exec backend pytest --cov=app --cov-report=term-missing
   ```

2. **Frontend tests**:
   ```bash
   docker compose exec frontend npm run test:coverage
   ```

3. **Pre-commit checks**:
   ```bash
   source venv/bin/activate
   pre-commit run --all-files
   ```

### Before Committing

1. Run all backend tests and ensure they pass
2. Run all frontend tests and ensure they pass
3. Run pre-commit hooks to catch formatting/linting issues
4. Fix any failing tests or pre-commit issues
5. Re-run tests to verify fixes

## Notes:

- Pre-commit hooks run in the host environment (venv) for Python tools
- ESLint runs in the Docker container via the custom hook script
- Some hooks auto-fix issues (black, isort, prettier, autoflake)
- Other hooks only report issues (flake8, eslint, vulture)
- Mypy is currently disabled due to types-all installation issues
- Backend tests use pytest with pytest-asyncio for async support
- Frontend tests use Vitest with jsdom environment
- Coverage reports are generated in `backend/htmlcov/` and `frontend/coverage/`

## Error Handling:

- If Docker containers are not running, inform the user to run `docker-compose up -d`
- If venv doesn't exist, guide the user through setup
- If pre-commit is not installed, provide installation instructions
- If tests fail, show specific error messages and suggest fixes
- If coverage is low, identify specific files and lines that need testing
