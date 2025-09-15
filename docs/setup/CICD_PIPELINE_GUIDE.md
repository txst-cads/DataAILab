# CI/CD Pipeline Guide

This guide explains how the Continuous Integration and Continuous Deployment (CI/CD) pipeline works for the CADS Research Visualization System, including testing execution, deployment processes, and monitoring integration.

## 🏗️ Pipeline Architecture

The CI/CD pipeline is built using GitHub Actions and provides automated testing, security scanning, and deployment to Vercel. Here's how it works:

```mermaid
graph TB
    subgraph "Development"
        DEV[Developer Push] --> GIT[GitHub Repository]
    end
    
    subgraph "CI Pipeline"
        GIT --> TRIGGER[Workflow Trigger]
        TRIGGER --> SETUP[Environment Setup]
        SETUP --> LINT[Code Linting]
        LINT --> SECURITY[Security Scan]
        SECURITY --> DBTEST[Database Tests]
        DBTEST --> JSTEST[JavaScript Tests]
        JSTEST --> PIPELINE[Pipeline Tests]
        PIPELINE --> BUILD[Build Assets]
    end
    
    subgraph "CD Pipeline"
        BUILD --> DEPLOY{Deploy?}
        DEPLOY -->|Main Branch| VERCEL[Vercel Deploy]
        DEPLOY -->|Other Branch| SKIP[Skip Deploy]
        VERCEL --> HEALTH[Health Check]
        HEALTH --> NOTIFY[Notifications]
    end
    
    subgraph "Monitoring"
        VERCEL --> ANALYTICS[Vercel Analytics]
        VERCEL --> SENTRY[Sentry Monitoring]
    end
```

## 📁 Pipeline Configuration Files

### Main CI/CD Workflow (`.github/workflows/ci.yml`)

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        cd cads
        pip install -r requirements.txt
    
    - name: Run database tests
      run: |
        python -m pytest tests/database/ -q --tb=short
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/postgres
    
    - name: Run pipeline tests
      run: |
        python -m pytest tests/pipeline/ -q --tb=short
    
    - name: Run visualization tests
      run: |
        python -m pytest tests/visualization/ -q --tb=short

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Vercel
      uses: amondnet/vercel-action@v20
      with:
        vercel-token: ${{ secrets.VERCEL_TOKEN }}
        vercel-org-id: ${{ secrets.ORG_ID }}
        vercel-project-id: ${{ secrets.PROJECT_ID }}
        working-directory: ./visuals/public
```

### Security Scanning (`.github/workflows/security.yml`)

```yaml
name: Security Scan

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 0 * * 0'  # Weekly scan

jobs:
  security:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Run Bandit Security Scan
      run: |
        pip install bandit
        bandit -r cads/ scripts/ -f json -o bandit-report.json
    
    - name: Upload security results
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: bandit-report.json
```

### Dependency Updates (`.github/dependabot.yml`)

```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/cads"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
    
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

## 🧪 Testing Strategy

### Test Categories

The CI/CD pipeline runs four categories of tests:

#### 1. Database Tests (`tests/database/`)
- **Connection testing**: Verify database connectivity
- **Data integrity**: Validate data consistency and relationships
- **Query performance**: Ensure queries execute within reasonable time
- **Migration testing**: Verify schema changes work correctly

**Example test execution:**
```bash
python -m pytest tests/database/test_connection.py -q --tb=short
python -m pytest tests/database/test_data_integrity.py -q --tb=short
```

#### 2. Pipeline Tests (`tests/pipeline/`)
- **Full pipeline execution**: Run complete ML pipeline with sample data
- **Output validation**: Verify pipeline produces expected results
- **Performance testing**: Ensure pipeline completes within time limits
- **Error handling**: Test pipeline behavior with invalid data

**Example test execution:**
```bash
python -m pytest tests/pipeline/test_full_pipeline.py -q --tb=short
python -m pytest tests/pipeline/test_data_processing.py -q --tb=short
```

