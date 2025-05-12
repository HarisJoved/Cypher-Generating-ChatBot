import streamlit as st
from llm import llm
from graph import graph
import logging
import re

logger = logging.getLogger(__name__)

def get_schema():
    """Get the database schema to help generate appropriate Cypher queries"""
    try:
        # Query to get node labels and their properties
        node_query = """
        CALL apoc.meta.schema() YIELD value
        RETURN value
        """
        
        # Simpler query if APOC is not available
        simple_node_query = """
        CALL db.schema.nodeTypeProperties() YIELD nodeType, propertyName
        RETURN nodeType, collect(propertyName) as properties
        """
        
        # Relationship query
        rel_query = """
        CALL db.schema.relTypeProperties() YIELD relType
        RETURN collect(relType) AS relationshipTypes
        """
        
        try:
            schema_result = graph.query(node_query)
            if not schema_result:
                logger.info("Using simplified schema query as APOC may not be available")
                schema_result = graph.query(simple_node_query)
        except:
            logger.info("Primary schema query failed, using simplified version")
            schema_result = graph.query(simple_node_query)
        
        # Get relationship types
        try:
            rel_result = graph.query(rel_query)
            relationship_types = rel_result[0]["relationshipTypes"] if rel_result else []
        except:
            relationship_types = []
            logger.warning("Could not retrieve relationship types")
        
        # Format schema for the LLM
        if schema_result:
            schema_text = "Database Schema:\n"
            
            if "value" in schema_result[0]:  # APOC result format
                schema_data = schema_result[0]["value"]
                for node_type, info in schema_data.items():
                    if node_type.startswith(":`"):  # Node labels
                        label = node_type.replace(":`", "").replace("`", "")
                        schema_text += f"Node Label: {label}\n"
                        if "properties" in info:
                            schema_text += "Properties: " + ", ".join(info["properties"].keys()) + "\n"
            else:  # Simple query result format
                for item in schema_result:
                    node_type = item["nodeType"]
                    props = item["properties"]
                    schema_text += f"Node Label: {node_type.replace(':', '')}\n"
                    schema_text += "Properties: " + ", ".join(props) + "\n"
            
            # Add relationship types
            if relationship_types:
                schema_text += "\nRelationship Types: " + ", ".join(relationship_types) + "\n"
            
            return schema_text
        else:
            # Provide a fallback schema if queries fail
            return """
            Database Schema:
            Node Label: Movie
            Properties: title, released, tagline, plot
            
            Node Label: Person
            Properties: name, born
            
            Relationship Types: ACTED_IN, DIRECTED, PRODUCED, WROTE
            """
    except Exception as e:
        logger.error(f"Error retrieving database schema: {e}")
        return """
        Database Schema:
        Node Label: Movie
        Properties: title, released, tagline, plot
        
        Node Label: Person
        Properties: name, born
        
        Relationship Types: ACTED_IN, DIRECTED, PRODUCED, WROTE
        """

def generate_cypher_query(user_input):
    """Generate a Cypher query based on user input and database schema"""
    try:
        logger.info(f"Generating Cypher query for: '{user_input}'")
        
        # Get the database schema
        schema = get_schema()
        logger.info(f"Retrieved schema for query generation")
        
        # Create a prompt for the LLM to generate a Cypher query
        prompt = f"""
        You are a Neo4j Cypher query expert. Based on the following database schema and user question,
        generate the most appropriate Cypher query to answer the user's question.
        
        {schema}
        
        User Question: {user_input}
        
        The query should:
        1. Be syntactically correct Cypher
        2. Use appropriate labels, relationships and properties from the schema
        3. Include relevant filters based on the user's question
        4. Return only the most relevant information (avoid returning entire nodes)
        5. Limit results to at most 10 items for performance
        6. Make sure to use case-insensitive comparisons with toLower() for text searches
        7. Use parameterized queries with $parameters where appropriate
        
        Return ONLY the Cypher query with no explanations or additional text. The query should be ready to execute.
        """
        
        # Generate the Cypher query using LLM
        response = llm.invoke(prompt)
        cypher_query = response.content.strip()
        
        # Clean up the query (remove markdown code blocks if present)
        if "```" in cypher_query:
            # Extract the query from code blocks
            matches = re.findall(r"```(?:cypher)?(.*?)```", cypher_query, re.DOTALL)
            if matches:
                cypher_query = matches[0].strip()
            else:
                # Fallback if regex doesn't match
                cypher_query = cypher_query.replace("```cypher", "").replace("```", "").strip()
        
        # Log the generated query with clear formatting for terminal visibility
        logger.info("════════════════════ GENERATED CYPHER QUERY ════════════════════")
        for line in cypher_query.split('\n'):
            logger.info(line)
        logger.info("══════════════════════════════════════════════════════════════")
        
        return cypher_query
    except Exception as e:
        logger.error(f"Error generating Cypher query: {e}")
        # Return a simple fallback query
        fallback_query = """
        MATCH (m:Movie)
        WHERE toLower(m.title) CONTAINS toLower($search)
        WITH m LIMIT 5
        OPTIONAL MATCH (person:Person)-[:ACTED_IN]->(m)
        OPTIONAL MATCH (director:Person)-[:DIRECTED]->(m)
        RETURN m.title AS title, 
               collect(distinct person.name) AS actors,
               collect(distinct director.name) AS directors
        """
        logger.info("════════════════════ FALLBACK CYPHER QUERY ════════════════════")
        for line in fallback_query.split('\n'):
            logger.info(line)
        logger.info("══════════════════════════════════════════════════════════════")
        return fallback_query

