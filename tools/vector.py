import streamlit as st
from llm import llm, embeddings
from graph import graph
import logging

logger = logging.getLogger(__name__)

# Simple function to get movie plot information
def get_movie_plot(input):
    try:
        logger.info(f"Searching for movie plots containing terms from: '{input}'")
        # Using direct Cypher query to find movies with plots
        cypher = """
        MATCH (m:Movie)
        WHERE m.plot IS NOT NULL AND toLower(m.plot) CONTAINS toLower($search)
        WITH m LIMIT 5
        OPTIONAL MATCH (person:Person)-[r:ACTED_IN]->(m)
        OPTIONAL MATCH (director:Person)-[:DIRECTED]->(m)
        RETURN m.title AS title, m.plot AS plot, 
               collect(distinct person.name) AS actors,
               collect(distinct director.name) AS directors
        """
        
        # Extract key terms from query
        search_terms = input.lower().split()
        search_terms = [term for term in search_terms if len(term) > 3]
        search_query = " ".join(search_terms) if search_terms else input.lower()
        
        logger.info(f"Search query for movie plots: '{search_query}'")
        result = graph.query(cypher, {"search": search_query})
        
        if not result or len(result) == 0:
            logger.info("No matching movie plots found")
            return {"output": None}  # Return None to try other approaches
        
        # Format the results in a readable way
        context = "\n\n".join([
            f"Title: {item['title']}\n"
            f"Plot: {item['plot']}\n"
            f"Actors: {', '.join(item['actors'])}\n"
            f"Directors: {', '.join(item['directors'])}"
            for item in result
        ])
        
        logger.info(f"Found {len(result)} movies with matching plots")
        
        # Call the LLM with the retrieved context
        prompt = f"""
        Based on these movie details from our database, answer the question: {input}
        
        Movie Information from the database:
        {context}
        
        Base your answer only on the information provided above. Make it clear this information comes from the database.
        Do not supplement with your general knowledge. If the database information doesn't fully answer the question,
        just provide what information is available from these results.
        """
        
        response = llm.invoke(prompt)
        return {"output": response.content}
    except Exception as e:
        logger.error(f"Error in get_movie_plot: {e}")
        return {"output": None}  # Return None to try other approaches 