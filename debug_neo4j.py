# import streamlit as st
# import sys
# import logging

# # Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

# # Add streamlit secrets
# try:
#     # Test secrets
#     logger.info("Checking Streamlit secrets...")
#     logger.info(f"Neo4j URI: {st.secrets['NEO4J_URI']}")
#     logger.info(f"Google Model: {st.secrets['GOOGLE_MODEL']}")
#     logger.info("Secrets loaded successfully")
# except Exception as e:
#     logger.error(f"Error loading secrets: {str(e)}")
#     sys.exit(1)

# # Test Neo4j connection
# try:
#     logger.info("Testing Neo4j connection...")
#     from graph import graph
    
#     # Run a simple query
#     result = graph.query("MATCH (m:Movie) RETURN m.title LIMIT 5")
#     logger.info("Neo4j connection successful!")
#     logger.info("Sample movies:")
#     for item in result:
#         logger.info(item)
# except Exception as e:
#     logger.error(f"Neo4j connection error: {str(e)}")
#     sys.exit(1)

# # Test Google Generative AI
# try:
#     logger.info("Testing Google Generative AI...")
#     from llm import llm
#     response = llm.invoke("Tell me about The Matrix movie")
#     logger.info("LLM test successful!")
#     logger.info(f"Sample response: {response.content[:100]}...")
# except Exception as e:
#     logger.error(f"LLM error: {str(e)}")
#     sys.exit(1)

# # Test embeddings
# try:
#     logger.info("Testing embeddings...")
#     from llm import embeddings
#     test_embedding = embeddings.embed_query("Test embedding")
#     logger.info(f"Embedding dimension: {len(test_embedding)}")
#     logger.info("Embeddings test successful!")
# except Exception as e:
#     logger.error(f"Embeddings error: {str(e)}")
#     sys.exit(1)

# logger.info("All tests passed successfully!") 