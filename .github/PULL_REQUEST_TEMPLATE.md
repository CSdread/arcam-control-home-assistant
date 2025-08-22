# Pull Request

## Description

Please provide a clear and concise description of your changes.

### Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Code quality improvement
- [ ] Performance improvement
- [ ] Test coverage improvement

### Related Issues
Fixes #(issue number) or Closes #(issue number)

## Changes Made

### Code Changes
- [ ] Modified protocol handling
- [ ] Updated configuration flow
- [ ] Changed media player entity
- [ ] Updated coordinator logic
- [ ] Modified connection management
- [ ] Other: _describe_

### Files Modified
List the main files you've changed:
- `homeassistant/components/arcam_avr/...`
- `tests/components/arcam_avr/...`
- `docs/...`

### New Dependencies
- [ ] No new dependencies
- [ ] Added new Python packages (list below)
- [ ] Updated existing dependencies (list below)

## Testing

### Test Coverage
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Performance tests added/updated
- [ ] Manual testing completed

### Test Results
```bash
# Paste test results here
pytest tests/ -v
```

### Manual Testing
Describe what manual testing you performed:
- [ ] Tested with real Arcam device (model: ___)
- [ ] Tested with mock device
- [ ] Tested configuration flow
- [ ] Tested all media player functions
- [ ] Tested error scenarios

## Performance Impact

### Performance Testing
- [ ] No performance impact expected
- [ ] Performance impact tested and acceptable
- [ ] Performance improvements included
- [ ] Benchmark results attached

### Memory Usage
- [ ] No memory impact
- [ ] Memory usage tested
- [ ] Memory leaks checked

## Breaking Changes

### Backward Compatibility
- [ ] Fully backward compatible
- [ ] Minor configuration changes required
- [ ] Major breaking changes (requires migration)

### Migration Required
If breaking changes, describe the migration path:
```yaml
# Old configuration
old_config: value

# New configuration  
new_config: value
```

## Documentation

### Documentation Updates
- [ ] Code documentation (docstrings) updated
- [ ] User guide updated
- [ ] Technical guide updated
- [ ] README updated
- [ ] CHANGELOG updated
- [ ] No documentation changes needed

### Translation Updates
- [ ] No translation changes
- [ ] English translations updated
- [ ] Other language translations updated
- [ ] New translation keys added

## Code Quality

### Code Standards
- [ ] Code follows project style guidelines
- [ ] Type hints added/updated
- [ ] Error handling implemented
- [ ] Logging added where appropriate
- [ ] Security considerations addressed

### Quality Checks
- [ ] Pre-commit hooks pass
- [ ] Ruff linting passes
- [ ] MyPy type checking passes
- [ ] Bandit security scan passes
- [ ] Tests pass locally

## Review Guidelines

### For Reviewers
Please check:
- [ ] Code quality and style
- [ ] Test coverage adequacy
- [ ] Documentation completeness
- [ ] Performance implications
- [ ] Security considerations
- [ ] Breaking change impact

### Review Areas
Focus review on:
- [ ] Protocol implementation
- [ ] Home Assistant integration patterns
- [ ] Error handling
- [ ] User experience
- [ ] Performance
- [ ] Security

## Deployment

### Release Notes
What should be included in release notes?
```markdown
- Added: New feature description
- Fixed: Bug fix description  
- Changed: Breaking change description
- Improved: Enhancement description
```

### Deployment Checklist
- [ ] Version bumped (if needed)
- [ ] Manifest updated
- [ ] Dependencies updated
- [ ] Ready for release

## Additional Context

### Screenshots
If UI changes, include before/after screenshots:

### Logs
If fixing bugs, include relevant logs:
```
[Paste relevant logs here]
```

### Related Work
- Related PRs: #
- Dependent on: #
- Enables: #

## Checklist

### Before Submitting
- [ ] I have read the contributing guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published

### Code Quality
- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings

### Testing
- [ ] I have added tests to cover my changes
- [ ] All new and existing tests passed
- [ ] I have tested on real hardware (if applicable)
- [ ] I have tested error scenarios

### Documentation
- [ ] I have updated relevant documentation
- [ ] I have updated translations (if applicable)
- [ ] I have added/updated code comments
- [ ] I have updated type hints

---

**Note for Maintainers:** 
- Use "Squash and merge" for single commits
- Use "Create a merge commit" for multiple related commits
- Update version and changelog before merging to main