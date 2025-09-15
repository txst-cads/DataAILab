# GitHub Actions Setup Guide

This document explains how to configure the required secrets and environment variables for the CI/CD pipeline.

## Required Secrets

Navigate to your repository's Settings > Environments > cads-research > Environment secrets, then add the following secrets:

**Important**: Secrets must be added to the `cads-research` environment, not repository-level secrets, as both test and deploy jobs target this environment.

### Vercel Deployment Secrets

1. **VERCEL_TOKEN**
   - Go to [Vercel Dashboard](https://vercel.com/account/tokens)
   - Create a new token with appropriate scope
   - Copy the token value

2. **VERCEL_ORG_ID**
   - Found in your Vercel team/organization settings
   - Or run `vercel org ls` in your local terminal

3. **VERCEL_PROJECT_ID**
   - Found in your Vercel project settings
   - Or run `vercel project ls` in your local terminal

4. **VERCEL_DEPLOYMENT_URL**
   - Your production deployment URL (e.g., `https://your-app.vercel.app`)
   - Used for health checks after deployment

### Database Secrets (Optional for Production Tests)

5. **DATABASE_URL** (Optional)
   - Production database connection string
   - Format: `postgresql://user:password@host:port/database`
   - Only needed if running tests against production database

6. **OPENALEX_EMAIL** (Optional)
   - Email address for OpenAlex API requests
   - Required for data processing pipeline tests

## Environment Variables

The following environment variables are automatically set by the workflow:

- `NODE_VERSION`: Node.js version (currently 18)
- `PYTHON_VERSION`: Python version (currently 3.9)
- `DATABASE_URL`: Test database URL (for CI tests)
- `OPENALEX_EMAIL`: Test email (for CI tests)

## Workflow Triggers

### Main CI/CD Workflow (`ci.yml`)
- **Push to main/develop**: Runs full test suite and deploys to production (main only)
- **Pull requests to main**: Runs full test suite without deployment

### Security Workflow (`security.yml`)
- **Push to main/develop**: Runs security scans
- **Pull requests to main**: Runs dependency review
- **Daily schedule**: Runs comprehensive security checks

## Test Configuration

The CI pipeline runs the following tests:

1. **Database Tests**: Connection and data integrity tests
2. **Data Processing Tests**: ML pipeline component tests
3. **Pipeline Integration Test**: Full end-to-end pipeline test
4. **JavaScript Visualization Tests**: Frontend functionality tests

## Deployment Process

1. Tests must pass on all components
2. Security scans must complete (warnings allowed)
3. Automatic deployment to Vercel on main branch
4. Health check verification after deployment
5. Rollback capability through Vercel dashboard

## Environment Configuration

### GitHub Environment Setup

1. Go to Repository Settings > Environments
2. Create or select the `cads-research` environment
3. Add environment protection rules (optional):
   - Required reviewers for production deployments
   - Deployment branches: `main` only
   - Wait timer: 0 minutes (for immediate deployment)

### Environment Variables vs Repository Secrets

- **Environment Secrets**: Used for deployment credentials (Vercel tokens)
- **Repository Secrets**: Used for general CI/CD secrets (database URLs, API keys)

## Troubleshooting

### Common Issues

1. **Missing Secrets**: Ensure all required secrets are configured in the `cads-research` environment
2. **Environment Mismatch**: Verify both test and deploy jobs target the same environment
3. **Test Failures**: Check test logs for specific error messages
4. **Deployment Failures**: Verify Vercel configuration and secrets
5. **Health Check Failures**: Confirm deployment URL is accessible

### Debug Steps

1. Check GitHub Actions logs for detailed error messages
2. Verify secret names match exactly (case-sensitive)
3. Test Vercel deployment locally using `vercel --prod`
4. Run tests locally to reproduce CI failures

## Security Considerations

- Secrets are encrypted and only accessible during workflow execution
- Database credentials use test database, not production
- Security scans run automatically and report vulnerabilities
- Dependency updates are monitored through Dependabot

## Manual Deployment

If automatic deployment fails, you can deploy manually:

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy to production
vercel --prod --token $VERCEL_TOKEN
```

## Monitoring

- GitHub Actions provides build status and history
- Vercel dashboard shows deployment status and logs
- Security alerts appear in repository security tab
- Failed builds trigger email notifications to repository maintainers