# ----------------------------------------- Libraries Importation ----------------------------------------- #
import streamlit as st
from huggingface_hub import InferenceClient
import io
import base64
# import mimetypes # Not strictly used in the final version but good for general file type handling
from pdf2image import convert_from_bytes
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch # For easier measurement in PDF
# import tempfile # No longer needed for PDF/JSON generation for download
import json
import re
import os
import time # Added for retry delay
from dotenv import load_dotenv
# from docx import Document # Not used in the current flow
# from docx2pdf import convert # Not used in the current flow
# import pythoncom # Windows specific, not used in the current flow
# from win32com.client import Dispatch # Windows specific, not used in the current flow

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
    display_logo(width=30, height=30, container_class_suffix="logo-container-sidebar")
    client = None
    if not hf_api_key:
        st.warning("⚠️ Please enter your Hugging Face API token to continue.")
        # You might want to add st.text_input here if you allow users to paste it directly
        # Or guide them to set the .env file
    else:
        try:
            client = InferenceClient(
                model=modelToLoad, # Using the globally defined model
                token=hf_api_key
            )
            st.success("✅ Smart Assistant is online and ready.")
        except Exception as e:
            st.error(f"❌ Failed to initialize Inference client: {e}")
            st.stop()

    # Section divider for actions
    st.markdown('<div class="sidebar-section-divider"></div>', unsafe_allow_html=True)
    st.header("💡 Actions:")


# Initialize session state for messages and other data
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploaded_image_bytes" not in st.session_state:
    st.session_state.uploaded_image_bytes = None
if "uploaded_image_type" not in st.session_state:
    st.session_state.uploaded_image_type = None
if "image_filename" not in st.session_state:
    st.session_state.image_filename = None
if "pdf_images" not in st.session_state: # For multi-page PDFs
    st.session_state.pdf_images = []
if "generated_pdf_bytes" not in st.session_state:
    st.session_state.generated_pdf_bytes = None
if "generated_json_bytes" not in st.session_state:
    st.session_state.generated_json_bytes = None


# ----------------------------------------- Image/PDF Upload -------------------------------------------- #
uploaded_file = st.file_uploader("📁 Upload an invoice image or PDF file", type=["png", "jpg", "jpeg", "pdf"])

if uploaded_file is not None:
    file_type = uploaded_file.type
    file_name = uploaded_file.name
    st.session_state.image_filename = file_name # Store filename

    # Reset previously generated files if a new file is uploaded
    st.session_state.generated_pdf_bytes = None
    st.session_state.generated_json_bytes = None


    if file_type.startswith("image"):
        image_bytes_content = uploaded_file.read() # Read bytes
        try:
            image = Image.open(io.BytesIO(image_bytes_content)) # Open image from bytes
            st.image(image, caption=f"Uploaded Image: {file_name}", use_container_width=True)
            st.session_state.uploaded_image_bytes = image_bytes_content # Store original bytes
            st.session_state.uploaded_image_type = file_type
            st.session_state.pdf_images = [] # Clear any previous PDF images
        except Exception as e:
            st.error(f"⚠️ Failed to load image: {e}")
            st.session_state.uploaded_image_bytes = None

    elif file_type == "application/pdf":
        with st.spinner("⏳ Converting PDF to images..."):
            pdf_bytes_content = uploaded_file.read()
            try:
                images_from_pdf = convert_from_bytes(pdf_bytes_content)
                st.session_state.pdf_images = []
                for i, img in enumerate(images_from_pdf):
                    buffered = io.BytesIO()
                    img.save(buffered, format="JPEG") # Save as JPEG for consistency
                    st.session_state.pdf_images.append(buffered.getvalue())

                if st.session_state.pdf_images:
                    st.image(st.session_state.pdf_images[0], caption=f"First Page of Uploaded PDF: {file_name}", use_container_width=True)
                    # For processing, typically use the first page or allow selection
                    st.session_state.uploaded_image_bytes = st.session_state.pdf_images[0]
                    st.session_state.uploaded_image_type = "image/jpeg"
                    st.info(f"📄 PDF has {len(st.session_state.pdf_images)} page(s). Processing the first page. Ask in chat to process a different page.")
                else:
                    st.error("⚠️ Could not convert PDF to images.")
                    st.session_state.uploaded_image_bytes = None
            except Exception as e:
                st.error(f"⚠️ PDF conversion failed: {e}")
                st.session_state.uploaded_image_bytes = None
    else:
        st.error("⚠️ Unsupported file type. Please upload a PNG, JPG, JPEG, or PDF file.")
        st.session_state.uploaded_image_bytes = None

