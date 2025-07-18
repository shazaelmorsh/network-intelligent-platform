#!/usr/bin/env python3
"""
Network Intelligence Agent for the Graph Q&A Application
"""

import sys
from graph_workflow import GraphWorkflow
from config import Config

class NetworkIntelligenceAgent:
    """A network intelligence agent that can answer questions about people and organizations for enhancing small talk and professional networking"""
    
    def __init__(self):
        """Initialize the agent with the graph workflow"""
        try:
            self.workflow = GraphWorkflow()
            print("🤖 Network Intelligence Agent initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize agent: {e}")
            raise
    
    def answer_question(self, question: str) -> dict:
        """
        Answer a question about people, organizations, and professional relationships
        
        Args:
            question (str): The question to answer
            
        Returns:
            dict: Contains the answer, steps taken, and cypher query
        """
        try:
            print(f"🤔 Processing question: {question}")
            result = self.workflow.invoke(question)
            
            return {
                'question': question,
                'answer': result['answer'],
                'steps': result['steps'],
                'cypher_query': result.get('cypher_statement', ''),
                'success': True
            }
        except Exception as e:
            return {
                'question': question,
                'answer': f"Sorry, I encountered an error: {str(e)}",
                'steps': ['error'],
                'cypher_query': '',
                'success': False,
                'error': str(e)
            }
    
    def get_capabilities(self) -> list:
        """Get a list of what the agent can do"""
        return [
            "Provide insights about people and their backgrounds",
            "Find information about organizations and companies",
            "Discover professional relationships and connections",
            "Identify common interests and topics people know about",
            "Find alumni connections and educational backgrounds",
            "Discover event attendance and professional activities",
            "Enhance small talk with relevant conversation starters",
            "Provide networking insights for professional meetings"
        ]
    
    def get_example_questions(self) -> list:
        """Get example questions the agent can answer"""
        return [
            "Tell me about Michael Dell",
            "What organizations does Michael Dell work for?",
            "Who does Michael Dell know?",
            "What events has Michael Dell attended?",
            "What is Michael Dell an alumnus of?",
            "What topics does Michael Dell know about?",
            "Who works for Dell Technologies?",
            "What organizations are in the database?",
            "What are some good conversation starters about Michael Dell?",
            "What professional background does Michael Dell have?"
        ]

def main():
    """Main function to run the agent"""
    try:
        # Validate configuration
        Config.validate()
        print("✅ Configuration validated")
        
        # Initialize agent
        agent = NetworkIntelligenceAgent()
        
        print("\n🎯 Network Intelligence Agent")
        print("=" * 50)
        print("I can help you with insights about people and organizations for better networking!")
        print("Type 'quit' or 'exit' to stop, 'help' for examples, 'capabilities' for what I can do.\n")
        
        while True:
            try:
                question = input("🤔 Your question: ").strip()
                
                if question.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if question.lower() == 'help':
                    print("\n💡 Example questions:")
                    for i, example in enumerate(agent.get_example_questions(), 1):
                        print(f"{i}. {example}")
                    print()
                    continue
                
                if question.lower() == 'capabilities':
                    print("\n🔧 What I can do:")
                    for i, capability in enumerate(agent.get_capabilities(), 1):
                        print(f"{i}. {capability}")
                    print()
                    continue
                
                if not question:
                    continue
                
                # Get answer from agent
                result = agent.answer_question(question)
                
                if result['success']:
                    print(f"\n💡 Answer: {result['answer']}")
                    print(f"🔍 Steps: {', '.join(result['steps'])}")
                    if result['cypher_query']:
                        print(f"📊 Cypher query: {result['cypher_query']}")
                else:
                    print(f"❌ Error: {result['answer']}")
                
                print("-" * 50)
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
    
    except Exception as e:
        print(f"❌ Failed to start agent: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 