#!/usr/bin/env python3
"""
Network Intelligence Application

A sophisticated question-answering system over a Neo4j graph database
using LangGraph for multi-step workflow management, focused on providing
insights about people and organizations for enhancing small talk and professional networking.
"""

import os
import sys
from config import Config
from database import DatabaseManager
from graph_workflow import GraphWorkflow

def setup_environment():
    """Setup and validate the environment"""
    try:
        Config.validate()
        print("✅ Environment configuration validated")
        return True
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return False

def setup_database():
    """Setup the database connection and populate with data"""
    db_manager = DatabaseManager()
    
    # Test connection
    if not db_manager.test_connection():
        print("❌ Failed to connect to Neo4j. Please check your Neo4j instance.")
        return None
    
    # Refresh schema
    print("📋 Refreshing database schema...")
    schema = db_manager.refresh_schema()
    print("✅ Database setup complete")
    
    return db_manager

def run_interactive_mode():
    """Run the application in interactive mode"""
    print("\n🎯 Network Intelligence Application")
    print("=" * 50)
    print("Ask questions about people, organizations, and professional relationships!")
    print("Get insights to enhance your small talk and networking conversations.")
    print("Type 'quit' or 'exit' to stop the application.\n")
    
    workflow = GraphWorkflow()
    
    while True:
        try:
            question = input("🤔 Your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not question:
                continue
            
            print("\n🔄 Processing your question...")
            result = workflow.invoke(question)
            
            print(f"\n💡 Answer: {result['answer']}")
            print(f"🔍 Steps taken: {', '.join(result['steps'])}")
            if result.get('cypher_statement'):
                print(f"📊 Cypher query: {result['cypher_statement']}")
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def run_single_question(question: str):
    """Run the application with a single question"""
    workflow = GraphWorkflow()
    result = workflow.invoke(question)
    
    print(f"Question: {question}")
    print(f"Answer: {result['answer']}")
    print(f"Steps: {', '.join(result['steps'])}")
    if result.get('cypher_statement'):
        print(f"Cypher query: {result['cypher_statement']}")

def main():
    """Main application entry point"""
    # Setup environment
    if not setup_environment():
        sys.exit(1)
    
    # Setup database
    db_manager = setup_database()
    if not db_manager:
        sys.exit(1)
    
    # Check command line arguments
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        run_single_question(question)
    else:
        run_interactive_mode()

if __name__ == "__main__":
    main()