# ----------------------------- Helper Functions for Invoice Processing ----------------------------- #
def extract_fields_with_retries(current_client, messages_payload, model_name, retries=3, delay=2):
    """
    Extracts information from an invoice image with retries.

    Args:
        current_client: The Hugging Face Inference Client instance.
        messages_payload (list): The list of messages (including image and text) to send to the model.
        model_name (str): The name of the model to use.
        retries (int): Number of retries.
        delay (int): Time to wait between retries in seconds.

    Returns:
        str: The extracted text, or None on failure.
    """
    if not current_client: # Check if client is initialized
        st.error("❌ LLM Client not initialized.")
        return None
    for attempt in range(retries):
        try:
            completion = current_client.chat.completions.create(
                model=model_name,
                messages=messages_payload,
                max_tokens=1024, # Increased for potentially more complex extractions
                temperature=0.2  # Lower temperature for more deterministic extraction
            )
            return completion.choices[0].message.content
        except Exception as e:
            st.warning(f"Attempt {attempt + 1}/{retries} for extraction failed: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                st.error(f"❌ All {retries} extraction attempts failed.")
    return None

def generate_invoice_summary_pdf_bytes(extracted_data):
    """
    Generates a PDF invoice summary from extracted data (ideally structured dictionary).
    Current implementation uses basic parsing from string if dict not provided.
    For robustness, passing a structured dictionary is highly recommended.

    Args:
        extracted_data (str or dict): Text extracted from the invoice or a structured dictionary.
                                      (Current implementation handles str, but dict is preferred)

    Returns:
        bytes: Byte stream of the generated PDF file. Returns None if data is insufficient.
    """
    # Default template data (can be overridden by extracted_data)
    template_data = {
        "provider_name": "Finsum AI (Sample)",
        "provider_address": "123 AI Avenue, Tech City",
        "provider_contact": "info@finsum.ai",
        "customer_name": "Customer Name (Sample)",
        "customer_address": "456 Data Street, Analytics Town",
        "invoice_number": "INV-2024-001",
        "invoice_date": "2024-07-26",
        "items": [
            {"description": "AI Consultation Service", "quantity": 1, "unit_price": 150.00, "total": 150.00},
            {"description": "Data Processing Module", "quantity": 2, "unit_price": 75.00, "total": 150.00},
        ],
        "subtotal": 300.00,
        "tax_rate": 0.08,  # 8%
        "tax_amount": 24.00,
        "total": 324.00,
        "notes": "Thank you for your business!"
    }

    # --- Try to parse fields from extracted text (very basic example) ---
    # --- It's STRONGLY recommended to have the LLM extract a structured JSON,
    # --- then use that JSON to populate template_data. ---
    if isinstance(extracted_data, str):
        lines = extracted_data.splitlines()
        # This is a placeholder for more sophisticated parsing or using LLM-extracted structured data.
        # For now, it will mostly use the template_data defaults unless specific keywords are found.
        for line in lines:
            if "Service Provider:" in line or "Provider:" in line:
                template_data["provider_name"] = line.split(":", 1)[1].strip()
            elif "Customer Name:" in line or "Customer:" in line:
                template_data["customer_name"] = line.split(":", 1)[1].strip()
            elif "Invoice Date:" in line or "Date:" in line:
                template_data["invoice_date"] = line.split(":", 1)[1].strip()
            elif "Invoice Total:" in line or "Total Amount:" in line or "Total:" in line :
                try:
                    total_str = line.split(":", 1)[1].strip().replace("$", "").replace("€", "").replace("£", "").replace(",", "")
                    template_data["total"] = float(total_str)
                    # Rough calculation for subtotal and tax (for demonstration only)
                    if template_data["tax_rate"] is not None and template_data["tax_rate"] > -1: # ensure tax_rate is valid
                        template_data["subtotal"] = template_data["total"] / (1 + template_data["tax_rate"])
                        template_data["tax_amount"] = template_data["total"] - template_data["subtotal"]
                    else: # if no tax_rate, subtotal is total
                        template_data["subtotal"] = template_data["total"]
                        template_data["tax_amount"] = 0.0

                except ValueError:
                    st.warning("Could not parse invoice total from extracted text. Using default.")
            # Add more parsing rules as needed for other fields like items, invoice_number etc.

    elif isinstance(extracted_data, dict): # If structured data is passed
        # Sensible updates: only update if key exists in extracted_data
        for key, value in extracted_data.items():
            if key in template_data and value is not None:
                if key == "items" and isinstance(value, list): # Ensure items is a list of dicts
                    template_data[key] = value
                elif key not in ["items"]:
                     template_data[key] = value
        # Recalculate totals if items are provided
        if "items" in extracted_data and isinstance(extracted_data["items"], list):
            subtotal = sum(item.get("total", 0) for item in extracted_data["items"])
            template_data["subtotal"] = subtotal
            if "tax_rate" in template_data and template_data["tax_rate"] is not None:
                 template_data["tax_amount"] = subtotal * template_data["tax_rate"]
                 template_data["total"] = subtotal + template_data["tax_amount"]
            else: # no tax
                 template_data["tax_amount"] = 0.0
                 template_data["total"] = subtotal


    pdf_buffer = io.BytesIO()
    # Use a common font that supports basic Latin characters. For Chinese, specific fonts are needed.
    # from reportlab.pdfbase.ttfonts import TTFont
    # from reportlab.pdfbase import pdfmetrics
    # pdfmetrics.registerFont(TTFont('SimSun', 'SimSun.ttf')) # Example for Chinese
    # c.setFont("SimSun", 12)
    c = canvas.Canvas(pdf_buffer, pagesize=A4)
    c.setFont("Helvetica", 10) # Default font

    width, height = A4 # Page dimensions

    # Margins
    margin_x = 0.75 * inch
    margin_y = 0.75 * inch
    content_width = width - 2 * margin_x
    current_y = height - margin_y

    # --- Header: Provider Info ---
    c.setFont("Helvetica-Bold", 16)
    current_y -= 0.5 * inch
    c.drawString(margin_x, current_y, str(template_data.get("provider_name", "Provider Name N/A")))
    c.setFont("Helvetica", 10)
    current_y -= 0.25 * inch
    c.drawString(margin_x, current_y, str(template_data.get("provider_address", "Provider Address N/A")))
    current_y -= 0.2 * inch
    c.drawString(margin_x, current_y, str(template_data.get("provider_contact", "Provider Contact N/A")))

    # --- Invoice Title & Details ---
    current_y -= 0.75 * inch
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, current_y, "INVOICE SUMMARY")
    current_y -= 0.5 * inch

    c.setFont("Helvetica", 10)
    invoice_details_x_start = margin_x + content_width * 0.6 # Align to the right
    c.drawString(invoice_details_x_start, current_y, f"Invoice #: {template_data.get('invoice_number', 'N/A')}")
    current_y -= 0.2 * inch
    c.drawString(invoice_details_x_start, current_y, f"Date: {template_data.get('invoice_date', 'N/A')}")


    # --- Customer Info (Bill To) ---
    # current_y -= 0.3 * inch # Space before Bill To
    bill_to_y = height - margin_y - 0.5 * inch # Align with provider info but on the right
    c.setFont("Helvetica-Bold", 12)
    c.drawString(invoice_details_x_start, bill_to_y, "BILL TO:") # Right aligned with invoice details
    c.setFont("Helvetica", 10)
    bill_to_y -= 0.25 * inch
    c.drawString(invoice_details_x_start, bill_to_y, str(template_data.get("customer_name", "Customer Name N/A")))
    bill_to_y -= 0.2 * inch
    c.drawString(invoice_details_x_start, bill_to_y, str(template_data.get("customer_address", "Customer Address N/A")))

    current_y -= 0.5 * inch # Space before items table

    # --- Items Table Header ---
    c.setFont("Helvetica-Bold", 10)
    header_y = current_y
    col_positions = [margin_x, margin_x + 2.5 * inch, margin_x + 3.5 * inch, margin_x + 4.5 * inch, margin_x + 5.5 * inch]
    c.drawString(col_positions[0], header_y, "Description")
    c.drawRightString(col_positions[2] - 0.1 * inch, header_y, "Quantity") # Adjusted for right alignment
    c.drawRightString(col_positions[3] - 0.1 * inch, header_y, "Unit Price")
    c.drawRightString(col_positions[4] + 0.75 * inch, header_y, "Total") # Adjusted for right alignment of last column
    current_y -= 0.1 * inch
    c.line(margin_x, current_y, width - margin_x, current_y) # Horizontal line
    current_y -= 0.25 * inch

    # --- Items ---
    c.setFont("Helvetica", 10)
    items_list = template_data.get("items", [])
    if not items_list: # Add a placeholder if no items
        items_list = [{"description": "No items found in extraction", "quantity": "", "unit_price": "", "total": ""}]

    for item in items_list:
        c.drawString(col_positions[0], current_y, str(item.get("description", "N/A")))
        c.drawRightString(col_positions[2] - 0.1 * inch, current_y, str(item.get("quantity", "")))
        c.drawRightString(col_positions[3] - 0.1 * inch, current_y, f"${item.get('unit_price', 0.00):.2f}" if isinstance(item.get('unit_price'), (int, float)) else str(item.get('unit_price', '')))
        c.drawRightString(col_positions[4] + 0.75 * inch, current_y, f"${item.get('total', 0.00):.2f}" if isinstance(item.get('total'), (int, float)) else str(item.get('total', '')))
        current_y -= 0.25 * inch
        if current_y < margin_y + 2 * inch: # Add new page if content is too low
            c.showPage()
            c.setFont("Helvetica", 10)
            current_y = height - margin_y - 0.5 * inch # Reset Y for new page

    # --- Totals Section ---
    current_y -= 0.1 * inch # Space before totals line
    c.line(margin_x + 3.5 * inch, current_y, width - margin_x, current_y) # Line above subtotal
    current_y -= 0.25 * inch

    total_label_x = margin_x + 4.0 * inch
    total_value_x = width - margin_x # Right align values

    c.drawString(total_label_x, current_y, "Subtotal:")
    c.drawRightString(total_value_x, current_y, f"${template_data.get('subtotal', 0.00):.2f}")
    current_y -= 0.25 * inch

    if template_data.get('tax_amount', 0.00) > 0 or template_data.get('tax_rate', 0.00) > 0:
        c.drawString(total_label_x, current_y, f"Tax ({template_data.get('tax_rate', 0.0)*100:.0f}%):")
        c.drawRightString(total_value_x, current_y, f"${template_data.get('tax_amount', 0.00):.2f}")
        current_y -= 0.25 * inch

    c.setFont("Helvetica-Bold", 12)
    c.drawString(total_label_x, current_y, "TOTAL:")
    c.drawRightString(total_value_x, current_y, f"${template_data.get('total', 0.00):.2f}")
    current_y -= 0.5 * inch

    # --- Notes ---
    c.setFont("Helvetica", 10)
    notes_y_start = margin_y + 1.0 * inch # Position notes at the bottom
    if current_y > notes_y_start + 0.5 * inch : # Only add notes if there's space, otherwise they might be too high
        current_y = notes_y_start
        c.drawString(margin_x, current_y, "Notes:")
        current_y -= 0.2 * inch
        c.drawString(margin_x, current_y, str(template_data.get("notes", "Thank you for your business!")))

    c.save()
    pdf_bytes = pdf_buffer.getvalue()
    pdf_buffer.close()
    return pdf_bytes

