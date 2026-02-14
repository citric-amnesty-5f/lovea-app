#!/usr/bin/env python3
"""
Automatically update index.html to use backend API instead of IndexedDB
"""

def update_index_html():
    """Update index.html to use backend API"""

    file_path = 'index.html'

    try:
        with open(file_path, 'r') as f:
            content = f.read()

        print("🔧 Updating index.html to use backend API...\n")

        # Backup original file
        with open(f'{file_path}.backup', 'w') as f:
            f.write(content)
        print("✓ Created backup: index.html.backup")

        # 1. Update gender values
        content = content.replace('<option value="M">Male</option>', '<option value="male">Male</option>')
        content = content.replace('<option value="F">Female</option>', '<option value="female">Female</option>')
        content = content.replace('<option value="T">Non-binary</option>', '<option value="non_binary">Non-binary</option>')
        content = content.replace('<option value="O">Other</option>', '<option value="other">Other</option>')
        print("✓ Updated gender values")

        # 2. Update script imports
        old_scripts = '''    <!-- Scripts -->
    <script src="js/database.js"></script>
    <script src="js/ai-matching.js"></script>
    <script src="js/auth.js"></script>'''

        new_scripts = '''    <!-- Scripts -->
    <script src="js/backend-api.js"></script>
    <!-- <script src="js/database.js"></script> --> <!-- Using backend API now -->
    <script src="js/ai-matching.js"></script>
    <script src="js/auth-backend.js"></script> <!-- Using backend API -->'''

        content = content.replace(old_scripts, new_scripts)
        print("✓ Updated script imports")

        # 3. Update demo credentials
        old_demo = '''                    Demo Admin: admin@loveai.com / admin123<br>
                    Demo User: user@loveai.com / user123'''

        new_demo = '''                    Backend Demo: user1@loveai.com / user123<br>
                    Admin: admin@loveai.com / admin123'''

        content = content.replace(old_demo, new_demo)
        print("✓ Updated demo credentials")

        # Write updated content
        with open(file_path, 'w') as f:
            f.write(content)

        print("\n" + "="*60)
        print("✅ SUCCESS! index.html updated to use backend API")
        print("="*60)
        print("\nNext steps:")
        print("1. cd backend")
        print("2. python init_db.py        # Initialize database")
        print("3. uvicorn app.main:app --reload   # Start backend")
        print("4. Open index.html in browser or use Live Server")
        print("\nBackend will run at: http://localhost:8000")
        print("API Docs: http://localhost:8000/docs")

    except FileNotFoundError:
        print(f"❌ Error: {file_path} not found")
        print("Make sure you're running this from the loveai-app folder")
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    update_index_html()