#### 3. Visualization Tests (`tests/visualization/`)
- **Rendering tests**: Verify visualizations render correctly
- **Interaction tests**: Test user interactions (filtering, search, etc.)
- **Data loading tests**: Ensure data loads and displays properly
- **HTML structure tests**: Validate HTML structure and required elements

**Example test execution:**
```bash
python -m pytest tests/visualization/test_rendering.py -q --tb=short
python -m pytest tests/visualization/test_interactions.py -q --tb=short
```

#### 4. Integration Tests
- **End-to-end workflow**: Test complete data processing to visualization flow
- **API integration**: Test external API connections (OpenAlex, Groq)
- **Cross-component**: Verify components work together correctly

### Test Execution Details

#### Local Test Execution

```bash
# Run all tests with minimal output
python tests/run_tests.py --all --quiet

# Run specific test categories
python tests/run_tests.py --database --quiet
python tests/run_tests.py --pipeline --quiet
python tests/run_tests.py --visualization --quiet

# Run individual test files
python -m pytest tests/database/test_connection.py -q --tb=short
```

#### CI Test Execution

The CI pipeline uses optimized test commands for faster execution:

```bash
# Database tests with timeout
timeout 300 python -m pytest tests/database/ -q --tb=short --maxfail=1

# Pipeline tests with sample data
python -m pytest tests/pipeline/ -q --tb=short --maxfail=1

# Visualization tests with headless browser
python -m pytest tests/visualization/ -q --tb=short --maxfail=1
```

### Test Data Management

#### Sample Data Strategy
- **Fixed test datasets**: Version-controlled sample data in `tests/fixtures/`
- **Synthetic data generation**: Create test data programmatically
- **Database fixtures**: Shared database setup and teardown

#### Test Environment Setup
```bash
# Set up test database
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/test_db
export OPENALEX_EMAIL=test@example.com
export LOG_LEVEL=ERROR  # Reduce test output noise
```

## 🚀 Deployment Process

### Vercel Deployment Configuration

The application deploys to Vercel with the following configuration (`vercel.json`):

```json
{
  "version": 2,
  "public": true,
  "github": {
    "enabled": true,
    "autoAlias": false
  },
  "builds": [
    {
      "src": "visuals/public/**",
      "use": "@vercel/static"
    }
  ],
  "routes": [
    {
      "src": "/data/(.*\\.gz)",
      "headers": {
        "Content-Encoding": "gzip",
        "Content-Type": "application/json",
        "Cache-Control": "public, max-age=31536000, immutable"
      }
    },
    {
      "src": "/data/(.*\\.json)",
      "headers": {
        "Content-Type": "application/json",
        "Cache-Control": "public, max-age=3600"
      }
    }
  ]
}
```

### Deployment Triggers

#### Automatic Deployment
- **Main branch**: Automatic deployment on successful tests
- **Pull requests**: Preview deployments for testing
- **Manual trigger**: Deploy button in GitHub Actions

#### Deployment Steps
1. **Code checkout**: Get latest code from repository
2. **Environment setup**: Configure Node.js and dependencies
3. **Asset building**: Prepare static files for deployment
4. **Vercel deployment**: Upload to Vercel CDN
5. **Health check**: Verify deployment is accessible
6. **Notification**: Send deployment status to team

### Environment Variables in Production

Required secrets in GitHub repository settings:

```bash
# Vercel Integration
VERCEL_TOKEN=your_vercel_token
ORG_ID=your_vercel_org_id
PROJECT_ID=your_vercel_project_id

# Database (for data processing)
DATABASE_URL=postgresql://user:pass@host:port/db

# API Keys
OPENALEX_EMAIL=your_email@domain.com
GROQ_API_KEY=your_groq_api_key

# Monitoring
SENTRY_DSN=your_sentry_dsn
SENTRY_AUTH_TOKEN=your_sentry_auth_token
```

## 📊 Monitoring and Observability

### Vercel Analytics Integration