# ----------------------------- Sidebar Button to Generate and Download PDF ----------------------------- #
with st.sidebar:
    # Document Processing Section
    st.markdown("### Document Processing")
    process_button_disabled = st.session_state.get("uploaded_image_bytes") is None

    if st.button("⚙️ Generate Invoice Summary PDF File", key="gen-pdf-btn", disabled=process_button_disabled):
        if client and st.session_state.uploaded_image_bytes:
            try:
                with st.spinner("🔎 Extracting invoice fields for PDF..."):
                    base64_data = base64.b64encode(st.session_state.uploaded_image_bytes).decode('utf-8')
                    data_url = f"data:{st.session_state.uploaded_image_type};base64,{base64_data}"
                    
                    # Prompt for structured data for better PDF generation
                    extraction_prompt = (
                        "Please extract the following fields from this invoice: "
                        "Service Provider Name (provider_name), Service Provider Address (provider_address), Service Provider Contact (provider_contact), "
                        "Customer Name (customer_name), Customer Address (customer_address), "
                        "Invoice Number (invoice_number), Invoice Date (invoice_date), "
                        "A list of line items (items) where each item has 'description', 'quantity', 'unit_price', and 'total'. "
                        "Subtotal (subtotal), Tax Amount (tax_amount), Tax Rate (tax_rate as a decimal, e.g., 0.08 for 8%), and Invoice Total (total). "
                        "Return a VALID JSON object only. If a field is not found, use null or an appropriate default (e.g., empty string, 0 for numbers, empty list for items)."
                    )
                    messages_for_pdf_extraction = [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": extraction_prompt},
                                {"type": "image_url", "image_url": {"url": data_url}}
                            ]
                        }
                    ]
                    extracted_content_str = extract_fields_with_retries(client, messages_for_pdf_extraction, modelToLoad)

                if extracted_content_str:
                    extracted_data_for_pdf = {}
                    try:
                        # Try to find JSON block
                        json_match = re.search(r"```json\s*({.*?})\s*```", extracted_content_str, re.DOTALL)
                        if not json_match:
                             json_match = re.search(r"({.*?})", extracted_content_str, re.DOTALL) # Fallback for plain JSON

                        if json_match:
                            json_str = json_match.group(1)
                            extracted_data_for_pdf = json.loads(json_str)
                            st.write("Extracted data for PDF:", extracted_data_for_pdf) # For debugging
                        else:
                            st.warning("⚠️ Could not find a JSON block in the model's response for PDF. Will use basic text parsing.")
                            # Fallback to using the raw string if JSON parsing fails or not found
                            extracted_data_for_pdf = extracted_content_str

                    except json.JSONDecodeError as json_err:
                        st.warning(f"⚠️ Failed to parse extracted JSON for PDF: {json_err}. Using raw text.")
                        extracted_data_for_pdf = extracted_content_str # Fallback

                    pdf_bytes = generate_invoice_summary_pdf_bytes(extracted_data_for_pdf)
                    if pdf_bytes:
                        st.session_state.generated_pdf_bytes = pdf_bytes
                        st.success("✅ PDF generated successfully!")
                    else:
                        st.error("❌ Failed to generate PDF bytes.")
                else:
                    st.error("❌ Failed to extract information from the invoice for PDF generation.")

            except Exception as e:
                st.error(f"❌ Failed to extract and generate PDF: {e}")
        elif not client:
            st.error("❌ LLM Client not initialized. Cannot generate PDF.")
        else:
            st.warning("📌 Please upload an image or PDF first to generate the summary.")


    if st.button("⚙️ Generate Invoice JSON File", key="gen-json-btn", disabled=process_button_disabled):
        if client and st.session_state.uploaded_image_bytes:
            try:
                with st.spinner("🧠 Generating structured JSON from invoice..."):
                    base64_data = base64.b64encode(st.session_state.uploaded_image_bytes).decode('utf-8')
                    data_url = f"data:{st.session_state.uploaded_image_type};base64,{base64_data}"
                    
                    json_prompt = (
                        "Extract all key invoice fields (provider, customer, items, totals) from this image. Return a VALID JSON object only, without nesting individual address lines or using sets. All fields must have a flat structure and values as strings, arrays, or numbers."
                    )
                    messages_for_json = [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": json_prompt},
                                {"type": "image_url", "image_url": {"url": data_url}}
                            ]
                        }
                    ]
                    raw_json_response = extract_fields_with_retries(client, messages_for_json, modelToLoad)

                if raw_json_response:
                    # Try to extract valid JSON using regex, looking for ```json ... ``` or just { ... }
                    json_str_to_parse = None
                    match_json_block = re.search(r"```json\s*({.*?})\s*```", raw_json_response, re.DOTALL)
                    if match_json_block:
                        json_str_to_parse = match_json_block.group(1)
                    else:
                        # Fallback: try to find the first and last curly brace
                        match_curly_braces = re.search(r"({.*})", raw_json_response, re.DOTALL)
                        if match_curly_braces:
                            json_str_to_parse = match_curly_braces.group(1)
                        else:
                             json_str_to_parse = raw_json_response # As a last resort, try to parse the whole thing

                    if json_str_to_parse:
                        try:
                            json_data = json.loads(json_str_to_parse)
                            formatted_json_str = json.dumps(json_data, indent=4)
                            st.session_state.generated_json_bytes = formatted_json_str.encode('utf-8')
                            st.success("✅ JSON data extracted successfully!")
                        except json.JSONDecodeError as e:
                            st.error(f"⚠️ Extracted content was not valid JSON: {e}. Response was:\n{raw_json_response[:500]}...")
                            st.session_state.generated_json_bytes = None # Clear if error
                    else:
                        st.error("⚠️ Could not extract a JSON structure from model response.")
                        st.session_state.generated_json_bytes = None
                else:
                    st.error("❌ Failed to get a response from the model for JSON extraction.")
                    st.session_state.generated_json_bytes = None

            except Exception as e:
                st.error(f"❌ Failed to generate JSON: {e}")
        elif not client:
            st.error("❌ LLM Client not initialized. Cannot generate JSON.")
        else:
            st.warning("📌 Please upload an image or PDF first to generate JSON.")


    # Add section divider
    st.markdown('<div class="sidebar-section-divider"></div>', unsafe_allow_html=True)

    # Download Section
    with st.expander("📂 Download Files", expanded=True):
        if st.session_state.get("generated_pdf_bytes"):
            st.download_button(
                label="📥 Download Invoice Summary PDF",
                data=st.session_state.generated_pdf_bytes,
                file_name=f"{st.session_state.get('image_filename', 'invoice_summary').split('.')[0]}_summary.pdf",
                mime="application/pdf",
                key="download-pdf-btn-sidebar"
            )
        else:
            st.caption("Generate a PDF summary first to enable download.")

        if st.session_state.get("generated_json_bytes"):
            st.download_button(
                label="📥 Download Extracted JSON",
                data=st.session_state.generated_json_bytes,
                file_name=f"{st.session_state.get('image_filename', 'invoice_data').split('.')[0]}_data.json",
                mime="application/json",
                key="download-json-btn-sidebar"
            )
        else:
            st.caption("Generate a JSON file first to enable download.")


    # Add section divider
    st.markdown('<div class="sidebar-section-divider"></div>', unsafe_allow_html=True)

    # Chat Management Section
    with st.expander("⚙️ Chat Management"):
        if st.button("🔄 Reset Chat & Data", key="reset-chat-btn"):
            st.session_state.messages = []
            st.session_state.uploaded_image_bytes = None
            st.session_state.uploaded_image_type = None
            st.session_state.image_filename = None
            st.session_state.pdf_images = []
            st.session_state.generated_pdf_bytes = None
            st.session_state.generated_json_bytes = None
            st.success("🔄 Chat and all uploaded data have been reset!")
            time.sleep(1) # Brief pause before rerun
            st.rerun()