def extract_parameters(query, user_input):
    """Extract parameters from the query and user input"""
    params = {}
    
    # Extract the main search term
    search_term = user_input.lower()
    if "about" in search_term:
        search_term = search_term.split("about")[1].strip()
    
    # Add standard parameters
    params["search"] = search_term
    
    # Look for specific name patterns in the user input
    name_match = re.search(r"(?:about|by|from|with)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", user_input)
    if name_match:
        params["name"] = name_match.group(1)
    
    # Check if the query contains any $parameters
    param_matches = re.findall(r'\$(\w+)', query)
    
    # For actor/director specific queries
    if "brad pitt" in user_input.lower():
        params["actor"] = "Brad Pitt"
    if "spielberg" in user_input.lower():
        params["director"] = "Steven Spielberg"
    
    # Extract year if present
    year_match = re.search(r'\b(19\d{2}|20\d{2})\b', user_input)
    if year_match:
        params["year"] = int(year_match.group(1))
    
    # Add any missing parameters from the query
    for param in param_matches:
        if param not in params:
            if param == "actor" or param == "director" or param == "person":
                # Try to extract a name if we haven't already
                if "name" in params:
                    params[param] = params["name"]
            elif param not in ["search", "title", "name", "year"]:
                # For any other parameter, use the search term as a default
                params[param] = search_term
    
    # Log the extracted parameters with clear formatting
    logger.info("════════════════════ QUERY PARAMETERS ════════════════════")
    for key, value in params.items():
        logger.info(f"${key} = {value}")
    logger.info("═════════════════════════════════════════════════════════")
    
    return params

def execute_dynamic_query(user_input):
    """Generate and execute a dynamic Cypher query based on user input"""
    try:
        logger.info(f"═══════════════ DYNAMIC QUERY EXECUTION ═══════════════")
        logger.info(f"User input: '{user_input}'")
        
        # Generate the query
        cypher_query = generate_cypher_query(user_input)
        
        # Extract parameters
        params = extract_parameters(cypher_query, user_input)
        
        # Execute the query
        try:
            logger.info("Executing generated query...")
            result = graph.query(cypher_query, params)
            logger.info(f"Dynamic query returned {len(result)} results")
            
            # Log a sample of results
            if result and len(result) > 0:
                logger.info("════════════════════ SAMPLE RESULTS ════════════════════")
                for i, item in enumerate(result[:3]):  # Show up to 3 results
                    logger.info(f"Result {i+1}: {item}")
                if len(result) > 3:
                    logger.info(f"... and {len(result)-3} more results")
                logger.info("══════════════════════════════════════════════════════")
            
        except Exception as query_error:
            logger.error(f"Error executing dynamic query: {query_error}")
            
            # Try a simplified version if the generated query fails
            logger.info("Attempting fallback query")
            fallback_query = """
            MATCH (m:Movie)
            WHERE toLower(m.title) CONTAINS toLower($search)
            WITH m LIMIT 5
            RETURN m.title AS title
            """
            
            # For actor/person specific queries
            if "actor" in params or "person" in params or any(name in user_input.lower() for name in ["actor", "star", "cast"]):
                person_name = params.get("actor", params.get("person", params.get("name", "")))
                if person_name:
                    logger.info(f"Using person-specific fallback query for: {person_name}")
                    fallback_query = """
                    MATCH (p:Person)-[:ACTED_IN]->(m:Movie)
                    WHERE toLower(p.name) CONTAINS toLower($person)
                    RETURN m.title as title, p.name as actor
                    LIMIT 10
                    """
                    params["person"] = person_name
            
            # For director-specific queries
            elif "director" in params or "directed" in user_input.lower():
                director_name = params.get("director", params.get("name", ""))
                if director_name:
                    logger.info(f"Using director-specific fallback query for: {director_name}")
                    fallback_query = """
                    MATCH (p:Person)-[:DIRECTED]->(m:Movie)
                    WHERE toLower(p.name) CONTAINS toLower($director)
                    RETURN m.title as title, p.name as director
                    LIMIT 10
                    """
                    params["director"] = director_name
            
            # Log the fallback query
            logger.info("════════════════════ FALLBACK QUERY ════════════════════")
            for line in fallback_query.split('\n'):
                if line.strip():
                    logger.info(line)
            logger.info("══════════════════════════════════════════════════════")
            
            result = graph.query(fallback_query, params)
            logger.info(f"Fallback query returned {len(result)} results")
        
        if result and len(result) > 0:
            # Format the results for LLM context
            if isinstance(result[0], dict):
                # Convert results to a readable format
                context = "\n".join([
                    str(item) for item in result
                ])
                
                # Use LLM to format the response in a friendly way
                prompt = f"""
                Based on the following database query results, answer the user's question: "{user_input}"
                
                Query Results from database:
                {context}
                
                Respond in a friendly, conversational way. Include specific details from the query results.
                Clearly state that this information comes from the database.
                If the results don't fully answer the question, say so, but provide what information you can from these results.
                """
                
                response = llm.invoke(prompt)
                logger.info("Successfully formatted dynamic query results")
                logger.info("═════════════════════════════════════════════════════════")
                return {"result": response.content}
            else:
                logger.warning("Query returned results in unexpected format")
                logger.info("═════════════════════════════════════════════════════════")
                return {"result": None}
        else:
            logger.info("Dynamic query returned no results")
            logger.info("═════════════════════════════════════════════════════════")
            return {"result": None}
    except Exception as e:
        logger.error(f"Error in execute_dynamic_query: {e}")
        logger.info("═════════════════════════════════════════════════════════")
        return {"result": None} 