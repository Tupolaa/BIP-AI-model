# 📝 MultiLingual Invoice Assistant 🤖

A smart Streamlit web application that leverages the power of **Meta LLaMA 3 Vision-Instruct** to extract structured data from invoices in image or PDF format. It supports intelligent field extraction, invoice summarization, and export to **PDF** and **JSON** formats.

- ⚙️ Built in [**BIP Smart Everything program**](https://run-eu.eu/2025/03/01/bip-smart-everything-connecting-artificial-intelligence-tools-with-business-ideas/)


---

## 🚀 Features

- 📤 Upload **PDF** or **Image (JPG/PNG)** invoices
- 🔍 Automatically extract:
  - **Service Provider**
  - **Customer Information**
  - **Service Description**
  - **Invoice Date**
  - **Invoice Total**
- 📄 Convert extracted summaries to **PDF**
- 🧾 Generate structured **JSON** output
- 💬 Ask natural language questions about uploaded documents
- 🧠 Powered by **LLaMA 3 Vision-Instruct** on **Hugging Face**


---

## 🧰 Tech Stack

| Tool / Library | Description |
|----------------|-------------|
| [Streamlit](https://streamlit.io) | Web UI framework for building interactive apps |
| [Hugging Face Inference Endpoints](https://huggingface.co/inference-endpoints) | Run multimodal LLMs (e.g., LLaMA 3) via API |
| [pdf2image](https://pypi.org/project/pdf2image/) | Convert PDF pages to high-resolution images |
| [PyPDF2](https://pypi.org/project/PyPDF2/) | Read, split, and merge PDF files |
| [Pillow (PIL)](https://python-pillow.org/) | Image processing library for Python |
| [ReportLab](https://www.reportlab.com/opensource/) | Create PDF documents with custom layout |
| [python-docx](https://python-docx.readthedocs.io/) | Create and edit Word (.docx) documents |
| [docx2pdf](https://pypi.org/project/docx2pdf/) | Convert Word documents (.docx) to PDF |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | Manage environment variables using `.env` files |
| [Meta LLaMA 3.2 Vision-Instruct](https://huggingface.co/meta-llama) | Multimodal LLM for document and image understanding |

- More of the imported/installed libraries can be found in the AI_Model_V2_Documentation.txt file
---

## 🖼️ Supported File Types

- `.jpg`, `.jpeg`, `.png` (image-based invoices)
- `.pdf` (multi-page supported)

---

##  👤👤 Creators

### 🧑‍💼 Team Supervisor
- [ Mazhar mohsin](https://github.com/mazarbaloch)

### 🧠 Team Leader 
- [Teemu Tupola](https://github.com/Tupolaa)

### 💻 Coding

- [Teemu Tupola](https://github.com/Tupolaa)
- [Hongqian Li](https://github.com/hongqian-li)
- [Fernando Barreto Rodrigues](https://github.com/FE7R7)


### 💵 Marketing/Design

- Adriana Pereira Bastos
- Anabela Oliveira Araújo
- Aleksander Sarnatskiy

---

## 📝 Licence

- This project is licensed under the MIT License. Feel free to use, modify, and distribute.

## 🙋 Contact
Developed by a students in the BIP Smart Everything program.
For feedback, improvements or collaborations, please reach out via GitHub.

## Project Structure

- `/frontend_astro` – Contains the Astro-based frontend for the websites.
- `/backend_model` – Contains different versions of the prototype that handles the document invoice parsing (AI_Model_V3.py is the latest version)
- `/general_files` – More detailed documents about the program and installations/libraries used.