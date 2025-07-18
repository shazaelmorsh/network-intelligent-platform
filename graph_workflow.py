from operator import add
from typing import Literal
from neo4j.exceptions import CypherSyntaxError
from langgraph.graph import END, START, StateGraph
from langchain_neo4j.chains.graph_qa.cypher_utils import CypherQueryCorrector, Schema

from models import InputState, OverallState, OutputState
from chains import ChainManager
from database import DatabaseManager

class GraphWorkflow:
    """Manages the LangGraph workflow for the graph Q&A system"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.chain_manager = ChainManager()
        self._setup_cypher_corrector()
        self._setup_workflow()
    
    def _setup_cypher_corrector(self):
        """Setup the Cypher query corrector for relationship direction correction"""
        try:
            # Cypher query corrector is experimental
            corrector_schema = [
                Schema(el["start"], el["type"], el["end"])
                for el in self.db_manager.graph.structured_schema.get("relationships", [])
            ]
            self.cypher_query_corrector = CypherQueryCorrector(corrector_schema)
        except Exception as e:
            print(f"Warning: Could not setup Cypher query corrector: {e}")
            self.cypher_query_corrector = None
    
    def _setup_workflow(self):
        """Setup the LangGraph workflow"""
        self.workflow = StateGraph(OverallState, input=InputState, output=OutputState)
        
        # Add nodes
        self.workflow.add_node("guardrails", self._guardrails)
        self.workflow.add_node("generate_cypher", self._generate_cypher)
        self.workflow.add_node("validate_cypher", self._validate_cypher)
        self.workflow.add_node("correct_cypher", self._correct_cypher)
        self.workflow.add_node("execute_cypher", self._execute_cypher)
        self.workflow.add_node("generate_final_answer", self._generate_final_answer)
        
        # Add edges
        self.workflow.add_edge(START, "guardrails")
        self.workflow.add_conditional_edges("guardrails", self._guardrails_condition)
        self.workflow.add_edge("generate_cypher", "validate_cypher")
        self.workflow.add_conditional_edges("validate_cypher", self._validate_cypher_condition)
        self.workflow.add_edge("execute_cypher", "generate_final_answer")
        self.workflow.add_edge("correct_cypher", "validate_cypher")
        self.workflow.add_edge("generate_final_answer", END)
        
        # Compile the workflow
        self.workflow = self.workflow.compile()
    
    def _guardrails(self, state: InputState) -> OverallState:
        """Decides if the question is related to network intelligence or not."""
        guardrails_output = self.chain_manager.guardrails_chain.invoke({
            "question": state.get("question")
        })
        
        database_records = None
        if guardrails_output.decision == "end":
            database_records = "This question is not about people, organizations, or professional networking. Therefore I cannot answer this question."
        
        return {
            "next_action": guardrails_output.decision,
            "database_records": database_records,
            "steps": state.get("steps", []) + ["guardrails"],
        }
    
    def _generate_cypher(self, state: OverallState) -> OverallState:
        """Generates a cypher statement based on the provided schema and user input"""
        fewshot_examples = self.chain_manager.get_fewshot_examples(state.get("question"))
        
        generated_cypher = self.chain_manager.text2cypher_chain.invoke({
            "question": state.get("question"),
            "fewshot_examples": fewshot_examples,
            "schema": self.db_manager.get_enhanced_schema(),
        })
        
        return {
            "cypher_statement": generated_cypher,
            "steps": state.get("steps", []) + ["generate_cypher"]
        }
    
    def _validate_cypher(self, state: OverallState) -> OverallState:
        """Validates the Cypher statements and maps any property values to the database."""
        errors = []
        mapping_errors = []
        
        # Check for syntax errors
        try:
            self.db_manager.query(f"EXPLAIN {state.get('cypher_statement')}")
        except CypherSyntaxError as e:
            errors.append(e.message)
        
        # Experimental feature for correcting relationship directions
        corrected_cypher = state.get("cypher_statement")
        if self.cypher_query_corrector:
            corrected_cypher = self.cypher_query_corrector(state.get("cypher_statement"))
            if not corrected_cypher:
                errors.append("The generated Cypher statement doesn't fit the graph schema")
            if not corrected_cypher == state.get("cypher_statement"):
                print("Relationship direction was corrected")
        
        # Use LLM to find additional potential errors and get the mapping for values
        llm_output = self.chain_manager.validate_cypher_chain.invoke({
            "question": state.get("question"),
            "schema": self.db_manager.get_enhanced_schema(),
            "cypher": state.get("cypher_statement"),
        })
        
        if llm_output.errors:
            errors.extend(llm_output.errors)
        
        if llm_output.filters:
            for filter in llm_output.filters:
                # Do mapping only for string values
                node_props = self.db_manager.graph.structured_schema.get("node_props", {})
                if filter.node_label in node_props:
                    props = node_props[filter.node_label]
                    prop_info = next((p for p in props if p["property"] == filter.property_key), None)
                    if prop_info and prop_info["type"] == "STRING":
                        mapping = self.db_manager.query(
                            f"MATCH (n:{filter.node_label}) WHERE toLower(n.`{filter.property_key}`) = toLower($value) RETURN 'yes' LIMIT 1",
                            {"value": filter.property_value},
                        )
                        if not mapping:
                            print(f"Missing value mapping for {filter.node_label} on property {filter.property_key} with value {filter.property_value}")
                            mapping_errors.append(
                                f"Missing value mapping for {filter.node_label} on property {filter.property_key} with value {filter.property_value}"
                            )
        
        if mapping_errors:
            # Instead of ending, try to execute anyway and let the LLM handle missing data
            next_action = "execute_cypher"
        elif errors:
            next_action = "correct_cypher"
        else:
            next_action = "execute_cypher"
        
        return {
            "next_action": next_action,
            "cypher_statement": corrected_cypher,
            "cypher_errors": errors,
            "steps": state.get("steps", []) + ["validate_cypher"],
        }
    
    def _correct_cypher(self, state: OverallState) -> OverallState:
        """Correct the Cypher statement based on the provided errors."""
        corrected_cypher = self.chain_manager.correct_cypher_chain.invoke({
            "question": state.get("question"),
            "errors": state.get("cypher_errors"),
            "cypher": state.get("cypher_statement"),
            "schema": self.db_manager.get_enhanced_schema(),
        })
        
        return {
            "next_action": "validate_cypher",
            "cypher_statement": corrected_cypher,
            "steps": state.get("steps", []) + ["correct_cypher"],
        }
    
    def _execute_cypher(self, state: OverallState) -> OverallState:
        """Executes the given Cypher statement."""
        no_results = "I couldn't find any relevant information in the database"
        
        try:
            records = self.db_manager.query(state.get("cypher_statement"))
            return {
                "database_records": records if records else no_results,
                "next_action": "end",
                "steps": state.get("steps", []) + ["execute_cypher"],
            }
        except Exception as e:
            return {
                "database_records": f"Error executing query: {str(e)}",
                "next_action": "end",
                "steps": state.get("steps", []) + ["execute_cypher"],
            }
    
    def _generate_final_answer(self, state: OverallState) -> OutputState:
        """Generate the final answer based on the database results."""
        final_answer = self.chain_manager.generate_final_chain.invoke({
            "question": state.get("question"),
            "results": state.get("database_records")
        })
        
        return {
            "answer": final_answer,
            "steps": state.get("steps", []) + ["generate_final_answer"],
            "cypher_statement": state.get("cypher_statement", "")
        }
    
    def _guardrails_condition(self, state: OverallState) -> Literal["generate_cypher", "generate_final_answer"]:
        """Conditional edge function for guardrails step."""
        if state.get("next_action") == "end":
            return "generate_final_answer"
        elif state.get("next_action") == "network":
            return "generate_cypher"
    
    def _validate_cypher_condition(self, state: OverallState) -> Literal["generate_final_answer", "correct_cypher", "execute_cypher"]:
        """Conditional edge function for validate_cypher step."""
        if state.get("next_action") == "end":
            return "generate_final_answer"
        elif state.get("next_action") == "correct_cypher":
            return "correct_cypher"
        elif state.get("next_action") == "execute_cypher":
            return "execute_cypher"
    
    def invoke(self, question: str) -> OutputState:
        """Invoke the workflow with a question."""
        return self.workflow.invoke({"question": question})
    
    def get_graph(self):
        """Get the workflow graph for visualization."""
        return self.workflow.get_graph() 