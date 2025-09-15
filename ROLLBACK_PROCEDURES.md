# Rollback Procedures for Final Touch Reorganization

## Backup Information
- **Backup Directory**: `backup_reorganization_20250820_032520/`
- **Backup Created**: 2025-08-20 03:25:20
- **Backup Size**: Complete repository state before reorganization

## Emergency Rollback Steps

### 1. Immediate Rollback (Complete Restoration)
If critical issues occur during reorganization:

```bash
# Stop any running processes
pkill -f python
pkill -f node

# Restore complete backup
rm -rf .git/index.lock 2>/dev/null || true
cp -r backup_reorganization_20250820_032520/* .
git checkout -- .
git clean -fd

# Verify restoration
git status
python -m pytest tests/ -q --tb=short
```

### 2. Selective File Rollback
To restore specific files or directories:

```bash
# Restore specific file
cp backup_reorganization_20250820_032520/path/to/file path/to/file

# Restore specific directory
rm -rf target_directory
cp -r backup_reorganization_20250820_032520/target_directory target_directory

# Verify changes
git diff
```

### 3. Git-Based Rollback
If changes are committed but need reverting:

```bash
# Find commit hash before reorganization
git log --oneline -10

# Revert to specific commit
git reset --hard <commit_hash>

# Or revert specific commits
git revert <commit_hash>
```

## Verification Procedures

### System Integrity Check
Run after any rollback to verify system state:

```bash
# Check repository structure
python tests/test_project_structure.py

# Verify core functionality
python -m pytest tests/database/test_connection.py -q
python -m pytest tests/visualization/test_data_loading.py -q

# Test CI configuration
.github/scripts/run-tests.sh
```

### Data Integrity Verification
```bash
# Check data files exist
ls -la data/processed/
ls -la visuals/public/data/

# Verify database connectivity
python scripts/utilities/check_cads_data_location.py

# Test visualization loading
cd visuals/public && python -m http.server 8000 &
curl -f http://localhost:8000/data/visualization-data.json
pkill -f "http.server"
```

## Recovery Scenarios

### Scenario 1: CI Pipeline Broken
**Symptoms**: GitHub Actions failing, tests not running
**Recovery**:
```bash
cp backup_reorganization_20250820_032520/.github/workflows/ci.yml .github/workflows/ci.yml
cp backup_reorganization_20250820_032520/.github/scripts/run-tests.sh .github/scripts/run-tests.sh
git add .github/
git commit -m "Restore CI configuration"
```

### Scenario 2: Database Tests Failing
**Symptoms**: Database connection errors, test failures
**Recovery**:
```bash
cp backup_reorganization_20250820_032520/tests/database/ tests/database/ -r
cp backup_reorganization_20250820_032520/tests/conftest.py tests/conftest.py
python -m pytest tests/database/ -q
```

### Scenario 3: Visualization Broken
**Symptoms**: Web interface not loading, data files missing
**Recovery**:
```bash
cp backup_reorganization_20250820_032520/visuals/ visuals/ -r
cp backup_reorganization_20250820_032520/index.html index.html
cp backup_reorganization_20250820_032520/app.js app.js
```

### Scenario 4: File Structure Corrupted
**Symptoms**: Missing files, broken imports, path errors
**Recovery**:
```bash
# Complete restoration (use emergency rollback)
cp -r backup_reorganization_20250820_032520/* .
git checkout -- .
git clean -fd
```

## Prevention Measures

### Before Each Major Change
1. Create checkpoint backup:
   ```bash
   timestamp=$(date +"%Y%m%d_%H%M%S")
   cp -r . "checkpoint_${timestamp}/"
   ```

2. Run verification tests:
   ```bash
   python -m pytest tests/ -q --tb=short
   ```

3. Document changes in progress log

### Automated Verification
The system includes automated verification scripts that should be run after any changes:

- `tests/test_project_structure.py` - Validates repository organization
- `tests/database/test_connection.py` - Verifies database connectivity
- `tests/visualization/test_data_loading.py` - Confirms visualization data integrity

## Contact Information
- **Primary Contact**: Development Team
- **Backup Contact**: System Administrator
- **Emergency Escalation**: Project Lead

## Notes
- Always test rollback procedures in a separate environment first
- Keep backup directory until reorganization is fully verified and stable
- Document any issues encountered during rollback for future reference
- Backup directory can be removed after 30 days of stable operation