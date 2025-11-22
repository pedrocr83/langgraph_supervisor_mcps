import sys
import os

if __name__ == "__main__":
    # Check if running via the wrapper to prevent infinite recursion
    if not os.environ.get("STREAMLIT_WRAPPER_ACTIVE"):
        import subprocess
        env = os.environ.copy()
        env["STREAMLIT_WRAPPER_ACTIVE"] = "true"
        cmd = [sys.executable, "-m", "streamlit", "run", os.path.abspath(sys.argv[0])]
        sys.exit(subprocess.call(cmd, env=env))

import streamlit as st
import asyncio

# Ensure we can import from the current directory
sys.path.append(os.getcwd())

from app import initialize_supervisor


@st.cache_resource
def get_supervisor_agent():
    """Initialize and cache the supervisor agent with MCP tools."""
    supervisor_agent, mcp_client = asyncio.run(initialize_supervisor())
    return supervisor_agent, mcp_client


# Initialize the supervisor agent (cached)
supervisor_agent, mcp_client = get_supervisor_agent()

st.set_page_config(page_title="LangGraph Supervisor", page_icon="🤖")

st.title("🤖 LangGraph Supervisor Agent")
st.markdown("Ask me anything!")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What can I do for you?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Create a container for intermediate steps
        steps_container = st.container()
        
        try:
            # Initialize thread_id for checkpointer
            if "thread_id" not in st.session_state:
                import uuid
                st.session_state.thread_id = str(uuid.uuid4())
            
            inputs = {"messages": [{"role": "user", "content": prompt}]}
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            
            for step in supervisor_agent.stream(inputs, config):
                for key, update in step.items():
                    # update is a dict that might contain "messages"
                    if "messages" in update:
                        for msg in update["messages"]:
                            
                            if hasattr(msg, 'content') and msg.content:
                                
                                # If it's a ToolMessage, show it as a status
                                if msg.type == 'tool':
                                    with steps_container:
                                        with st.status(f"Tool Output: {msg.name or 'Unknown'}", expanded=False):
                                            st.code(msg.content)
                                            
                                # If it's an AIMessage
                                elif msg.type == 'ai':
                                    # If it has tool_calls, show them
                                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                        with steps_container:
                                            for tool_call in msg.tool_calls:
                                                st.status(f"Calling Tool: {tool_call['name']}", expanded=False)
                                    
                                    # If it has content, it might be the final answer or a thought
                                    if msg.content:
                                        content_str = ""
                                        if isinstance(msg.content, list):
                                            for block in msg.content:
                                                if isinstance(block, dict) and "text" in block:
                                                    content_str += block["text"]
                                                elif isinstance(block, str):
                                                    content_str += block
                                        else:
                                            content_str = str(msg.content)
                                            
                                        full_response += content_str + "\n"
                                        message_placeholder.markdown(full_response)

        except Exception as e:
            st.error(f"An error occurred: {e}")

        # Add assistant response to chat history
        if full_response:
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        else:
             st.session_state.messages.append({"role": "assistant", "content": "Task completed (no text output)."})

