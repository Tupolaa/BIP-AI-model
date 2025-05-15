# ----------------------------------------- Libraries Importation ----------------------------------------- #
import streamlit as st
from huggingface_hub import InferenceClient
import io
import base64
import mimetypes
from pdf2image import convert_from_bytes
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import tempfile
import json
import re
from dotenv import load_dotenv
from docx import Document
import os
from PyPDF2 import PdfReader, PdfWriter
import tempfile


load_dotenv()
hf_api_key = os.getenv("hf_api_key")
# ------------------ Meta Llama (Model Developer) / Novita (API Provider) -> Model To Load ----------------- #
modelToLoad = "meta-llama/Llama-3.2-11B-Vision-Instruct"

# ------------------------------------------- Page Configuration ------------------------------------------- #
st.set_page_config(page_title="Finsum AI - Invoice Processor", layout="wide", page_icon=":robot_face:")

# Add custom CSS styles
# Note: Directly styling Streamlit auto-generated classes (e.g., .st-emotion-cache-xxxxxx) can break with Streamlit updates.
# A more robust method is to use Streamlit's theme configuration (config.toml) or wrap components in custom divs for styling.
st.markdown("""
<style>
    /* --- Astro.build Inspired Dark Theme Palette --- */
    :root {
        --color-background: #0a0c1a; /* Deep dark background */
        --color-card-background: #151a30; /* Slightly lighter for cards/sections */
        --color-text-base: #f4f4f4; /* Light text */
        --color-text-muted: #a0a0b3; /* Muted text for descriptions */
        --color-primary-accent: #612eff; /* Primary purple/blue accent */
        --color-secondary-accent: #e93c58; /* Secondary pink/red accent */
        --color-highlight-text: #3ecf8e; /* Greenish highlight (like code blocks) */
        --color-border: #2c304a; /* Subtle border color */
    }

    /* Base styles */
    .stApp {
        background-color: var(--color-background);
        color: var(--color-text-base);
    }

    /* Custom font for title */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@700&display=swap');

    /* Title styling */
    h1 {
        color: var(--color-primary-accent) !important;
        font-size: 2.5em !important;
        margin-bottom: 0.5em !important;
        font-family: 'Poppins', sans-serif !important;
    }

    /* Logo styling */
    .logo-container {
        display: flex;
        align-items: center;
        margin-bottom: 1.5rem;
    }
    .logo-container-sidebar .logo-text { /* Example for sidebar specific styling if needed */
        font-size: 1.3rem; /* Slightly smaller for sidebar */
    }


    .logo-text {
        font-size: 1.5rem;
        font-weight: 700;
        margin-left: 0.5rem;
        background: linear-gradient(45deg, var(--color-primary-accent), var(--color-secondary-accent));
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }

    /* Sidebar styling - BEWARE: .st-emotion-cache-6qob1r is an auto-generated class and might change */
    .st-emotion-cache-6qob1r { /* This targets the sidebar main block, Streamlit might change this class */
        background-color: var(--color-card-background) !important;
        border-right: 1px solid var(--color-border) !important;
    }
    /* A more robust way for sidebar background would be via config.toml:
       [theme]
       secondaryBackgroundColor="#151a30"
    */

    /* Sidebar section divider */
    .sidebar-section-divider { /* Renamed for clarity */
        margin: 1.5rem 0;
        padding: 0.1rem 0; /* Make it a thin line */
        border-top: 1px solid var(--color-border);
    }

    /* Button styling */
    .stButton>button {
        background: linear-gradient(45deg, var(--color-primary-accent), var(--color-secondary-accent)) !important;
        color: white !important;
        border-radius: 50px !important;
        padding: 0.5em 1.5em !important;
        font-weight: 700 !important;
        transition: transform 0.2s ease, opacity 0.2s ease !important;
        border: none !important;
    }

    .stButton>button:hover {
        transform: translateY(-3px) !important;
        opacity: 0.9 !important;
    }
    .stButton>button:disabled {
        background: var(--color-text-muted) !important;
        opacity: 0.5 !important;
        cursor: not-allowed !important;
    }


    /* File uploader styling */
    .stFileUploader {
        background-color: var(--color-card-background) !important;
        border-radius: 8px !important;
        padding: 1em !important;
        border: 1px solid var(--color-border) !important;
    }

    /* Chat message styling */
    .stChatMessage {
        background-color: var(--color-card-background) !important;
        border-radius: 8px !important;
        padding: 1em !important;
        margin-bottom: 1em !important;
        border: 1px solid var(--color-border) !important;
    }

    /* Custom avatar styling - Note: Streamlit's avatar param takes emoji or URL. This CSS won't directly style emoji avatars. */
    .user-avatar {
        background-color: #612eff !important;
    }

    .assistant-avatar {
        background-color: #e93c58 !important;
    }

    /* Chat input styling */
    .stTextInput>div>div>input {
        background-color: var(--color-card-background) !important;
        color: var(--color-text-base) !important;
        border: 1px solid var(--color-border) !important;
        border-radius: 8px !important;
        padding: 0.5em 1em !important;
    }

    /* Warning/error message styling */
    .stAlert {
        background-color: var(--color-card-background) !important;
        border: 1px solid var(--color-border) !important;
        border-radius: 8px !important;
    }

    /* Success message styling */
    .stAlert [data-testid="stMarkdownContainer"] { /* Targets markdown within success alerts */
        color: var(--color-highlight-text) !important;
    }

    /* Spinner styling */
    .stSpinner>div {
        color: var(--color-primary-accent) !important;
    }

    /* Slider styling */
    .stSlider>div>div>div>div {
        background-color: var(--color-primary-accent) !important;
    }

    /* Download button styling */
    .stDownloadButton>button { /* Targets download button specifically */
        background: linear-gradient(45deg, var(--color-primary-accent), var(--color-secondary-accent)) !important;
        color: white !important;
        border-radius: 50px !important;
        padding: 0.5em 1.5em !important;
        font-weight: 700 !important;
    }
    .stDownloadButton>button:hover {
        transform: translateY(-3px) !important;
        opacity: 0.9 !important;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------- Helper Functions -------------------------------------------- #
def display_logo(width=40, height=40, container_class_suffix=""):
    """Displays the Finsum AI logo."""
    import uuid # For unique gradient IDs if multiple SVGs are on the page
    paint0_id = f"paint0_linear_{uuid.uuid4().hex}"
    paint1_id = f"paint1_linear_{uuid.uuid4().hex}"
    paint2_id = f"paint2_linear_{uuid.uuid4().hex}"

    logo_svg = f"""
    <svg width="{width}" height="{height}" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M20 0C8.96 0 0 8.96 0 20C0 31.04 8.96 40 20 40C31.04 40 40 31.04 40 20C40 8.96 31.04 0 20 0ZM20 36C11.16 36 4 28.84 4 20C4 11.16 11.16 4 20 4C28.84 4 36 11.16 36 20C36 28.84 28.84 36 20 36Z" fill="url(#{paint0_id})"/>
        <path d="M20 8C13.36 8 8 13.36 8 20C8 26.64 13.36 32 20 32C26.64 32 32 26.64 32 20C32 13.36 26.64 8 20 8ZM20 28C15.58 28 12 24.42 12 20C12 15.58 15.58 12 20 12C24.42 12 28 15.58 28 20C28 24.42 24.42 28 20 28Z" fill="url(#{paint1_id})"/>
        <path d="M20 16C17.8 16 16 17.8 16 20C16 22.2 17.8 24 20 24C22.2 24 24 22.2 24 20C24 17.8 22.2 16 20 16Z" fill="url(#{paint2_id})"/>
        <defs>
            <linearGradient id="{paint0_id}" x1="20" y1="0" x2="20" y2="40" gradientUnits="userSpaceOnUse">
                <stop stop-color="#612EFF"/>
                <stop offset="1" stop-color="#E93C58"/>
            </linearGradient>
            <linearGradient id="{paint1_id}" x1="20" y1="8" x2="20" y2="32" gradientUnits="userSpaceOnUse">
                <stop stop-color="#612EFF"/>
                <stop offset="1" stop-color="#E93C58"/>
            </linearGradient>
            <linearGradient id="{paint2_id}" x1="20" y1="16" x2="20" y2="24" gradientUnits="userSpaceOnUse">
                <stop stop-color="#612EFF"/>
                <stop offset="1" stop-color="#E93C58"/>
            </linearGradient>
        </defs>
    </svg>
    """
    st.markdown(f"""
    <div class="logo-container {container_class_suffix}">
        {logo_svg}
    </div>
    """, unsafe_allow_html=True)

# Add logo and title
display_logo()
st.title("Finsum AI Invoice Processor")

# ------------------------------------------ API Key Input (Sidebar) --------------------------------------- #
with st.sidebar:
   
    client = None
    
    if not hf_api_key:
        st.warning("⚠️ Please enter your API token to continue.")
    else:
        try:
            client = InferenceClient(
                model="meta-llama/Llama-3.2-11B-Vision-Instruct",
                token=hf_api_key
            )
            st.success("✅ Smart Assistant is online and ready...")
            st.header("💡 Actions:")
        except Exception as e:
            st.error(f"❌ Failed to initialize Inference client: {e}")
            st.stop()

# --------------------------------------- Session State Initialization --------------------------------------- #
if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_image_bytes" not in st.session_state:
    st.session_state.uploaded_image_bytes = None

if "uploaded_image_type" not in st.session_state:
    st.session_state.uploaded_image_type = None

if "image_filename" not in st.session_state:
    st.session_state.image_filename = None

if "pdf_images" not in st.session_state:
    st.session_state.pdf_images = []

# ------------------------------------------------ File Upload ------------------------------------------------ #
uploaded_file = st.file_uploader("Upload an image or PDF...", type=["png", "jpg", "jpeg", "pdf"])

if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    filename = uploaded_file.name
    mime_type = uploaded_file.type

    if mime_type == "application/pdf":
        try:
            images = convert_from_bytes(file_bytes)
            num_pages = len(images)

            if num_pages == 0:
                st.error("📄 No pages found in the PDF.")
            else:
                selected_page_index = 0
                if num_pages > 1:
                    selected_page_index = st.slider(
                        "Select PDF page to display",
                        min_value=1,
                        max_value=num_pages,
                        value=1,
                        step=1
                    ) - 1  # zero-based index

                image = images[selected_page_index]
                image_bytes_io = io.BytesIO()
                image.save(image_bytes_io, format='JPEG')
                image_bytes = image_bytes_io.getvalue()
                mime_type = "image/jpeg"

                st.session_state.uploaded_image_bytes = image_bytes
                st.session_state.uploaded_image_type = mime_type
                st.session_state.image_filename = filename
                st.session_state.messages = []

                st.success(f"PDF '{filename}' uploaded and converted.")
                st.image(image, caption=f"{filename} (page {selected_page_index + 1})", use_container_width=True)

        except Exception as e:
            st.error(f"Failed to process PDF: {e}")
    else:
            # Inside 'else' block for image processing
        image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        image_bytes_io = io.BytesIO()
        image.save(image_bytes_io, format="JPEG")
        image_bytes = image_bytes_io.getvalue()
        st.session_state.uploaded_image_bytes = image_bytes
        st.session_state.uploaded_image_type = "image/jpeg"
        st.session_state.image_filename = filename
        st.session_state.messages = []
        st.success(f"Image '{filename}' uploaded ({mime_type}).")
        st.image(image_bytes, caption=filename, use_container_width=True)

# ------------------------------------------- PDF Summary Generator ------------------------------------------- #
def generate_invoice_from_template(summary_text):
    try:
        # Step 1: Create a temporary PDF with summary text content
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as content_pdf:
            c = canvas.Canvas(content_pdf.name, pagesize=A4)
            width, height = A4
            margin_x = 50
            margin_y = height - 250  # Adjusted to move content below logo/title

            text = c.beginText(margin_x, margin_y)
            text.setFont("Helvetica", 12)

            for line in summary_text.splitlines():
                text.textLine(line.strip())

            c.drawText(text)
            c.showPage()
            c.save()

        # Step 2: Overlay this text on the background template
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(current_dir, "pdf_template.pdf")

        template_reader = PdfReader(template_path)
        content_reader = PdfReader(content_pdf.name)

        output_writer = PdfWriter()

        # Assume only 1 page each (can be expanded if needed)
        template_page = template_reader.pages[0]
        content_page = content_reader.pages[0]

        template_page.merge_page(content_page)
        output_writer.add_page(template_page)

        # Save final merged PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as final_pdf:
            output_writer.write(final_pdf)
            return final_pdf.name

    except Exception as e:
        st.error(f"❌ Failed to generate PDF with template overlay: {e}")
        return None



# ----------------------------- Sidebar Button to Generate and Download PDF ----------------------------- #
with st.sidebar:
    if st.sidebar.button("⚙️ Generate Invoice Summary PDF File", key="gen-pdf-btn"):
        try:
            with st.spinner("🔎 Extracting invoice fields..."):
                base64_data = base64.b64encode(st.session_state.uploaded_image_bytes).decode('utf-8')
                data_url = f"data:{st.session_state.uploaded_image_type};base64,{base64_data}"
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Please extract the following fields from this invoice: "
                                        "Service Provider, Customer, Service Description, Invoice Date, Invoice Total."
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": data_url}
                            }
                        ]
                    }
                ]
                completion = client.chat.completions.create(
                    model=modelToLoad,
                    messages=messages,
                    max_tokens=512,
                    temperature=0.3
                )
                extracted_text = completion.choices[0].message.content

            # Generate PDF and save path
            pdf_path = generate_invoice_from_template(extracted_text)
            st.session_state.generated_pdf_path = pdf_path

            st.success("✅ PDF generated successfully!")

        except Exception as e:
            st.error(f"❌ Failed to extract and generate PDF: {e}")

    if st.sidebar.button("⚙️ Generate Invoice JSON File", key="gen-json-btn"):
        try:
            with st.spinner("🧠 Generating structured JSON from invoice..."):
                base64_data = base64.b64encode(st.session_state.uploaded_image_bytes).decode('utf-8')
                data_url = f"data:{st.session_state.uploaded_image_type};base64,{base64_data}"
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Extract all key invoice fields (provider, customer, items, totals) from this image. Respond with a VALID JSON object **only**, with no explanation, no markdown formatting, and no text before or after. All fields must have a flat structure with string, array, or number values. The output must be directly parseable by a JSON parser."
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": data_url}
                            }
                        ]
                    }
                ]
                completion = client.chat.completions.create(
                    model=modelToLoad,
                    messages=messages,
                    max_tokens=1024,
                    temperature=0.3
                )
                raw_json_response = completion.choices[0].message.content.strip()
                # st.text_area("🧾 Model Raw Output", raw_json_response, height=300)  # for debugging

                # Try to extract valid JSON using regex
                json_match = re.search(r"{.*}", raw_json_response, re.DOTALL)

                if json_match:
                    try:
                        json_data = json.loads(json_match.group(0))
                        formatted_json = json.dumps(json_data, indent=4)
                    except json.JSONDecodeError:
                        st.error("⚠️ Extracted JSON was still invalid.")
                        formatted_json = "{}"
                else:
                    st.error("⚠️ Could not extract valid JSON from model response.")
                    formatted_json = "{}"

            json_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w", encoding="utf-8")
            json_file.write(formatted_json)
            json_file.close()
            st.session_state.generated_json_path = json_file.name

        except Exception as e:
            st.error(f"❌ Failed to generate JSON: {e}")

    st.markdown(
        """
        <style>
            .element-container button {
                background-color: #4CAF50 !important;
                color: white !important;
                border-radius: 5px !important;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    if "generated_pdf_path" in st.session_state:
        with open(st.session_state.generated_pdf_path, "rb") as pdf_file:
            st.download_button(
                label="📥 Download Invoice Summary PDF",
                data=pdf_file,
                file_name="invoice_summary.pdf",
                mime="application/pdf",
                key="download-btn-sidebar"
            )

    if "generated_json_path" in st.session_state:
        with open(st.session_state.generated_json_path, "rb") as json_file:
            st.download_button(
                label="📥 Download Extracted JSON",
                data=json_file,
                file_name="invoice_data.json",
                mime="application/json",
                key="download-json-btn"
            )

# ------------------------------------------- Chat History Display ------------------------------------------- #
for message in st.session_state.messages:
    if isinstance(message["content"], str):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    elif isinstance(message["content"], list):
        text_parts = [item["text"] for item in message["content"] if isinstance(item, dict) and item.get("type") == "text"]
        if text_parts:
            with st.chat_message(message["role"]):
                st.markdown("".join(text_parts).strip())

# ------------------------------------------------ Chat Input ------------------------------------------------ #
prompt = st.chat_input("💬 Ask a question about the uploaded document...")

if prompt and hf_api_key and client:
    image_bytes = st.session_state.get("uploaded_image_bytes")
    mime_type = st.session_state.get("uploaded_image_type")

    if image_bytes is None:
        st.warning("📌 Please upload an image or PDF first.")
        st.stop()

    user_message_content = [{"type": "text", "text": prompt}]

    if not st.session_state.messages:
        base64_data = base64.b64encode(image_bytes).decode('utf-8')
        data_url = f"data:{mime_type};base64,{base64_data}"
        user_message_content.append({
            "type": "image_url",
            "image_url": {"url": data_url}
        })

    st.session_state.messages.append({"role": "user", "content": user_message_content})

    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with st.spinner("🤔 Thinking..."):
            completion = client.chat.completions.create(
                model=modelToLoad,
                messages=st.session_state.messages,
                max_tokens=1024,
                temperature=0.7,
            )
            assistant_response = completion.choices[0].message.content

        st.session_state.messages.append({"role": "assistant", "content": assistant_response})
        with st.chat_message("assistant"):
            st.markdown(assistant_response)

    except Exception as e:
        st.error("⚠️ An error occurred while communicating with the model:")
        st.error(str(e))
        if st.session_state.messages:
            st.session_state.messages.pop()
        st.rerun()

# ------------------------------------------- Optional: Clear Chat ------------------------------------------- #
if st.sidebar.button("🔄 Reset Chat"):
    st.session_state.messages = []
    st.session_state.uploaded_image_bytes = None
    st.session_state.uploaded_image_type = None
    st.session_state.image_filename = None
    st.session_state.pdf_images = []
    if "generated_pdf_path" in st.session_state:
        del st.session_state.generated_pdf_path
    if "generated_json_path" in st.session_state:
        del st.session_state.generated_json_path
    st.rerun()