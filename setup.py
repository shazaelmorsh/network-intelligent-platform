#!/usr/bin/env python3
"""
Setup script for the Graph Q&A Application
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_env_file():
    """Create .env file if it doesn't exist"""
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    print("📝 Creating .env file...")
    env_content = """# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4.1-nano
OPENAI_TEMPERATURE=0

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password_here

# LangSmith Configuration (optional)
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_TRACING=false
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ .env file created")
        print("⚠️  Please update the .env file with your actual API keys and database credentials")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def check_neo4j_connection():
    """Check if Neo4j is accessible"""
    print("🗄️ Checking Neo4j connection...")
    try:
        from config import Config
        from database import DatabaseManager
        
        Config.validate()
        db_manager = DatabaseManager()
        
        if db_manager.test_connection():
            print("✅ Neo4j connection successful")
            return True
        else:
            print("❌ Neo4j connection failed")
            print("💡 Make sure Neo4j is running and credentials are correct")
            return False
    except Exception as e:
        print(f"❌ Neo4j check failed: {e}")
        return False

def run_tests():
    """Run basic tests"""
    print("🧪 Running tests...")
    try:
        subprocess.check_call([sys.executable, "test_app.py"])
        print("✅ Tests passed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Tests failed: {e}")
        return False

def show_next_steps():
    """Show next steps for the user"""
    print("\n🎉 Setup completed!")
    print("\n📋 Next steps:")
    print("1. Update the .env file with your actual API keys and database credentials")
    print("2. Make sure Neo4j is running")
    print("3. Run the application:")
    print("   - Interactive mode: python main.py")
    print("   - Web interface: python web_app.py")
    print("   - Agent mode: python agent.py")
    print("   - Single question: python main.py 'What was the cast of the Casino?'")
    print("\n📚 For more information, see README.md")

def main():
    """Main setup function"""
    print("🚀 Graph Q&A Application Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Create .env file
    if not create_env_file():
        sys.exit(1)
    
    # Check Neo4j connection (optional)
    print("\n💡 Neo4j connection check (optional - you can skip this if Neo4j isn't set up yet)")
    response = input("Do you want to check Neo4j connection? (y/n): ").lower()
    if response == 'y':
        check_neo4j_connection()
    
    # Run tests (optional)
    print("\n💡 Test run (optional)")
    response = input("Do you want to run tests? (y/n): ").lower()
    if response == 'y':
        run_tests()
    
    # Show next steps
    show_next_steps()

if __name__ == "__main__":
    main() 