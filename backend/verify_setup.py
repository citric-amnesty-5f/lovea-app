"""
Verify LoveAI backend setup and run quick tests
"""
import sys
import subprocess
import os


def print_header(title):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60 + "\n")


def check_dependencies():
    """Check if all dependencies are installed"""
    print_header("Step 1: Checking Dependencies")

    required_packages = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "psycopg2",
        "python-jose",
        "passlib",
        "pytest"
    ]

    missing = []

    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - MISSING")
            missing.append(package)

    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False

    print("\n✅ All dependencies installed")
    return True


def check_database_models():
    """Check if database models can be imported"""
    print_header("Step 2: Checking Database Models")

    try:
        from app.models import User, Profile, Match, Message
        print("✓ User model")
        print("✓ Profile model")
        print("✓ Match model")
        print("✓ Message model")
        print("\n✅ All models imported successfully")
        return True
    except Exception as e:
        print(f"\n❌ Error importing models: {str(e)}")
        return False


def check_routes():
    """Check if all routes can be imported"""
    print_header("Step 3: Checking API Routes")

    try:
        from app.routers import auth_routes, profile_routes, discovery_routes
        print("✓ Auth routes")
        print("✓ Profile routes")
        print("✓ Discovery routes")
        print("\n✅ All routes imported successfully")
        return True
    except Exception as e:
        print(f"\n❌ Error importing routes: {str(e)}")
        return False


def run_quick_tests():
    """Run a subset of quick tests"""
    print_header("Step 4: Running Quick Tests")

    try:
        result = subprocess.run(
            ["pytest", "tests/test_auth.py::TestRegistration::test_register_new_user", "-v"],
            capture_output=True,
            text=True,
            timeout=30
        )

        print(result.stdout)

        if result.returncode == 0:
            print("\n✅ Quick tests passed")
            return True
        else:
            print("\n❌ Quick tests failed")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"\n❌ Error running tests: {str(e)}")
        return False


def run_full_test_suite():
    """Run complete test suite"""
    print_header("Step 5: Running Full Test Suite")

    try:
        result = subprocess.run(
            ["pytest", "tests/", "-v", "--tb=short"],
            timeout=120
        )

        if result.returncode == 0:
            print("\n✅ All tests passed!")
            return True
        else:
            print("\n❌ Some tests failed")
            return False
    except Exception as e:
        print(f"\n❌ Error running full test suite: {str(e)}")
        return False


def check_env_file():
    """Check if .env file exists"""
    print_header("Step 0: Checking Environment Configuration")

    if os.path.exists(".env"):
        print("✓ .env file found")
        return True
    else:
        print("⚠️  .env file not found")
        print("Copy .env.example to .env and configure it")
        return False


def main():
    """Run all verification steps"""
    print("\n" + "🚀" * 30)
    print("LoveAI Backend - Setup Verification")
    print("🚀" * 30)

    results = []

    # Run checks
    results.append(("Environment", check_env_file()))
    results.append(("Dependencies", check_dependencies()))
    results.append(("Database Models", check_database_models()))
    results.append(("API Routes", check_routes()))
    results.append(("Quick Tests", run_quick_tests()))

    # Ask if user wants to run full suite
    print("\n" + "=" * 60)
    response = input("Run full test suite? (y/n): ")

    if response.lower() == 'y':
        results.append(("Full Test Suite", run_full_test_suite()))

    # Summary
    print_header("Verification Summary")

    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:.<40} {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)

    if all_passed:
        print("🎉 All checks passed! Backend is ready to use.")
        print("\nNext steps:")
        print("1. python init_db.py          # Initialize database")
        print("2. uvicorn app.main:app --reload  # Start server")
        print("3. Visit http://localhost:8000/docs")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
