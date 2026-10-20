"""Phase 0 Verification Script."""
import sys
from pathlib import Path

def main():
    base_dir = Path(__file__).resolve().parent.parent
    if str(base_dir) not in sys.path:
        sys.path.insert(0, str(base_dir))

    print("=" * 60)
    print("PHASE 0 ENVIRONMENT & SCAFFOLDING VERIFICATION")
    print("=" * 60)

    # 1. Check Python version
    print(f"[OK] Python Version: {sys.version.split()[0]}")

    # 2. Check Directory Structure
    required_dirs = [
        "data/raw",
        "data/processed",
        "src/data_ingestion",
        "src/retrieval",
        "src/llm",
        "src/services",
        "src/api",
        "frontend/components",
        "tests",
        "docs",
    ]
    base_dir = Path(__file__).resolve().parent.parent
    all_dirs_exist = True
    for rel_path in required_dirs:
        dir_path = base_dir / rel_path
        if dir_path.is_dir():
            print(f"[OK] Directory exists: {rel_path}")
        else:
            print(f"[FAIL] Directory MISSING: {rel_path}")
            all_dirs_exist = False

    # 3. Check Core Imports
    modules_to_test = [
        "pandas",
        "pyarrow",
        "datasets",
        "fastapi",
        "uvicorn",
        "streamlit",
        "pydantic",
        "pydantic_settings",
        "google.genai",
        "google.generativeai",
        "pytest",
    ]
    all_imports_passed = True
    for mod in modules_to_test:
        try:
            __import__(mod)
            print(f"[OK] Successfully imported: {mod}")
        except ImportError as e:
            print(f"[FAIL] Failed to import: {mod} ({e})")
            all_imports_passed = False

    # 4. Check Config Loading
    try:
        from src.config import get_settings
        settings = get_settings()
        print(f"[OK] Settings loaded successfully!")
        print(f"    - Environment: {settings.APP_ENV}")
        print(f"    - Gemini Model: {settings.GEMINI_MODEL}")
        print(f"    - API Port: {settings.API_PORT}")
        print(f"    - Dataset ID: {settings.HUGGINGFACE_DATASET_ID}")
        config_passed = True
    except Exception as e:
        print(f"[FAIL] Failed to load settings: {e}")
        config_passed = False

    print("=" * 60)
    if all_dirs_exist and all_imports_passed and config_passed:
        print("ALL PHASE 0 VERIFICATION CHECKS PASSED!")
        return 0
    else:
        print("SOME CHECKS FAILED. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
