#!/usr/bin/env python3
"""
Streamlit Network Intelligence Application
"""

import streamlit as st
import sys
import os
from graph_workflow import GraphWorkflow
from config import Config

# Page configuration
st.set_page_config(
    page_title="Network Intelligence Platform",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .answer-box {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    .steps-box {
        background-color: #e8f4fd;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .cypher-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        font-family: 'Courier New', monospace;
        font-size: 14px;
        overflow-x: auto;
        border: 1px solid #e1e5e9;
    }
    .example-question {
        padding: 0.5rem;
        margin: 0.25rem 0;
        border-radius: 5px;
        cursor: pointer;
        transition: background-color 0.2s;
    }
    .example-question:hover {
        background-color: #f0f0f0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def initialize_workflow():
    """Initialize the workflow with caching"""
    try:
        Config.validate()
        workflow = GraphWorkflow()
        return workflow, None
    except Exception as e:
        return None, str(e)

def main():
    """Main Streamlit application"""
    
    try:
        # Header
        st.markdown("""
        <div class="main-header">
            <h1>🎯 Network Intelligence Platform</h1>
            <p>Get insights about people and organizations for better networking and small talk</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Initialize workflow
        workflow, error = initialize_workflow()
        
        if error:
            st.error(f"❌ Failed to initialize application: {error}")
            st.info("Please check your environment variables and Neo4j connection.")
            return
        
        # Sidebar
        with st.sidebar:
            st.header("💡 Example Questions")
            example_questions = [
                "Tell me about Michael Dell",
                "What organizations does Michael Dell work for?",
                "Who does Michael Dell know?",
                "What events has Michael Dell attended?",
                "What topics does Michael Dell know about?",
                "What is Michael Dell an alumnus of?",
                "What are Michael Dell's professional connections?",
                "What concepts does Michael Dell know about?"
            ]
            
            for question in example_questions:
                if st.button(question, key=f"example_{question}"):
                    st.session_state.question_input = question
                    st.rerun()
        
        # Database overview/info box
        st.info(
            """
            **Database Overview**  
            - This database contains detailed information about **Mark Zuckerberg**, **Brad Gerstner**, and **Michael Dell**.  
            - **Case Sensitive:** Names and IDs are case sensitive. Please use the exact spelling (e.g., "Mark Zuckerberg", not "mark zuckerberg").  

            **Schema Highlights:**
            - **Node Types:**
                - `Person` (id, name)
                - `Organization` (id)
                - `Event` (id)
                - `Thing` (id)
                - `Document` (fileName, fileType, url, etc.)
            - **Key Relationships:**
                - `(:Person)-[:WORKSFOR]->(:Organization)`
                - `(:Person)-[:KNOWS]->(:Person)`
                - `(:Person)-[:ALUMNIOF]->(:Organization)`
                - `(:Person)-[:ATTENDEE]->(:Event)`
                - `(:Person)-[:SPONSOR]->(:Organization|:Person|:Event|:Thing)`
                - `(:Person)-[:KNOWSABOUT]->(:Thing|:Organization|:Event)`
                - ...and more (see documentation for full list)
            - **Other Entities:** Documents, Chunks, Entities, EntityTypes, etc. are also present for advanced knowledge representation.
            """,
            icon="📚"
        )
        # Main content
        st.header("🤔 Ask a Question")
        
        # Question input
        question = st.text_input(
            "Enter your question about people, organizations, or professional relationships:",
            placeholder="e.g., Tell me about Michael Dell",
            key="question_input"
        )
        
        if st.button("🔍 Get Insights", type="primary"):
            if question and question.strip():
                with st.spinner("Processing your question..."):
                    try:
                        result = workflow.invoke(question)
                        
                        # Display results
                        st.markdown("### 💡 Answer")
                        answer = result.get('answer', 'No answer generated')
                        if answer and answer.strip():
                            st.markdown(f"""
                            <div class="answer-box">
                                {answer}
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.warning("No answer was generated.")
                        
                        # Display steps
                        st.markdown("### 🔍 Processing Steps")
                        steps = result.get('steps', [])
                        if steps:
                            st.markdown(f"""
                            <div class="steps-box">
                                {' → '.join(steps)}
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.info("No processing steps recorded.")
                        
                        # Display Cypher query if available
                        cypher_statement = result.get('cypher_statement', '')
                        if cypher_statement and cypher_statement.strip():
                            st.markdown("### 📊 Cypher Query")
                            st.markdown(f"""
                            <div class="cypher-box">
                                {cypher_statement}
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.info("No Cypher query was generated.")
                            
                    except Exception as e:
                        st.error(f"❌ Error processing question: {str(e)}")
            elif not question:
                st.warning("Please enter a question.")
            else:
                st.warning("Please enter a valid question.")
                
    except Exception as e:
        st.error(f"❌ Application error: {str(e)}")
        st.info("Please check the console for more details.")

if __name__ == "__main__":
    main() 