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

# ------------------------------------------- Page Configuration ------------------------------------------- #
st.set_page_config(page_title="Multimodal Chatbot", layout="wide")

st.title("📝 Image + PDF Chatbot 🤖")

# ------------------------------------------ API Key Input (Sidebar) --------------------------------------- #
with st.sidebar:
    st.header("🔐 Configuration:")

    hf_api_key = st.text_input("Enter your API Access Token:", type="password")
    st.markdown("That grants access to Model:")
    st.markdown("`meta-llama/Llama-3.2-11B-Vision-Instruct`.")

    client = None
    if not hf_api_key:
        st.warning("⚠️ Please enter your API token to continue.")
        st.markdown("")
        st.markdown("")
        st.markdown("")
        st.header("💡 Actions:")
        st.markdown("")


    else:
        try:
            client = InferenceClient(provider="novita", token=hf_api_key)
            st.success("✅ Inference client initialized.")
            st.markdown("")
            st.markdown("")
            st.markdown("")
            st.header("💡 Actions:")
            st.markdown("")

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

# ------------------------------------------------ File Upload ------------------------------------------------ #
uploaded_file = st.file_uploader("Upload an image or PDF...", type=["png", "jpg", "jpeg", "pdf"])

if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    filename = uploaded_file.name
    mime_type = uploaded_file.type

    if mime_type == "application/pdf":
        try:
            images = convert_from_bytes(file_bytes)
            if images:
                image = images[0]
                image_bytes_io = io.BytesIO()
                image.save(image_bytes_io, format='JPEG')
                image_bytes = image_bytes_io.getvalue()
                mime_type = "image/jpeg"

                st.session_state.uploaded_image_bytes = image_bytes
                st.session_state.uploaded_image_type = mime_type
                st.session_state.image_filename = filename
                st.session_state.messages = []

                st.success(f"PDF '{filename}' uploaded and converted.")
                st.image(image, caption=f"{filename} (page 1)", use_container_width=True)
        except Exception as e:
            st.error(f"Failed to process PDF: {e}")
    else:
        image_bytes = file_bytes
        st.session_state.uploaded_image_bytes = image_bytes
        st.session_state.uploaded_image_type = mime_type
        st.session_state.image_filename = filename
        st.session_state.messages = []
        st.success(f"Image '{filename}' uploaded ({mime_type}).")
        st.image(image_bytes, caption=filename, use_container_width=True)

# ------------------------------------------- PDF Summary Generator ------------------------------------------- #
def generate_invoice_summary_pdf(summary_text):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(temp_file.name, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 80, "Invoice Summary")

    c.setFont("Helvetica", 12)
    y = height - 120
    for line in summary_text.split("\n"):
        c.drawString(100, y, line.strip())
        y -= 20

    c.save()
    return temp_file.name

# ----------------------------- Sidebar Button to Generate and Download PDF ----------------------------- #
with st.sidebar:
    if st.sidebar.button("⚙️ Generate Invoice Summary PDF", key="gen-pdf-btn"):
        try:
            # Ask the model to extract key fields
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
                    model="meta-llama/Llama-3.2-11B-Vision-Instruct",
                    messages=messages,
                    max_tokens=512,
                    temperature=0.3
                )
                extracted_text = completion.choices[0].message.content

            pdf_path = generate_invoice_summary_pdf(extracted_text)
            st.session_state.generated_pdf_path = pdf_path

        except Exception as e:
            st.error(f"Failed to extract and generate PDF: {e}")

    # Inject CSS for green button style
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
            st.markdown("")


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
                model="meta-llama/Llama-3.2-11B-Vision-Instruct",
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
    if "generated_pdf_path" in st.session_state:
        del st.session_state.generated_pdf_path
    st.rerun()
