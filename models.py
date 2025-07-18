from typing import Annotated, List, Literal, Optional
from typing_extensions import TypedDict
from pydantic import BaseModel, Field

class InputState(TypedDict):
    """Input state for the LangGraph workflow"""
    question: str

class OverallState(TypedDict):
    """Overall state for the LangGraph workflow"""
    question: str
    next_action: str
    cypher_statement: str
    cypher_errors: List[str]
    database_records: List[dict]
    steps: Annotated[List[str], "add"]

class OutputState(TypedDict):
    """Output state for the LangGraph workflow"""
    answer: str
    steps: List[str]
    cypher_statement: str

class GuardrailsOutput(BaseModel):
    """Output model for guardrails step"""
    decision: Literal["network", "end"] = Field(
        description="Decision on whether the question is related to network intelligence"
    )

class Property(BaseModel):
    """Represents a filter condition based on a specific node property in a graph in a Cypher statement."""
    node_label: str = Field(
        description="The label of the node to which this property belongs."
    )
    property_key: str = Field(description="The key of the property being filtered.")
    property_value: str = Field(
        description="The value that the property is being matched against."
    )

class ValidateCypherOutput(BaseModel):
    """Represents the validation result of a Cypher query's output"""
    errors: Optional[List[str]] = Field(
        description="A list of syntax or semantical errors in the Cypher statement. Always explain the discrepancy between schema and Cypher statement"
    )
    filters: Optional[List[Property]] = Field(
        description="A list of property-based filters applied in the Cypher statement."
    ) 