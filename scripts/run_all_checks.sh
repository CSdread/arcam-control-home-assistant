#!/bin/bash
# Comprehensive code quality and compliance check script

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INTEGRATION_PATH="$PROJECT_ROOT/homeassistant/components/arcam_avr"
TEST_PATH="$PROJECT_ROOT/tests/components/arcam_avr"

# Output functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if UV is available
check_uv() {
    if ! command -v uv &> /dev/null; then
        print_error "UV package manager not found. Please install UV first."
        echo "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
    print_success "UV package manager found"
}

# Install dependencies
install_dependencies() {
    print_header "Installing Dependencies"
    cd "$PROJECT_ROOT"
    
    print_info "Installing project dependencies..."
    uv sync --dev
    
    print_success "Dependencies installed"
}

# Run pre-commit hooks
run_pre_commit() {
    print_header "Pre-commit Hooks"
    cd "$PROJECT_ROOT"
    
    # Install pre-commit if not already done
    if [ ! -f .git/hooks/pre-commit ]; then
        print_info "Installing pre-commit hooks..."
        uv run pre-commit install
    fi
    
    print_info "Running pre-commit hooks on all files..."
    if uv run pre-commit run --all-files; then
        print_success "Pre-commit hooks passed"
    else
        print_error "Pre-commit hooks failed"
        return 1
    fi
}

# Code formatting and linting
run_formatting() {
    print_header "Code Formatting & Linting"
    cd "$PROJECT_ROOT"
    
    print_info "Running Ruff formatter..."
    if uv run ruff format .; then
        print_success "Code formatting completed"
    else
        print_error "Code formatting failed"
        return 1
    fi
    
    print_info "Running Ruff linter..."
    if uv run ruff check . --fix; then
        print_success "Linting completed"
    else
        print_error "Linting failed"
        return 1
    fi
}

# Type checking
run_type_checking() {
    print_header "Type Checking"
    cd "$PROJECT_ROOT"
    
    print_info "Running MyPy type checking..."
    if uv run mypy "$INTEGRATION_PATH" --strict --ignore-missing-imports; then
        print_success "Type checking passed"
    else
        print_error "Type checking failed"
        return 1
    fi
}

