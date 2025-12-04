# Run Pre-commit Checks

Run pre-commit hooks to check code quality for both Python backend and Vue/JavaScript frontend.

## Steps:

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

## Notes:
- Pre-commit hooks run in the host environment (venv) for Python tools
- ESLint runs in the Docker container via the custom hook script
- Some hooks auto-fix issues (black, isort, prettier, autoflake)
- Other hooks only report issues (flake8, eslint, vulture)
- Mypy is currently disabled due to types-all installation issues

## Error Handling:
- If Docker containers are not running, inform the user to run `docker-compose up -d`
- If venv doesn't exist, guide the user through setup
- If pre-commit is not installed, provide installation instructions
