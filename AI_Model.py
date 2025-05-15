import streamlit as st
from huggingface_hub import InferenceClient
import io
import base64 # Import base64 for encoding
import mimetypes # To guess mime type if not available, though Streamlit provides it

# --- Page Configuration ---
st.set_page_config(page_title="Multimodal Chatbot", layout="wide")

st.title("Image Chatbot")

# --- API Key Input (Sidebar) ---
with st.sidebar:
    st.header("Configuration")
    # IMPORTANT: If using a specific provider like "novita", this token
    # needs to be the API key for that provider, not necessarily a standard
    # Hugging Face token. Get your API key from the provider's dashboard.
    hf_api_key = st.text_input("Enter your API Token (for Novita.ai or chosen provider):", type="password")
    st.markdown("Get your token from your provider's dashboard (e.g., Novita.ai)")
    st.markdown("Ensure your token and provider have access to the model `meta-llama/Llama-3.2-11B-Vision-Instruct`")

    client = None # Initialize client to None
    if not hf_api_key:
        st.warning("Please enter your API token to continue.")
    else:
        try:
            # Initialize the client using the specified provider
            client = InferenceClient(
                provider="novita", # <-- Explicitly set the provider here
                token=hf_api_key # Hugging Face Access Token
            )
            # Optional: You could try a basic call specific to the provider to verify authentication
            st.success("Inference client initialized with provider 'novita'.")
        except Exception as e:
            st.error(f"Failed to initialize Inference client: {e}")
            st.warning("Double check your API token (ensure it's for the provider) and the 'provider' setting.")
            st.error(f"Error details: {e}")


# --- Session State Initialization ---
# We need to store the conversation history and the image data.
if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_image_bytes" not in st.session_state:
    st.session_state.uploaded_image_bytes = None # Stores image bytes

if "uploaded_image_type" not in st.session_state:
    st.session_state.uploaded_image_type = None # Stores image mime type (e.g., "image/jpeg")

if "image_filename" not in st.session_state:
    st.session_state.image_filename = None # Stores filename for display


# --- Image Upload ---
uploaded_file = st.file_uploader("Upload an image...", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    # Read the image file as bytes
    image_bytes = uploaded_file.getvalue()
    filename = uploaded_file.name
    mime_type = uploaded_file.type # Get the MIME type directly from Streamlit

    # Check if a new image is uploaded or if it's a re-upload of the same one
    if st.session_state.uploaded_image_bytes is None or st.session_state.image_filename != filename:
        st.session_state.uploaded_image_bytes = image_bytes
        st.session_state.uploaded_image_type = mime_type
        st.session_state.image_filename = filename
        st.session_state.messages = [] # Clear history for a new image
        st.success(f"Image '{filename}' uploaded ({mime_type}). You can now ask questions.")
        # Display the uploaded image
        st.image(image_bytes, caption=filename, use_column_width=True)
    else:
         # If the same image is re-uploaded, just display it and continue the conversation
         st.image(image_bytes, caption=filename, use_column_width=True)


# --- Display Chat History ---
# We display the conversation. The image itself is shown separately after upload.
for message in st.session_state.messages:
    # Messages can have complex content (list of parts) or simple string content (from assistant)
    if isinstance(message["content"], str):
         with st.chat_message(message["role"]):
             st.markdown(message["content"])
    elif isinstance(message["content"], list):
        # This handles messages with complex content (like the initial user message with text and image)
        # We'll only display the text part here to avoid re-displaying the image in chat history
        text_content_parts = []
        for item in message["content"]:
             # Check for dictionary and 'type' key before accessing it
             if isinstance(item, dict) and item.get("type") == "text":
                 text_content_parts.append(item.get("text", ""))
             # We are deliberately NOT displaying image parts here
             # elif isinstance(item, dict) and item.get("type") == "image_url":
             #     st.image(item["image_url"]["url"], caption="Uploaded Image Part", width=100) # Example, usually image is shown once
        if text_content_parts:
             with st.chat_message(message["role"]):
                 st.markdown("".join(text_content_parts).strip())


# --- Chat Input ---
prompt = st.chat_input("Ask a question about the image...")

if prompt and hf_api_key and client:
    if st.session_state.uploaded_image_bytes is None:
        st.warning("Please upload an image first.")
        st.stop()

    # Prepare the content for the current user message.
    # The content is a list of parts.
    user_message_content = [{"type": "text", "text": prompt}]

    # If this is the FIRST message in the conversation history,
    # we need to include the image data alongside the text prompt.
    # The API expects image data as a Base64 encoded data URL within an image_url object.
    if not st.session_state.messages:
         # Get image bytes and type from state
         image_bytes = st.session_state.uploaded_image_bytes
         mime_type = st.session_state.uploaded_image_type # Get the stored MIME type

         # Base64 encode the image bytes
         base64_image = base64.b64encode(image_bytes).decode('utf-8')

         # Create the data URL
         data_url = f"data:{mime_type};base64,{base64_image}"

         # Append the image part formatted as expected by the API
         user_message_content.append({
              "type": "image_url",
              "image_url": {"url": data_url}
         })

    # Add the user's complete message (with image data URL if first) to the session state history
    # This structured list is what the InferenceClient will send to the API
    st.session_state.messages.append({"role": "user", "content": user_message_content})

    # Display the user's text message in the chat bubble
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- Call the Inference API ---
    try:
        with st.spinner("Thinking..."):
            # Pass the ENTIRE session state messages list to the client.
            # The client handles the communication, including the structured image_url part.
            completion = client.chat.completions.create(
                model="meta-llama/Llama-3.2-11B-Vision-Instruct", # Your model name - Ensure this works with the provider
                messages=st.session_state.messages, # <--- Pass the structured list
                max_tokens=1024, # Adjust as needed
                temperature=0.7, # Adjust as needed
                # Add other parameters if required by the model or provider
            )

            # The response content is usually a string for text models
            assistant_response = completion.choices[0].message.content

        # Add assistant response to state
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})

        # Display assistant response
        with st.chat_message("assistant"):
            st.markdown(assistant_response)

    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.error("Please check your API token (is it for the provider?), the model name (is it supported by the provider?), and the provider setting.")
        st.error("Error details: " + str(e)) # Print exception details for debugging
        # Optional: Remove the last user message from history if the API call failed
        # This prevents the conversation from getting stuck after an error
        if st.session_state.messages:
             # Remove the user message that caused the error
             st.session_state.messages.pop()
        # Use the corrected rerun command
        st.rerun() # Rerun to clear the input box and spinner