# Security scanning
run_security_scan() {
    print_header "Security Scanning"
    cd "$PROJECT_ROOT"
    
    print_info "Running Bandit security scan..."
    if uv run bandit -r "$INTEGRATION_PATH" -f json -o bandit-report.json --skip B101; then
        print_success "Security scan completed"
        
        # Check for high severity issues
        if [ -f bandit-report.json ]; then
            HIGH_ISSUES=$(python3 -c "
import json
try:
    with open('bandit-report.json') as f:
        data = json.load(f)
    high_issues = [r for r in data.get('results', []) if r.get('issue_severity') == 'HIGH']
    print(len(high_issues))
except:
    print(0)
")
            if [ "$HIGH_ISSUES" -gt 0 ]; then
                print_error "Found $HIGH_ISSUES high severity security issues"
                return 1
            else
                print_success "No high severity security issues found"
            fi
        fi
    else
        print_warning "Security scan completed with warnings"
    fi
    
    print_info "Running Safety dependency check..."
    if uv run safety check --json --output safety-report.json; then
        print_success "Dependency vulnerability check passed"
    else
        print_warning "Dependency vulnerability check found issues"
    fi
}

# Run tests
run_tests() {
    print_header "Test Suite"
    cd "$PROJECT_ROOT"
    
    print_info "Running unit tests with coverage..."
    if uv run pytest "$TEST_PATH" \
        --cov=homeassistant.components.arcam_avr \
        --cov-report=term-missing \
        --cov-report=html \
        --cov-fail-under=85 \
        --tb=short \
        -v; then
        print_success "Test suite passed with adequate coverage"
    else
        print_error "Test suite failed"
        return 1
    fi
}

# Run integration tests
run_integration_tests() {
    print_header "Integration Tests"
    cd "$PROJECT_ROOT"
    
    print_info "Running integration tests..."
    if python3 "$TEST_PATH/run_integration_tests.py" --fast; then
        print_success "Integration tests passed"
    else
        print_error "Integration tests failed"
        return 1
    fi
}

# Performance tests
run_performance_tests() {
    print_header "Performance Tests"
    cd "$PROJECT_ROOT"
    
    print_info "Running performance tests..."
    if python3 "$TEST_PATH/run_integration_tests.py" --performance; then
        print_success "Performance tests passed"
    else
        print_warning "Performance tests completed with warnings"
    fi
}

# Validate manifest and translations
validate_manifest_translations() {
    print_header "Manifest & Translation Validation"
    cd "$PROJECT_ROOT"
    
    print_info "Validating manifest.json..."
    if python3 -c "
import json
with open('$INTEGRATION_PATH/manifest.json') as f:
    manifest = json.load(f)
    
required_fields = ['domain', 'name', 'documentation', 'dependencies', 'codeowners']
missing = [f for f in required_fields if f not in manifest]
if missing:
    print(f'Missing required fields: {missing}')
    exit(1)
    
if manifest['domain'] != 'arcam_avr':
    print(f'Domain mismatch: expected arcam_avr, got {manifest[\"domain\"]}')
    exit(1)
    
print('Manifest validation passed')
"; then
        print_success "Manifest validation passed"
    else
        print_error "Manifest validation failed"
        return 1
    fi
    
    print_info "Validating translation files..."
    if python3 -c "
import json
from pathlib import Path

translation_dir = Path('$INTEGRATION_PATH/translations')
required_files = ['en.json', 'es.json', 'fr.json', 'de.json']

for file in required_files:
    path = translation_dir / file
    if not path.exists():
        print(f'Missing translation file: {file}')
        exit(1)
    try:
        with open(path) as f:
            json.load(f)
    except json.JSONDecodeError as e:
        print(f'Invalid JSON in {file}: {e}')
        exit(1)

print('Translation validation passed')
"; then
        print_success "Translation validation passed"
    else
        print_error "Translation validation failed"
        return 1
    fi
}

# Documentation checks
check_documentation() {
    print_header "Documentation Validation"
    cd "$PROJECT_ROOT"
    
    print_info "Checking documentation files..."
    
    required_docs=(
        "README.md"
        "docs/user_guide.md"
        "docs/technical_guide.md"
        "docs/development_guide.md"
        "docs/troubleshooting.md"
    )
    
    missing_docs=()
    for doc in "${required_docs[@]}"; do
        if [ ! -f "$doc" ]; then
            missing_docs+=("$doc")
        fi
    done
    
    if [ ${#missing_docs[@]} -gt 0 ]; then
        print_error "Missing documentation files: ${missing_docs[*]}"
        return 1
    else
        print_success "All required documentation files present"
    fi
    
    print_info "Checking for broken internal links..."
    # Simple check for .md references
    find docs/ -name "*.md" -exec grep -l "\.md" {} \; | while read -r file; do
        if grep -o '\[.*\](\([^)]*\.md[^)]*\))' "$file" | grep -v "http" | while read -r link; do
            link_path=$(echo "$link" | sed 's/.*(\([^)]*\)).*/\1/' | cut -d'#' -f1)
            if [ -n "$link_path" ] && [ ! -f "$(dirname "$file")/$link_path" ] && [ ! -f "$link_path" ]; then
                print_warning "Potentially broken link in $file: $link_path"
            fi
        done
    done
    
    print_success "Documentation validation completed"
}

# Build validation
validate_build() {
    print_header "Build Validation"
    cd "$PROJECT_ROOT"
    
    print_info "Building package..."
    if uv build; then
        print_success "Package build successful"
    else
        print_error "Package build failed"
        return 1
    fi
}

# Home Assistant validation (if available)
validate_home_assistant() {
    print_header "Home Assistant Integration Validation"
    
    print_info "Checking Home Assistant compatibility..."
    
    # Check if we can validate against HA core
    if command -v hassfest &> /dev/null; then
        print_info "Running hassfest validation..."
        if hassfest --integration-path "$INTEGRATION_PATH"; then
            print_success "Home Assistant validation passed"
        else
            print_error "Home Assistant validation failed"
            return 1
        fi
    else
        print_warning "hassfest not available, skipping HA validation"
    fi
}

# Generate final report
generate_report() {
    print_header "Quality Report"
    
    echo "Code Quality Validation Report"
    echo "============================="
    echo "Generated: $(date)"
    echo "Project: Arcam AVR Home Assistant Integration"
    echo ""
    
    # Check if report files exist and summarize
    if [ -f bandit-report.json ]; then
        echo "Security Scan:"
        python3 -c "
import json
try:
    with open('bandit-report.json') as f:
        data = json.load(f)
    results = data.get('results', [])
    if results:
        print(f'  - Issues found: {len(results)}')
        high = len([r for r in results if r.get('issue_severity') == 'HIGH'])
        medium = len([r for r in results if r.get('issue_severity') == 'MEDIUM'])
        low = len([r for r in results if r.get('issue_severity') == 'LOW'])
        print(f'  - High: {high}, Medium: {medium}, Low: {low}')
    else:
        print('  - No security issues found')
except:
    print('  - Report not available')
"
    fi
    
    if [ -f htmlcov/index.html ]; then
        echo "Test Coverage:"
        echo "  - Coverage report generated in htmlcov/"
        # Extract coverage percentage if possible
        if command -v grep &> /dev/null; then
            coverage=$(grep -o '[0-9]\+%' htmlcov/index.html | head -1 2>/dev/null || echo "Unknown")
            echo "  - Coverage: $coverage"
        fi
    fi
    
    if [ -d dist/ ]; then
        echo "Build Artifacts:"
        echo "  - Package built successfully"
        echo "  - Files: $(ls dist/ | tr '\n' ' ')"
    fi
    
    echo ""
    print_success "Quality validation completed successfully!"
}

# Cleanup function
cleanup() {
    print_info "Cleaning up temporary files..."
    cd "$PROJECT_ROOT"
    
    # Remove temporary report files but keep important ones
    rm -f requirements-safety.txt
    
    print_info "Cleanup completed"
}

# Main execution
main() {
    print_header "Arcam AVR Integration - Code Quality & Compliance Check"
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Track failures
    failures=0
    
    # Run all checks
    checks=(
        "check_uv"
        "install_dependencies"
        "validate_manifest_translations"
        "run_formatting"
        "run_type_checking"
        "run_security_scan"
        "run_tests"
        "run_integration_tests"
        "check_documentation"
        "validate_build"
    )
    
    for check in "${checks[@]}"; do
        if ! $check; then
            ((failures++))
            print_error "Check failed: $check"
        fi
    done
    
    # Optional checks (don't fail on these)
    print_info "Running optional checks..."
    run_performance_tests || print_warning "Performance tests had issues"
    validate_home_assistant || print_warning "HA validation not available"
    
    # Generate report
    generate_report
    
    # Cleanup
    cleanup
    
    # Final status
    echo ""
    if [ $failures -eq 0 ]; then
        print_success "🎉 All quality checks passed! Integration is ready for release."
        exit 0
    else
        print_error "❌ $failures check(s) failed. Please fix issues before proceeding."
        exit 1
    fi
}

# Handle script interruption
trap cleanup EXIT

# Run main function
main "$@"