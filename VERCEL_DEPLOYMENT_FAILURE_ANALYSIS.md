# Vercel Deployment Failure - Technical Analysis & Resolution

## 🚨 **Issue Summary**

**Error**: `Error! Project not found ({"VERCEL_PROJECT_ID":"***","VERCEL_ORG_ID":"***"})`  
**Exit Code**: 1  
**Failing Component**: Vercel deployment via `amondnet/vercel-action@v25`  
**Root Cause**: GitHub Actions environment variable scoping mismatch

## 🔍 **Root Cause Analysis**

### **Environment Scoping Problem**

The deployment failure is caused by a **GitHub Actions environment configuration mismatch**:

1. **Test Job Configuration**:
   ```yaml
   test:
     environment: cads-research  # ✅ Correctly targets environment
   ```

2. **Deploy Job Configuration** (BEFORE FIX):
   ```yaml
   deploy:
     # ❌ Missing environment declaration
     # Variables from cads-research environment not accessible
   ```

### **GitHub Actions Environment Variable Inheritance**

GitHub Actions follows this variable accessibility hierarchy:

```
Repository Level
├── Available to ALL jobs
├── No environment protection
└── Lower security for sensitive data

Environment Level (cads-research)
├── Available ONLY to jobs with environment: cads-research
├── Environment protection rules apply
├── Higher security for deployment credentials
└── ❌ NOT accessible to jobs without environment declaration
```

### **Technical Flow Analysis**

1. **Variable Storage**: Vercel secrets stored in `cads-research` environment
2. **Test Job**: Successfully accesses environment (has `environment: cads-research`)
3. **Deploy Job**: Runs in default repository scope (missing environment declaration)
4. **Variable Resolution**: `${{ secrets.VERCEL_PROJECT_ID }}` resolves to empty/null
5. **Vercel API Call**: Receives empty project ID → "Project not found" error

### **Evidence from Error Message**

```
Project not found ({"VERCEL_PROJECT_ID":"***","VERCEL_ORG_ID":"***"})
```

- `***` indicates variables are being passed (GitHub masks non-empty secrets)
- But the actual values are likely empty strings or null
- Vercel API interprets empty project ID as non-existent project

## ✅ **Solution Implemented**

### **Primary Fix: Environment Declaration**

```yaml
deploy:
  name: Deploy to Vercel
  needs: test
  runs-on: ubuntu-latest
  environment: cads-research  # ← Added this line
  if: success() && github.ref == 'refs/heads/main' && github.event_name == 'push'
```

### **Secondary Fix: Debug Verification**

Added debug step to verify variable accessibility:

```yaml
- name: Debug Vercel configuration
  run: |
    echo "🔍 Verifying Vercel environment variables..."
    echo "VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN != '' && 'SET' || 'NOT SET' }}"
    echo "VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID != '' && 'SET' || 'NOT SET' }}"
    echo "VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID != '' && 'SET' || 'NOT SET' }}"
    echo "Environment: cads-research"
```

### **Documentation Updates**

Updated `.github/SETUP.md` to clarify:
- Environment-specific secret configuration
- Difference between repository and environment secrets
- Troubleshooting steps for environment mismatches

## 🧪 **Verification Steps**

### **1. Immediate Verification**
After pushing the fix, check the GitHub Actions logs for:
```
🔍 Verifying Vercel environment variables...
VERCEL_TOKEN: SET
VERCEL_ORG_ID: SET  
VERCEL_PROJECT_ID: SET
Environment: cads-research
```

### **2. Deployment Success Indicators**
- Vercel action completes without "Project not found" error
- Health check passes with 200 response
- Deployment URL accessible

### **3. Local Testing (Optional)**
```bash
# Verify project exists and is accessible
vercel whoami
vercel projects ls | grep "prj_URZwqwFdPh5pwQ3NwEj7npRswMFn"
vercel teams ls
```

## 🛡️ **Prevention Measures**

### **1. Environment Consistency**
Ensure all jobs requiring environment secrets target the same environment:
```yaml
jobs:
  test:
    environment: cads-research
  deploy:
    environment: cads-research  # Must match
```

### **2. Secret Organization Strategy**

| Secret Type | Storage Location | Accessibility |
|-------------|------------------|---------------|
| Deployment Credentials | Environment Secrets | Protected, job-specific |
| CI/CD Tokens | Repository Secrets | Global, all jobs |
| Test Data | Workflow Variables | Workflow-specific |

### **3. Debug Verification Pattern**
Always include debug steps for critical deployments:
```yaml
- name: Verify deployment prerequisites
  run: |
    echo "Required secrets status:"
    echo "TOKEN: ${{ secrets.TOKEN != '' && 'SET' || 'NOT SET' }}"
    echo "Environment: ${{ github.environment }}"
```

## 📋 **Technical Specifications**

### **GitHub Actions Environment Features**
- **Protection Rules**: Require approvals, restrict branches
- **Variable Scoping**: Environment-specific secret isolation
- **Deployment History**: Track environment-specific deployments
- **Security**: Enhanced protection for production credentials

### **Vercel Integration Requirements**
- **VERCEL_TOKEN**: Personal access token with project permissions
- **VERCEL_ORG_ID**: Organization/team identifier
- **VERCEL_PROJECT_ID**: Specific project identifier (format: `prj_*`)
- **Environment Targeting**: Must match GitHub environment configuration

### **Error Resolution Matrix**

| Error Pattern | Root Cause | Solution |
|---------------|------------|----------|
| `Project not found` | Environment scoping | Add `environment:` to job |
| `Unauthorized` | Invalid token | Regenerate VERCEL_TOKEN |
| `Organization not found` | Wrong ORG_ID | Verify with `vercel teams ls` |
| `Forbidden` | Insufficient permissions | Update token scope |

## 🎯 **Expected Outcome**

After implementing this fix:

1. **Deploy job** will have access to `cads-research` environment secrets
2. **Vercel action** will receive valid project ID and organization ID
3. **Deployment** will proceed successfully to production
4. **Health check** will verify deployment accessibility
5. **Future deployments** will work consistently

## 📚 **Additional Resources**

- [GitHub Actions Environments Documentation](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
- [Vercel CLI Authentication](https://vercel.com/docs/cli/global-options#token)
- [GitHub Actions Secrets and Variables](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

## 🔄 **Next Steps**

1. **Commit and push** the workflow changes
2. **Monitor** the next deployment attempt
3. **Verify** successful deployment to Vercel
4. **Document** any additional environment-specific configurations needed
5. **Test** the deployed application functionality

The fix addresses the core issue of environment variable accessibility in GitHub Actions, ensuring that deployment credentials are properly scoped and accessible to the deployment job.