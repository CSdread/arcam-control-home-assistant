#!/usr/bin/env python3
"""Code quality validation script for Arcam AVR integration."""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class CodeQualityValidator:
    """Comprehensive code quality validator."""

    def __init__(self, project_root: Path):
        """Initialize validator with project root."""
        self.project_root = project_root
        self.integration_path = project_root / "homeassistant" / "components" / "arcam_avr"
        self.test_path = project_root / "tests" / "components" / "arcam_avr"
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def run_command(self, command: List[str], capture_output: bool = True) -> Tuple[int, str, str]:
        """Run a command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(
                command,
                cwd=self.project_root,
                capture_output=capture_output,
                text=True,
                timeout=300,  # 5 minute timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Command timed out"
        except Exception as e:
            return 1, "", str(e)

    def validate_ruff(self) -> bool:
        """Run Ruff linting and formatting checks."""
        print("🔍 Running Ruff linting...")
        
        # Check linting
        code, stdout, stderr = self.run_command(["uv", "run", "ruff", "check", "."])
        if code != 0:
            self.errors.append(f"Ruff linting failed:\n{stdout}\n{stderr}")
            return False

        # Check formatting
        code, stdout, stderr = self.run_command(["uv", "run", "ruff", "format", "--check", "."])
        if code != 0:
            self.errors.append(f"Ruff formatting check failed:\n{stdout}\n{stderr}")
            return False

        print("✅ Ruff checks passed")
        return True

    def validate_mypy(self) -> bool:
        """Run MyPy type checking."""
        print("🔍 Running MyPy type checking...")
        
        code, stdout, stderr = self.run_command([
            "uv", "run", "mypy", 
            str(self.integration_path),
            "--strict",
            "--ignore-missing-imports"
        ])
        
        if code != 0:
            self.errors.append(f"MyPy type checking failed:\n{stdout}\n{stderr}")
            return False

        print("✅ MyPy type checking passed")
        return True

    def validate_bandit(self) -> bool:
        """Run Bandit security checks."""
        print("🔍 Running Bandit security scan...")
        
        code, stdout, stderr = self.run_command([
            "uv", "run", "bandit",
            "-r", str(self.integration_path),
            "-f", "json",
            "-o", str(self.project_root / "bandit-report.json"),
            "--skip", "B101"  # Skip assert_used in tests
        ])
        
        # Bandit returns 1 for issues found, but we need to check severity
        if (self.project_root / "bandit-report.json").exists():
            with open(self.project_root / "bandit-report.json") as f:
                report = json.load(f)
                
            high_severity = [r for r in report.get("results", []) if r.get("issue_severity") == "HIGH"]
            medium_severity = [r for r in report.get("results", []) if r.get("issue_severity") == "MEDIUM"]
            
            if high_severity:
                self.errors.append(f"Bandit found {len(high_severity)} high severity security issues")
                return False
            elif medium_severity:
                self.warnings.append(f"Bandit found {len(medium_severity)} medium severity security issues")

        print("✅ Bandit security scan passed")
        return True

    def validate_safety(self) -> bool:
        """Run Safety dependency vulnerability check."""
        print("🔍 Running Safety vulnerability check...")
        
        # Generate requirements for safety check
        code, stdout, stderr = self.run_command(["uv", "pip", "freeze"])
        if code != 0:
            self.warnings.append("Could not generate requirements for safety check")
            return True
            
        requirements_file = self.project_root / "requirements-safety.txt"
        requirements_file.write_text(stdout)
        
        try:
            code, stdout, stderr = self.run_command([
                "uv", "run", "safety", "check",
                "-r", str(requirements_file),
                "--json",
                "--output", str(self.project_root / "safety-report.json")
            ])
            
            if code != 0 and (self.project_root / "safety-report.json").exists():
                with open(self.project_root / "safety-report.json") as f:
                    report = json.load(f)
                    
                vulnerabilities = report.get("vulnerabilities", [])
                if vulnerabilities:
                    self.warnings.append(f"Safety found {len(vulnerabilities)} dependency vulnerabilities")
                    
        except Exception:
            self.warnings.append("Safety check could not complete")
        finally:
            if requirements_file.exists():
                requirements_file.unlink()

        print("✅ Safety vulnerability check completed")
        return True

    def validate_tests(self) -> bool:
        """Run test suite with coverage."""
        print("🔍 Running test suite...")
        
        code, stdout, stderr = self.run_command([
            "uv", "run", "pytest",
            str(self.test_path),
            "--cov=homeassistant.components.arcam_avr",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-fail-under=85",
            "--tb=short",
            "-v"
        ])
        
        if code != 0:
            self.errors.append(f"Test suite failed:\n{stdout}\n{stderr}")
            return False

        print("✅ Test suite passed with adequate coverage")
        return True

    def validate_manifest(self) -> bool:
        """Validate Home Assistant manifest.json."""
        print("🔍 Validating manifest.json...")
        
        manifest_path = self.integration_path / "manifest.json"
        if not manifest_path.exists():
            self.errors.append("manifest.json not found")
            return False

        try:
            with open(manifest_path) as f:
                manifest = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in manifest.json: {e}")
            return False

        # Required fields
        required_fields = ["domain", "name", "documentation", "dependencies", "codeowners"]
        missing_fields = [field for field in required_fields if field not in manifest]
        if missing_fields:
            self.errors.append(f"Missing required fields in manifest.json: {missing_fields}")
            return False

        # Validate domain matches directory
        if manifest["domain"] != "arcam_avr":
            self.errors.append(f"Domain mismatch: expected 'arcam_avr', got '{manifest['domain']}'")
            return False

        # Check version format if present
        if "version" in manifest:
            version = manifest["version"]
            if not version.replace(".", "").replace("-", "").replace("alpha", "").replace("beta", "").replace("rc", "").isalnum():
                self.warnings.append(f"Version format may be invalid: {version}")

        print("✅ Manifest validation passed")
        return True

    def validate_translations(self) -> bool:
        """Validate translation files."""
        print("🔍 Validating translation files...")
        
        translations_path = self.integration_path / "translations"
        if not translations_path.exists():
            self.errors.append("Translations directory not found")
            return False

        # Check required languages
        required_languages = ["en.json"]
        available_languages = ["es.json", "fr.json", "de.json"]
        
        for lang_file in required_languages:
            lang_path = translations_path / lang_file
            if not lang_path.exists():
                self.errors.append(f"Required translation file missing: {lang_file}")
                return False

        # Validate JSON structure
        base_translation = None
        for lang_file in translations_path.glob("*.json"):
            try:
                with open(lang_file) as f:
                    translation = json.load(f)
                    
                if lang_file.name == "en.json":
                    base_translation = translation
                elif base_translation:
                    # Check for key consistency
                    self._check_translation_keys(base_translation, translation, lang_file.name)
                    
            except json.JSONDecodeError as e:
                self.errors.append(f"Invalid JSON in {lang_file.name}: {e}")
                return False

        print("✅ Translation validation passed")
        return True

    def _check_translation_keys(self, base: Dict, translation: Dict, filename: str) -> None:
        """Recursively check translation key consistency."""
        def get_all_keys(d: Dict, prefix: str = "") -> set:
            keys = set()
            for k, v in d.items():
                key = f"{prefix}.{k}" if prefix else k
                keys.add(key)
                if isinstance(v, dict):
                    keys.update(get_all_keys(v, key))
            return keys

        base_keys = get_all_keys(base)
        translation_keys = get_all_keys(translation)
        
        missing_keys = base_keys - translation_keys
        extra_keys = translation_keys - base_keys
        
        if missing_keys:
            self.warnings.append(f"Missing translation keys in {filename}: {missing_keys}")
        if extra_keys:
            self.warnings.append(f"Extra translation keys in {filename}: {extra_keys}")

    def validate_imports(self) -> bool:
        """Validate import statements and dependencies."""
        print("🔍 Validating imports...")
        
        # Check for forbidden imports
        forbidden_imports = ["time.sleep", "requests", "urllib3"]
        allowed_async_alternatives = {
            "time.sleep": "asyncio.sleep",
            "requests": "aiohttp",
        }
        
        for py_file in self.integration_path.rglob("*.py"):
            with open(py_file) as f:
                content = f.read()
                
            for forbidden in forbidden_imports:
                if forbidden in content:
                    suggestion = allowed_async_alternatives.get(forbidden, "async alternative")
                    self.warnings.append(
                        f"Found potentially problematic import '{forbidden}' in {py_file.name}. "
                        f"Consider using {suggestion} instead."
                    )

        print("✅ Import validation completed")
        return True

    def validate_docstrings(self) -> bool:
        """Validate docstring presence and format."""
        print("🔍 Validating docstrings...")
        
        missing_docstrings = []
        for py_file in self.integration_path.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue
                
            with open(py_file) as f:
                content = f.read()
                
            # Check for class and function definitions without docstrings
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if (line.strip().startswith('class ') or 
                    line.strip().startswith('def ') or 
                    line.strip().startswith('async def ')):
                    
                    # Check if next non-empty line is a docstring
                    j = i + 1
                    while j < len(lines) and not lines[j].strip():
                        j += 1
                        
                    if j >= len(lines) or not lines[j].strip().startswith('"""'):
                        func_name = line.strip().split('(')[0].replace('class ', '').replace('def ', '').replace('async ', '')
                        if not func_name.startswith('_') and func_name not in ['__init__', '__str__', '__repr__']:
                            missing_docstrings.append(f"{py_file.name}:{i+1} - {func_name}")

        if missing_docstrings:
            # Only warn about missing docstrings, don't fail
            self.warnings.append(f"Missing docstrings: {missing_docstrings[:10]}")  # Limit output

        print("✅ Docstring validation completed")
        return True

    def validate_file_structure(self) -> bool:
        """Validate project file structure."""
        print("🔍 Validating file structure...")
        
        # Required files
        required_files = [
            self.integration_path / "__init__.py",
            self.integration_path / "manifest.json",
            self.integration_path / "config_flow.py",
            self.integration_path / "coordinator.py",
            self.integration_path / "media_player.py",
            self.integration_path / "const.py",
        ]

        missing_files = [f for f in required_files if not f.exists()]
        if missing_files:
            self.errors.append(f"Missing required files: {[f.name for f in missing_files]}")
            return False

        # Check test structure
        test_files = [
            self.test_path / "__init__.py",
            self.test_path / "conftest.py",
            self.test_path / "test_init.py",
            self.test_path / "test_config_flow.py",
            self.test_path / "test_coordinator.py",
            self.test_path / "test_media_player.py",
        ]

        missing_test_files = [f for f in test_files if not f.exists()]
        if missing_test_files:
            self.warnings.append(f"Missing test files: {[f.name for f in missing_test_files]}")

        print("✅ File structure validation passed")
        return True

    def generate_report(self) -> None:
        """Generate quality report."""
        print("\n" + "="*60)
        print("CODE QUALITY VALIDATION REPORT")
        print("="*60)
        
        if not self.errors and not self.warnings:
            print("🎉 All quality checks passed!")
            return

        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"{i}. {error}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"{i}. {warning}")

        print(f"\nSUMMARY:")
        print(f"- Errors: {len(self.errors)}")
        print(f"- Warnings: {len(self.warnings)}")
        
        if self.errors:
            print("\n❌ Quality validation FAILED - please fix errors before proceeding")
        else:
            print("\n✅ Quality validation PASSED - warnings should be addressed when possible")

    def run_all_validations(self) -> bool:
        """Run all code quality validations."""
        print("🚀 Starting comprehensive code quality validation...\n")

        validations = [
            ("File Structure", self.validate_file_structure),
            ("Manifest", self.validate_manifest),
            ("Translations", self.validate_translations),
            ("Ruff Linting", self.validate_ruff),
            ("Type Checking", self.validate_mypy),
            ("Security Scan", self.validate_bandit),
            ("Dependency Check", self.validate_safety),
            ("Import Analysis", self.validate_imports),
            ("Docstrings", self.validate_docstrings),
            ("Test Suite", self.validate_tests),
        ]

        success = True
        for name, validation_func in validations:
            try:
                if not validation_func():
                    success = False
            except Exception as e:
                self.errors.append(f"{name} validation failed with exception: {e}")
                success = False
            print()  # Add spacing between validations

        return success


def main():
    """Main entry point."""
    project_root = Path(__file__).parent.parent
    validator = CodeQualityValidator(project_root)
    
    # Run validations
    success = validator.run_all_validations()
    
    # Generate report
    validator.generate_report()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()