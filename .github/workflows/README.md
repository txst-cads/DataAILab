# GitHub Actions Workflows

This directory contains the CI/CD pipeline configuration for the CADS Research Visualization System.

## Workflow Status

[![CI/CD Pipeline](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci.yml)
[![Security Checks](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/security.yml/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/security.yml)

## Workflows Overview

### 1. CI/CD Pipeline (`ci.yml`)
**Purpose**: Main testing and deployment workflow

**Triggers**:
- Push to `main` or `develop` branches
- Pull requests to `main` branch

**Jobs**:
- **Test Job**: Runs comprehensive test suite
  - Database connectivity tests
  - Data processing pipeline tests
  - ML pipeline integration tests
  - JavaScript visualization tests
- **Deploy Job**: Automatic deployment to Vercel (main branch only)
  - Deploys on successful tests
  - Performs health check validation

**Duration**: ~5-8 minutes

### 2. Security Checks (`security.yml`)
**Purpose**: Security scanning and dependency monitoring

**Triggers**:
- Push to `main` or `develop` branches
- Pull requests to `main` branch
- Daily schedule (2 AM UTC)

**Jobs**:
- **Security Scan**: Python security analysis
  - Safety check for known vulnerabilities
  - Bandit static security analysis
  - CodeQL analysis for Python and JavaScript
- **Dependency Review**: PR-based dependency analysis

**Duration**: ~3-5 minutes

### 3. Dependabot (`dependabot.yml`)
**Purpose**: Automated dependency updates

**Schedule**: Weekly on Mondays at 9 AM UTC

**Scope**:
- Python dependencies in `/cads` directory
- GitHub Actions workflow dependencies

## Test Strategy

### Database Tests
- PostgreSQL service container for isolated testing
- Connection validation and basic query tests
- Test database automatically created and destroyed

### Python Pipeline Tests
- ML pipeline component testing
- Data processing validation
- Integration tests with sample data
- Minimal output mode for CI efficiency

### JavaScript Tests
- HTML structure validation
- Basic visualization functionality
- Static file integrity checks

## Deployment Strategy

### Automatic Deployment
- Triggered only on `main` branch pushes
- Requires all tests to pass
- Uses Vercel for static site deployment
- Includes post-deployment health checks

### Manual Deployment
- Available through Vercel CLI
- Documented in setup guide
- Useful for hotfixes or rollbacks

## Security Features

### Automated Scanning
- Daily security vulnerability checks
- Dependency review on pull requests
- Static code analysis with Bandit
- CodeQL analysis for multiple languages

### Secret Management
- Encrypted GitHub secrets for sensitive data
- Environment-specific configuration
- No hardcoded credentials in workflows

## Performance Optimizations

### Caching
- Python pip cache for faster dependency installation
- Node.js cache for frontend dependencies
- Docker layer caching for service containers

### Parallel Execution
- Test jobs run in parallel where possible
- Security scans run independently
- Minimal test output to prevent timeouts

## Monitoring and Alerts

### Build Status
- Workflow badges in README
- Email notifications on failures
- GitHub status checks for pull requests

### Security Alerts
- Dependabot security advisories
- CodeQL security findings
- Automated dependency update PRs

## Troubleshooting

### Common Issues
1. **Test timeouts**: Use minimal output flags (`-q`, `--tb=short`)
2. **Secret errors**: Verify secret names and values in repository settings
3. **Deployment failures**: Check Vercel configuration and project settings

### Debug Resources
- GitHub Actions logs with detailed error messages
- Vercel deployment logs and dashboard
- Local testing with same environment variables

## Configuration Files

- `ci.yml`: Main CI/CD pipeline
- `security.yml`: Security and quality checks
- `dependabot.yml`: Dependency update configuration
- `SETUP.md`: Detailed setup instructions

## Best Practices

- Keep workflows focused and fast
- Use minimal test output in CI
- Cache dependencies when possible
- Separate concerns (testing vs. security vs. deployment)
- Document all required secrets and setup steps