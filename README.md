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

| Tool | Description |
|------|-------------|
| [Streamlit](https://streamlit.io) | Web UI framework |
| [Hugging Face Hub](https://huggingface.co/inference-endpoints) | API for multimodal LLM |
| [pdf2image](https://pypi.org/project/pdf2image/) | Convert PDF pages to images |
| [python-docx](https://python-docx.readthedocs.io/) | Edit DOCX templates |
| [docx2pdf](https://pypi.org/project/docx2pdf/) | Convert DOCX to PDF |
| [OpenAI LLM-compatible API](https://huggingface.co/meta-llama) | Meta’s LLaMA 3.2 11B Vision-Instruct |
| [pythoncom + win32com](https://pypi.org/project/pywin32/) | COM automation for Windows (used for Office conversion) |

- More of the imported/installed libraries can be found in the AI_Model_V2_Documentation.txt file
---

## 🖼️ Supported File Types

- `.jpg`, `.jpeg`, `.png` (image-based invoices)
- `.pdf` (multi-page supported)

---

##  👤👤 Creators

### Team Supervisor
- [ Mazhar mohsin](https://github.com/mazarbaloch)

### Team Leader 
- [Teemu Tupola](https://github.com/Tupolaa)

### Coding

- [Teemu Tupola](https://github.com/Tupolaa)
- [Hongqian Li](https://github.com/hongqian-li)
- [Fernando Barreto Rodrigues](https://github.com/FE7R7)


### Marketing/Desing

- Adriana Pereira Bastos
- Anabela Oliveira Araújo
- Aleksander Sarnatskiy

---

## Licence

- This project is licensed under the MIT License. Feel free to use, modify, and distribute.

## 🙋 Contact
Developed by a students in the BIP Smart Everything program.
For feedback, improvements or collaborations, please reach out via GitHub.