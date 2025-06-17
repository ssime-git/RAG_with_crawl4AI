from dotenv import load_dotenv
import streamlit as st
import asyncio
import os
import aiohttp
import json
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("streamlit_app")

# Load environment variables
load_dotenv()

# RAG Service API URL
RAG_SERVICE_URL = os.environ.get("RAG_SERVICE_URL", "http://rag-service:8000")

# Create a session
_session = None

def get_session():
    """Get a shared aiohttp ClientSession or create a new one if needed."""
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession()
        logger.info("Created new aiohttp ClientSession")
    return _session

async def close_session():
    """Close the global session if it exists."""
    global _session
    if _session and not _session.closed:
        await _session.close()
        _session = None
        logger.info("Closed aiohttp ClientSession")

# Check RAG service health
async def check_rag_service_health():
    """Check if the RAG service is healthy"""
    try:
        session = get_session()
        async with session.get(f"{RAG_SERVICE_URL}/health", timeout=5) as response:
            if response.status == 200:
                data = await response.json()
                logger.info(f"RAG Service is healthy: {data}")
                return True
            else:
                logger.warning(f"RAG Service health check failed: {response.status}")
                return False
    except Exception as e:
        logger.error(f"Could not connect to RAG Service: {e}")
        return False


# RAG service API functions
async def retrieve_context(query, n_results=5, collection_name="docs"):
    """Retrieve context from the RAG service"""
    try:
        session = get_session()
        async with session.post(
            f"{RAG_SERVICE_URL}/retrieve",
            json={
                "query": query,
                "n_results": n_results,
                "collection_name": collection_name
            },
            timeout=30
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data["context"]
            else:
                error_text = await response.text()
                logger.error(f"RAG Service error: {response.status} - {error_text}")
                return f"Error retrieving context: {response.status}"
    except Exception as e:
        logger.error(f"Error retrieving context: {e}")
        return f"Error: {str(e)}"

async def generate_answer(query, context, temperature=0.7, max_tokens=1000):
    """Generate an answer using the RAG service"""
    try:
        session = get_session()
        async with session.post(
            f"{RAG_SERVICE_URL}/rag-query",
            json={
                "query": query,
                "n_results": 5,
                "temperature": temperature,
                "max_tokens": max_tokens
            },
            timeout=60
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data["answer"], data["context"]
            else:
                error_text = await response.text()
                logger.error(f"RAG Service error: {response.status} - {error_text}")
                return f"Error generating answer: {response.status}", ""
    except Exception as e:
        logger.error(f"Error generating answer: {e}")
        return f"Error: {str(e)}", ""

# Chat history management
class Message:
    def __init__(self, role, content):
        self.role = role
        self.content = content

async def process_user_query(user_input):
    """Process a user query using the RAG service and return the answer"""
    # Add user message to history
    st.session_state.messages.append(Message("user", user_input))
    
    # Get answer from RAG service
    answer, context = await generate_answer(user_input, "", 0.7, 1000)
    
    # Add assistant message to history
    st.session_state.messages.append(Message("assistant", answer))
    
    # Store context for reference
    if "contexts" not in st.session_state:
        st.session_state.contexts = {}
    st.session_state.contexts[user_input] = context
    
    return answer

async def stream_response(user_input):
    """Stream the response from the RAG service"""
    answer, _ = await generate_answer(user_input, "", 0.7, 1000)
    
    # Stream the answer character by character
    full_response = ""
    message_placeholder = st.empty()
    
    for i in range(len(answer) + 1):
        full_response = answer[:i]
        message_placeholder.markdown(full_response)
        await asyncio.sleep(0.01)  # Simulate streaming
    
    # Add the message to history after streaming
    st.session_state.messages.append(Message("assistant", answer))


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~ Main Function with UI Creation ~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

async def main():
    st.title("ChromaDB Crawl4AI RAG AI Agent")

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "contexts" not in st.session_state:
        st.session_state.contexts = {}

    # Check if RAG service is healthy
    service_status = await check_rag_service_health()
    if not service_status:
        st.error("⚠️ RAG Service is not available. Please check the service and try again.")
    else:
        st.success("✅ RAG Service is connected and healthy")

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg.role):
            st.markdown(msg.content)

    # Chat input for the user
    user_input = st.chat_input("What do you want to know?")

    if user_input:
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)

        # Display assistant response with streaming effect
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            # Stream the response
            await stream_response(user_input)
            
    # Add a section to show the retrieved context if available
    if st.session_state.messages and "contexts" in st.session_state and st.session_state.contexts:
        with st.expander("View Retrieved Context"):
            # Get the last user query
            last_user_queries = [msg.content for msg in st.session_state.messages if msg.role == "user"]
            if last_user_queries:
                last_query = last_user_queries[-1]
                if last_query in st.session_state.contexts:
                    st.markdown("### Context Used for Last Query")
                    st.markdown(st.session_state.contexts[last_query])
                else:
                    st.markdown("No context available for the last query.")
            else:
                st.markdown("No queries have been made yet.")
                
    # Add a section for advanced options
    with st.sidebar:
        st.header("RAG Settings")
        st.markdown("Adjust the settings for the RAG system")
        
        # Collection name
        collection_name = st.text_input("Collection Name", value="docs")
        
        # Number of results
        n_results = st.slider("Number of Results", min_value=1, max_value=10, value=5)
        
        # Temperature
        temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
        
        # Clear chat history button
        if st.button("Clear Chat History"):
            st.session_state.messages = []
            st.session_state.contexts = {}
            st.experimental_rerun()


# Initialize the page configuration outside of the main function
st.set_page_config(page_title="ChromaDB Crawl4AI RAG AI Agent", layout="wide")

# Helper function to run async code in Streamlit
def run_async(coroutine):
    import nest_asyncio
    import asyncio
    
    # Apply nest_asyncio to allow nested event loops
    nest_asyncio.apply()
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coroutine)

# Register cleanup handler for when the app exits
import atexit
import asyncio

def cleanup():
    """Clean up resources when the app exits"""
    try:
        # Run the async cleanup in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(close_session())
        loop.close()
        logger.info("Cleaned up resources on exit.")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

# Register the cleanup function
atexit.register(cleanup)

# Run the main function
if __name__ == "__main__":
    # Import nest_asyncio at the top level for nested event loops
    import nest_asyncio
    nest_asyncio.apply()
    
    # Run the main function
    run_async(main())