Automatic performance monitoring includes:
- **Page load times**: Core Web Vitals tracking
- **User interactions**: Click and navigation tracking
- **Geographic data**: User location and performance by region
- **Device analytics**: Browser and device usage patterns

### Sentry Error Tracking

Comprehensive error monitoring:
- **JavaScript errors**: Automatic error capture and reporting
- **Performance monitoring**: Frontend performance tracking
- **Release tracking**: Monitor errors by deployment version
- **User context**: Track errors with user and session data

### GitHub Actions Monitoring

CI/CD pipeline monitoring:
- **Build status**: Track success/failure rates
- **Test results**: Monitor test execution and coverage
- **Deployment history**: Track deployment frequency and success
- **Performance metrics**: Build and test execution times

## 🔧 Pipeline Maintenance

### Regular Maintenance Tasks

#### Weekly
- Review test results and fix any flaky tests
- Update dependencies using Dependabot PRs
- Check deployment success rates and performance
- Review security scan results

#### Monthly
- Analyze test coverage and add missing tests
- Review and optimize CI/CD pipeline performance
- Update GitHub Actions versions
- Review monitoring alerts and thresholds

#### Quarterly
- Comprehensive security audit
- Performance optimization review
- Documentation updates
- Disaster recovery testing

### Pipeline Optimization

#### Speed Improvements
```yaml
# Cache dependencies
- name: Cache pip dependencies
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}

# Parallel test execution
- name: Run tests in parallel
  run: |
    python -m pytest tests/ -n auto --tb=short
```

#### Resource Optimization
```yaml
# Use matrix strategy for multiple Python versions
strategy:
  matrix:
    python-version: [3.8, 3.9, '3.10']
    
# Conditional job execution
if: github.event_name == 'push' && github.ref == 'refs/heads/main'
```

## 🚨 Troubleshooting CI/CD Issues

### Common Pipeline Failures

#### 1. Test Failures
**Problem**: Tests failing in CI but passing locally

**Solutions**:
```bash
# Run tests with same environment as CI
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres
python -m pytest tests/ -q --tb=short

# Check for timing issues
python -m pytest tests/ --timeout=300

# Verify test data and fixtures
ls -la tests/fixtures/
```

#### 2. Deployment Failures
**Problem**: Vercel deployment fails

**Solutions**:
```bash
# Check Vercel configuration
vercel --version
vercel whoami

# Test deployment locally
cd visuals/public
vercel --prod

# Verify environment variables
echo $VERCEL_TOKEN
```

#### 3. Security Scan Issues
**Problem**: Security vulnerabilities detected

**Solutions**:
```bash
# Run security scan locally
pip install bandit safety
bandit -r cads/ scripts/
safety check

# Update vulnerable dependencies
pip install --upgrade package_name
```

### Pipeline Debugging

#### Enable Debug Logging
```yaml
- name: Debug pipeline
  run: |
    echo "Runner OS: ${{ runner.os }}"
    echo "Python version: $(python --version)"
    echo "Working directory: $(pwd)"
    ls -la
  env:
    ACTIONS_STEP_DEBUG: true
```

#### Access Pipeline Artifacts
```yaml
- name: Upload test results
  uses: actions/upload-artifact@v3
  if: always()
  with:
    name: test-results
    path: |
      test-results.xml
      coverage.xml
      logs/
```

## 📚 Additional Resources

### Documentation Links
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Vercel Deployment Guide](https://vercel.com/docs)
- [Pytest Testing Framework](https://docs.pytest.org/)
- [Sentry Monitoring Setup](../monitoring/MONITORING_SETUP.md)

### Configuration Examples
- [Complete CI/CD workflow](../../.github/workflows/ci.yml)
- [Security scanning setup](../../.github/workflows/security.yml)
- [Vercel configuration](../../vercel.json)
- [Test configuration](../../pytest.ini)

---

**🎯 CI/CD Pipeline Ready**

Your CI/CD pipeline provides automated testing, security scanning, and deployment with comprehensive monitoring. The system ensures code quality and reliable deployments while maintaining fast feedback cycles for development teams.