from llm import llm
from graph import graph
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create a movie chat chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser

# Create a set of tools
from langchain.tools import Tool
from tools.vector import get_movie_plot
from tools.cypher import cypher_qa
from tools.cypher_generator import execute_dynamic_query
from tools.general_conversation import is_general_conversation, handle_general_chat

# Create the agent
try:
    # Create a more versatile chat prompt that handles both movie questions and general conversation
    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a friendly and knowledgeable assistant specializing in movies, but also capable of having natural conversations.
When asked about movies, provide detailed information about plots, actors, directors, and related recommendations.
When engaged in general conversation, respond in a warm, personable manner as if talking to a friend.
Always maintain a helpful, positive tone regardless of the topic."""),
        ("human", "{input}"),
    ])

    general_chat = chat_prompt | llm | StrOutputParser()

    def generate_response(user_input):
        """Generate a response based on user input"""
        try:
            # Check if the input is general conversation
            if is_general_conversation(user_input):
                logger.info(f"TOOL USED: general_conversation.handle_general_chat - User input: '{user_input}'")
                general_result = handle_general_chat(user_input)
                if general_result and "output" in general_result and general_result["output"]:
                    logger.info("RESPONSE FROM: general_conversation.handle_general_chat - Using general conversation response")
                    return general_result["output"]
            
            # First try to get information about specific movies
            logger.info(f"TOOL USED: vector.get_movie_plot - Attempting to find movie plot info for: '{user_input}'")
            movie_info = get_movie_plot(user_input)
            if movie_info and "output" in movie_info and movie_info["output"]:
                logger.info("RESPONSE FROM: vector.get_movie_plot - Using movie plot information")
                return movie_info["output"]
            
            # If no specific movie info, try standard cypher query
            logger.info(f"TOOL USED: cypher.cypher_qa - Attempting standard cypher query for: '{user_input}'")
            cypher_result = cypher_qa(user_input)
            
            # If standard cypher returned valid database results, use them
            if cypher_result and "result" in cypher_result and cypher_result["result"]:
                logger.info("RESPONSE FROM: cypher.cypher_qa - Using movie information from database")
                return cypher_result["result"]
            else:
                logger.info("Standard cypher query returned no results, trying dynamic query")
            
            # Try dynamic query generation for all movie-related queries
            logger.info(f"TOOL USED: cypher_generator.execute_dynamic_query - Attempting dynamic cypher query for: '{user_input}'")
            dynamic_result = execute_dynamic_query(user_input)
            if dynamic_result and "result" in dynamic_result and dynamic_result["result"]:
                logger.info("RESPONSE FROM: cypher_generator.execute_dynamic_query - Using dynamically generated query results")
                return dynamic_result["result"]
            
            # Final fallback to general chat - only used for movie questions when all database approaches fail
            logger.info(f"TOOL USED: general_chat fallback - No database information found, using general chat for: '{user_input}'")
            return general_chat.invoke({"input": user_input})
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            # Final fallback
            try:
                logger.info(f"TOOL USED: final llm fallback - All other methods failed for: '{user_input}'")
                return llm.invoke(f"As a friendly assistant who knows about movies but can also chat about other topics, respond to this: {user_input}").content
            except:
                logger.error(f"COMPLETE FAILURE: Could not generate any response for: '{user_input}'")
                return "I'm having trouble right now. Please try again later."
except Exception as e:
    logger.error(f"Error setting up movie agent: {e}")
    
    # Ultra-simple fallback
    def generate_response(user_input):
        try:
            logger.info(f"TOOL USED: ultra-simple fallback - Agent setup failed, using direct LLM call for: '{user_input}'")
            return llm.invoke(f"As a friendly assistant who knows about movies but can also chat about other topics, respond to this: {user_input}").content
        except:
            logger.error(f"COMPLETE FAILURE: Could not generate any response even with ultra-simple fallback for: '{user_input}'")
            return "I apologize, but I'm experiencing technical difficulties. Please try again later." 