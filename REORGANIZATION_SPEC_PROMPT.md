# CADS Codebase Final Reorganization - Kiro Spec Prompt

## System Prompt
You are a senior software engineer specializing in codebase organization and technical debt reduction. You have expertise in Python data processing pipelines, JavaScript visualization systems, and production deployment practices. Your goal is to create a comprehensive reorganization plan that eliminates technical debt while preserving all functionality.

## Task Context
The CADS Research Visualization System is a production-ready academic research data processing and visualization platform. The system works well functionally but suffers from organizational chaos including duplicate files, redundant documentation, scattered scripts, and disabled CI tests. This is the final cleanup before production handoff.

## Requirements

### Critical Issues to Address (Must Fix Today)

#### 1. **CI/CD Pipeline Integrity**
- **Problem**: Database tests are completely disabled in CI with `pytest.mark.skipif(os.getenv("CI") == "true")`
- **Impact**: Production database issues will not be caught before deployment
- **Requirement**: Enable database testing in CI with proper test database configuration
- **Acceptance Criteria**: All database tests run and pass in GitHub Actions CI pipeline

#### 2. **File Duplication Elimination**
- **Problem**: Critical files duplicated at root level (`app.js`, `index.html`, `requirements.txt`)
- **Impact**: Confusion about canonical files, deployment inconsistencies
- **Requirement**: Remove all duplicate files, establish single source of truth
- **Acceptance Criteria**: Each file exists in exactly one location, no duplicates

#### 3. **Documentation Consolidation**
- **Problem**: 6+ redundant summary documents covering the same cleanup activities
- **Impact**: Information overload, maintenance burden, outdated information
- **Requirement**: Consolidate to essential documentation only
- **Acceptance Criteria**: Clear documentation hierarchy with no redundant summaries

#### 4. **Script Organization**
- **Problem**: Scripts scattered between root `scripts/` and organized subdirectories
- **Impact**: Developer confusion about which scripts to use
- **Requirement**: Organize all scripts in logical subdirectories with clear purposes
- **Acceptance Criteria**: All scripts in appropriate subdirectories, no duplicates

### System Architecture Constraints

#### **Preserve Core Functionality**
- **CRITICAL**: Do not modify core processing logic in `cads/data_loader.py` or `cads/process_data.py`
- **CRITICAL**: Do not modify visualization logic in `visuals/public/app.js`
- **CRITICAL**: Do not modify database schema in `database/schema/`
- **CRITICAL**: Preserve all working scripts in `scripts/migration/` and `scripts/processing/`

#### **Maintain Data Flow**
- **Data Pipeline**: OpenAlex API → Database → CADS Pipeline → Visualization
- **File Structure**: `data/processed/` → `visuals/public/data/` (production sync)
- **Testing**: Unit tests → Integration tests → CI/CD pipeline

#### **Preserve Working Configurations**
- **Database**: Supabase IPv4 pooler connection (working solution)
- **API**: OpenAlex rate limiting and email configuration
- **Deployment**: Vercel configuration and build process

### Reorganization Specifications

#### **Directory Structure Target**
```
CADS-Research-Visualization/
├── 📊 cads/                          # Core pipeline (PRESERVE)
├── 🎨 visuals/                       # Visualization (PRESERVE)  
├── 🗄️ database/                      # Database schema (PRESERVE)
├── 🔧 scripts/                       # REORGANIZE - Clear categorization
│   ├── migration/                   # Database setup only
│   ├── processing/                  # Data processing only
│   └── utilities/                   # Verification tools only
├── 📚 docs/                          # CONSOLIDATE - Essential docs only
├── 📦 data/                          # Data storage (PRESERVE)
├── 🧪 tests/                         # Testing (FIX CI issues)
└── [config files]                   # Root level configs only
```