# ------------------------------------------- Chat History Display ------------------------------------------- #
for message in st.session_state.messages:
    avatar_icon = "👤" # User
    if message["role"] == "assistant":
        avatar_icon = "🤖" # Assistant
    
    # Handle complex content (list of dicts for image+text) vs simple string content
    if isinstance(message["content"], list):
        # Display only the text part for history if image was included
        text_content = ""
        for item in message["content"]:
            if isinstance(item, dict) and item.get("type") == "text":
                text_content += item["text"] + " "
        if text_content:
             with st.chat_message(message["role"], avatar=avatar_icon):
                st.markdown(text_content.strip())
        # Image is not re-displayed in history here to avoid clutter,
        # as the main image is already shown above or was part of the initial prompt.
    elif isinstance(message["content"], str): # Standard string content
        with st.chat_message(message["role"], avatar=avatar_icon):
            st.markdown(message["content"])


# ------------------------------------------------ Chat Input ------------------------------------------------ #
prompt = st.chat_input("💬 Ask a question about the uploaded document...")

if prompt:
    if not hf_api_key or not client:
        st.warning("⚠️ Please ensure your API key is set and the assistant is online (check sidebar).")
        st.stop()
    
    if st.session_state.get("uploaded_image_bytes") is None and not any(msg.get("role") == "user" and isinstance(msg.get("content"), list) and any(c.get("type") == "image_url" for c in msg.get("content")) for msg in st.session_state.messages):
        st.warning("📌 Please upload an image or PDF first before asking questions.")
        st.stop()

    # Add user message to chat history
    user_message_payload = {"role": "user", "content": prompt}
    
    # Check if this is the first user message AFTER an image upload
    # If so, and no image is in history, attach the current image.
    # This handles cases where user uploads, then immediately chats.
    is_first_message_after_upload = True 
    if not st.session_state.messages: # No messages yet
        is_first_message_after_upload = True
    else: # Check if last message was an assistant response (meaning user is replying)
        is_first_message_after_upload = st.session_state.messages[-1]["role"] == "assistant"

    # If it's the first user prompt in a sequence or no image context in messages, add image
    # Also, ensure image bytes are available
    if st.session_state.uploaded_image_bytes and (is_first_message_after_upload or not any(isinstance(m.get("content"), list) and any(c.get("type")=="image_url" for c in m.get("content")) for m in st.session_state.messages if m["role"]=="user")):
        base64_data = base64.b64encode(st.session_state.uploaded_image_bytes).decode('utf-8')
        data_url = f"data:{st.session_state.uploaded_image_type};base64,{base64_data}"
        user_message_payload["content"] = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": data_url}}
        ]
    
    st.session_state.messages.append(user_message_payload)

    # Display user message in chat message container
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Prepare messages for the API call (can be just the last few for context, or all)
    # For vision models, usually the image is sent with the current user prompt.
    api_messages = []
    # System prompt (optional, can be tuned)
    # api_messages.append({"role": "system", "content": "You are a helpful assistant analyzing documents."})
    
    # Add relevant history. For vision, the image is typically part of the *last* user message.
    # Let's send the last few messages for context, ensuring the image is with the latest user prompt.
    
    # Construct messages for API:
    # The API expects the image in the 'content' list of the user message.
    # We've already formatted user_message_payload correctly if an image needs to be sent.
    
    # Simple approach: send all history, model should handle context.
    # More complex: send only relevant history + current prompt with image.
    # For now, let's send a limited history to keep payload smaller.
    
    messages_for_api_call = []
    # If the last message (current user prompt) contains an image, use that.
    if isinstance(user_message_payload["content"], list):
         messages_for_api_call.append(user_message_payload)
    else: # If no image in current prompt, check previous user messages for image context (less ideal for some models)
        # Or just send text prompt if image was processed via sidebar buttons
         messages_for_api_call.append({"role": "user", "content": prompt})


    # Add some previous assistant responses and user messages for conversational context if they exist
    # This part can be refined to manage context length better
    relevant_history = st.session_state.messages[:-1] # All but the current message
    for msg in reversed(relevant_history[-4:]): # Last 4 messages for context
        if isinstance(msg["content"], str): # only include text history for context
             messages_for_api_call.insert(0, {"role": msg["role"], "content": msg["content"]})


    try:
        with st.spinner("🤔 Thinking..."):
            completion = client.chat.completions.create(
                model=modelToLoad,
                messages=messages_for_api_call, # Send the constructed list
                max_tokens=1500, # Allow for more detailed responses
                temperature=0.5, # Balanced temperature
            )
            assistant_response = completion.choices[0].message.content

        st.session_state.messages.append({"role": "assistant", "content": assistant_response})
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(assistant_response)

    except Exception as e:
        st.error(f"⚠️ An error occurred while communicating with the model: {e}")
        # Optionally remove the last user message if the API call failed, to allow retry
        # if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        # st.session_state.messages.pop()
        # st.rerun() # Consider if rerun is always desired on error

elif not st.session_state.get("uploaded_image_bytes") and not st.session_state.messages:
    st.info("👋 Welcome to Finsum AI Invoice Processor! Upload a document to get started or ask questions about your invoice.")

