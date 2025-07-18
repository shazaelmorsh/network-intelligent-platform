from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from models import GuardrailsOutput, ValidateCypherOutput
from config import Config

class ChainManager:
    """Manages all the LangChain chains for the network intelligence platform"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=Config.OPENAI_MODEL, 
            temperature=Config.OPENAI_TEMPERATURE
        )
        self._setup_examples()
        self._setup_chains()
    
    def _setup_examples(self):
        """Setup few-shot examples for Cypher generation"""
        self.examples = [
            {
                "question": "Tell me about Michael Dell",
                "query": "MATCH (p:Person {id: 'Michael Dell'}) RETURN p.id as name",
            },
            {
                "question": "What organizations does Michael Dell work for?",
                "query": "MATCH (p:Person {id: 'Michael Dell'})-[:WORKSFOR]->(o:Organization) RETURN o.id as organization",
            },
            {
                "question": "Who does Michael Dell know?",
                "query": "MATCH (p:Person {id: 'Michael Dell'})-[:KNOWS]->(other:Person) RETURN other.id as person",
            },
            {
                "question": "What events has Michael Dell attended?",
                "query": "MATCH (p:Person {id: 'Michael Dell'})-[:ATTENDEE]->(e:Event) RETURN e.id as event",
            },
            {
                "question": "What is Michael Dell an alumnus of?",
                "query": "MATCH (p:Person {id: 'Michael Dell'})-[:ALUMNIOF]->(o:Organization) RETURN o.id as organization",
            },
            {
                "question": "What topics does Michael Dell know about?",
                "query": "MATCH (p:Person {id: 'Michael Dell'})-[:KNOWSABOUT]->(thing:Thing) RETURN p.id AS person, thing.id AS concept",
            },
            {
                "question": "Who works for Dell Technologies?",
                "query": "MATCH (p:Person)-[:WORKSFOR]->(o:Organization {id: 'Dell Technologies'}) RETURN p.id as person",
            },
            {
                "question": "What organizations are in the database?",
                "query": "MATCH (o:Organization) RETURN o.id as organization",
            },
            {
                "question": "What concepts does Michael Dell know about?",
                "query": "MATCH (p:Person {id: 'Michael Dell'})-[:KNOWSABOUT]->(thing:Thing) RETURN thing.id AS concept",
            },
            {
                "question": "What are Michael Dell's professional connections?",
                "query": "MATCH (p:Person {id: 'Michael Dell'})-[:KNOWS]->(other:Person) RETURN other.id as connection",
            },
        ]
        
        # Remove the semantic example selector to avoid embeddings
        self.example_selector = None
    
    def _setup_chains(self):
        """Setup all the LangChain chains"""
        self._setup_guardrails_chain()
        self._setup_text2cypher_chain()
        self._setup_validate_cypher_chain()
        self._setup_correct_cypher_chain()
        self._setup_generate_final_chain()
    
    def _setup_guardrails_chain(self):
        """Setup the guardrails chain"""
        guardrails_system = """
        As an intelligent assistant, your primary objective is to decide whether a given question is related to people, organizations, relationships, or network intelligence or not. 
        If the question is related to people, organizations, relationships, networking, professional connections, or business intelligence, output "network". Otherwise, output "end".
        To make this decision, assess the content of the question and determine if it refers to any person, organization, professional relationship, networking, business intelligence, 
        or related topics. Provide only the specified output: "network" or "end".
        """
        
        guardrails_prompt = ChatPromptTemplate.from_messages([
            ("system", guardrails_system),
            ("human", "{question}"),
        ])
        
        self.guardrails_chain = guardrails_prompt | self.llm.with_structured_output(GuardrailsOutput)
    
    def _setup_text2cypher_chain(self):
        """Setup the text to Cypher conversion chain"""
        text2cypher_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "Given an input question, convert it to a Cypher query. No pre-amble. Do not wrap the response in any backticks or anything else. Respond with a Cypher statement only!"
            ),
            (
                "human",
                """You are a Neo4j expert. Given an input question, create a syntactically correct Cypher query to run.
Do not wrap the response in any backticks or anything else. Respond with a Cypher statement only!
Here is the schema information
{schema}

Below are a number of examples of questions and their corresponding Cypher queries.

{fewshot_examples}

User input: {question}
Cypher query:"""
            ),
        ])
        
        self.text2cypher_chain = text2cypher_prompt | self.llm | StrOutputParser()
    
    def _setup_validate_cypher_chain(self):
        """Setup the Cypher validation chain"""
        validate_cypher_system = "You are a Cypher expert reviewing a statement written by a junior developer."
        
        validate_cypher_user = """You must check the following:
* Are there any syntax errors in the Cypher statement?
* Are there any missing or undefined variables in the Cypher statement?
* Are any node labels missing from the schema?
* Are any relationship types missing from the schema?
* Are any of the properties not included in the schema?
* Does the Cypher statement include enough information to answer the question?

Examples of good errors:
* Label (:Foo) does not exist, did you mean (:Bar)?
* Property bar does not exist for label Foo, did you mean baz?
* Relationship FOO does not exist, did you mean FOO_BAR?

Schema:
{schema}

The question is:
{question}

The Cypher statement is:
{cypher}

Make sure you don't make any mistakes!"""
        
        validate_cypher_prompt = ChatPromptTemplate.from_messages([
            ("system", validate_cypher_system),
            ("human", validate_cypher_user),
        ])
        
        self.validate_cypher_chain = validate_cypher_prompt | self.llm.with_structured_output(ValidateCypherOutput)
    
    def _setup_correct_cypher_chain(self):
        """Setup the Cypher correction chain"""
        correct_cypher_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are a Cypher expert reviewing a statement written by a junior developer. You need to correct the Cypher statement based on the provided errors. No pre-amble. Do not wrap the response in any backticks or anything else. Respond with a Cypher statement only!"
            ),
            (
                "human",
                """Check for invalid syntax or semantics and return a corrected Cypher statement.

Schema:
{schema}

Note: Do not include any explanations or apologies in your responses.
Do not wrap the response in any backticks or anything else.
Respond with a Cypher statement only!

Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.

The question is:
{question}

The Cypher statement is:
{cypher}

The errors are:
{errors}

Corrected Cypher statement: """
            ),
        ])
        
        self.correct_cypher_chain = correct_cypher_prompt | self.llm | StrOutputParser()
    
    def _setup_generate_final_chain(self):
        """Setup the final answer generation chain"""
        generate_final_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful network intelligence assistant that provides insights about people and organizations for enhancing small talk and professional networking."),
            (
                "human",
                """Use the following results retrieved from a database to provide
a succinct, informative answer to the user's question. Focus on providing insights that would be useful for small talk or professional networking.

Respond as if you are answering the question directly, providing context that would be helpful for someone meeting this person or organization.

Results: {results}
Question: {question}"""
            ),
        ])
        
        self.generate_final_chain = generate_final_prompt | self.llm | StrOutputParser()
    
    def get_fewshot_examples(self, question):
        """Get few-shot examples for a given question"""
        NL = "\n"
        # Use first 5 examples without embeddings
        examples = self.examples[:5]
        
        return (NL * 2).join([
            f"Question: {el['question']}{NL}Cypher:{el['query']}"
            for el in examples
        ]) 