#### **Documentation Hierarchy Target**
```
docs/
├── README.md                        # Documentation index
├── HANDOFF_GUIDE.md                 # Single comprehensive handoff doc
├── setup/                           # Installation guides
├── troubleshooting/                 # Problem-solving guides
└── [NO SUMMARY DOCS]                # Remove all redundant summaries
```

#### **Scripts Organization Target**
```
scripts/
├── README.md                        # Clear workflow documentation
├── migration/
│   ├── execute_cads_migration.py    # MAIN working script
│   └── legacy/                      # Archive old attempts
├── processing/
│   ├── process_cads_with_openalex_ids.py
│   └── migrate_cads_data_to_cads_tables.py
└── utilities/
    └── check_cads_data_location.py
```

### Quality Assurance Requirements

#### **Testing Integrity**
- All existing tests must continue to pass
- Database tests must be enabled in CI
- No functionality regression allowed
- Test coverage must be maintained or improved

#### **Documentation Quality**
- Single source of truth for each topic
- Clear navigation and cross-references
- No outdated or contradictory information
- Handoff documentation for next developer

#### **Code Organization**
- Logical file placement
- Clear naming conventions
- No duplicate functionality
- Proper separation of concerns

### Risk Mitigation

#### **High-Risk Areas (Handle Carefully)**
1. **Database Connection**: Multiple legacy scripts exist due to connection issues
2. **OpenAlex Integration**: Rate limiting and API changes can break data collection
3. **Embedding Generation**: Memory-intensive process with potential failures
4. **File Path Dependencies**: Relative imports and hardcoded paths

#### **Backup and Recovery**
- Create backup before any file moves
- Verify functionality after each major change
- Document rollback procedures
- Test complete pipeline after reorganization

### Success Criteria

#### **Immediate Success (End of Day)**
- [ ] CI database tests enabled and passing
- [ ] All duplicate files removed
- [ ] Documentation consolidated to essentials
- [ ] Scripts properly organized
- [ ] All core functionality verified working

#### **Handoff Success (Next Developer)**
- [ ] Clear system understanding from documentation
- [ ] Obvious file locations and purposes
- [ ] Working development environment setup
- [ ] Emergency procedures documented
- [ ] Maintenance tasks clearly defined

### Implementation Approach

#### **Phase 1: Critical Fixes (2 hours)**
1. Fix CI database testing configuration
2. Remove duplicate files at root level
3. Consolidate redundant documentation
4. Organize scattered scripts

#### **Phase 2: Verification (1 hour)**
1. Test complete data pipeline
2. Verify visualization functionality
3. Run full test suite
4. Check deployment process

#### **Phase 3: Documentation (1 hour)**
1. Create comprehensive handoff guide
2. Update README files
3. Document known issues and workarounds
4. Create maintenance procedures

## Expected Deliverables

### **Reorganized Codebase**
- Clean directory structure with logical organization
- No duplicate files or redundant functionality
- Working CI/CD pipeline with database testing
- Consolidated documentation hierarchy

### **Handoff Documentation**
- Single comprehensive handoff guide
- Clear setup and maintenance procedures
- Known issues and emergency procedures
- Architecture overview and data flow diagrams

### **Quality Assurance**
- All tests passing including database tests in CI
- Complete functionality verification
- Performance benchmarks maintained
- Security and deployment configurations preserved

## Constraints and Limitations

### **Time Constraints**
- Must be completed in single day (4-5 hours maximum)
- Cannot break existing functionality
- Must maintain production readiness

### **Functional Constraints**
- Preserve all working scripts and configurations
- Maintain database connection stability
- Keep visualization performance optimized
- Preserve data processing accuracy

### **Organizational Constraints**
- Follow established Python and JavaScript conventions
- Maintain compatibility with existing deployment process
- Preserve git history and commit messages
- Keep backup and recovery options available

---

**This prompt should be used to create a Kiro spec for the final codebase reorganization, focusing on eliminating technical debt while preserving all functionality and ensuring smooth handoff to the next developer.**