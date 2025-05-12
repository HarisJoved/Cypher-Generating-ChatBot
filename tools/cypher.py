import streamlit as st
from llm import llm
from graph import graph
import logging

logger = logging.getLogger(__name__)

# Simple function to get movie information using Cypher
def cypher_qa(input):
    try:
        logger.info(f"Executing cypher query for: '{input}'")
        # Try a simple query to get relevant movie data
        cypher = """
        MATCH (m:Movie)
        WHERE toLower(m.title) CONTAINS toLower($search)
        WITH m LIMIT 5
        OPTIONAL MATCH (person:Person)-[r:ACTED_IN]->(m)
        OPTIONAL MATCH (director:Person)-[:DIRECTED]->(m)
        RETURN m.title AS title, 
               collect(distinct person.name) AS actors,
               collect(distinct director.name) AS directors
        """
        
        # Extract potential movie titles from user input
        search_term = input.lower()
        if "about" in search_term:
            search_term = search_term.split("about")[1].strip()
        
        logger.info(f"Search term for movie titles: '{search_term}'")
        result = graph.query(cypher, {"search": search_term})
        
        if result and len(result) > 0:
            logger.info(f"Found {len(result)} movies matching: '{search_term}'")
            # Format the results
            context = "\n".join([
                f"Movie: {item['title']}, " +
                f"Actors: {', '.join(item['actors'])}, " +
                f"Directors: {', '.join(item['directors'])}"
                for item in result
            ])
            
            prompt = f"""
            These are the movies found in the database matching the query:
            {context}
            
            Based on this database information only, please answer: {input}
            
            Be specific that this information comes from the database. If the database information
            doesn't completely answer the question, just share what information is available in the database.
            DO NOT supplement with your general knowledge.
            """
            logger.info("Using database information to generate response")
            
            response = llm.invoke(prompt)
            return {"result": response.content}
        else:
            logger.info(f"No movies found matching: '{search_term}'")
            # Return None to try the next approach instead of using general knowledge
            return {"result": None}
    except Exception as e:
        logger.error(f"Error in cypher_qa: {e}")
        return {"result": None} 