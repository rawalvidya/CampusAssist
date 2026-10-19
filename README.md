# 🎓 CampusAssist — Smart Student Support Assistant

CampusAssist is a student-support chatbot built with Python and Streamlit. It combines a local FAQ knowledge base with locally running AI to help students find information and receive assistance with general educational questions.

## ✨ Features

- 📚 **FAQ-Based Answers:** Retrieves answers from a predefined student-support knowledge base.
- 🤖 **Local AI Integration:** Uses Qwen3 through Ollama to answer suitable general questions when the FAQ system cannot find a match.
- 💬 **Interactive Chat Interface:** Ask questions and receive responses through a user-friendly interface.
- ⚡ **Suggested Questions:** Start conversations quickly using clickable question suggestions.
- 🌙 **Dark Mode:** Switch the interface theme.
- 🕘 **Conversation History:** Review questions and answers during your session.
- 📋 **Copy Answers:** Copy responses for notes and revision.
- 👍 **Answer Feedback:** Mark responses as helpful or not helpful.
- 📥 **Chat Export:** Export conversations for later reference.
- 🔒 **Responsible Responses:** Avoids claiming access to private student records or inventing unverified college policies.

## 🛠️ Technologies Used

- Python
- Streamlit
- Ollama
- Qwen3 local language model
- JSON-based FAQ knowledge base

## ⚙️ How It Works

1. A student submits a question through the chat interface.
2. CampusAssist searches its FAQ knowledge base for a relevant answer.
3. If no suitable FAQ match is found, it can use Qwen3 through Ollama for appropriate general questions.
4. If Ollama is unavailable, the application should fall back to a clarification response rather than crash.

## 🚀 Getting Started

### Prerequisites

- Python installed on your computer
- pip, Python's package installer
- Ollama and the Qwen3 model for AI-generated responses

### 1. Download the Project

Clone your GitHub repository:

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd CampusAssist
```

Replace `YOUR_GITHUB_REPOSITORY_URL` with your actual repository URL.

Alternatively, download the project as a ZIP file and extract it.

### 2. Create a Virtual Environment

```powershell
py -m venv .venv
```

Activate it in Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

If a `requirements.txt` file is included, run:

```powershell
py -m pip install -r requirements.txt
```

### 4. Set Up the Local AI Model

Install Ollama from its official website:

https://ollama.com/

Download the model:

```powershell
ollama pull qwen3:4b
```

Ensure Ollama is running before using AI-generated responses.

### 5. Run CampusAssist

From the project folder, run:

```powershell
py -m streamlit run app_enhanced.py
```

Streamlit will display a local URL in the terminal. Open that URL in your browser to use CampusAssist.

## 📁 Project Structure

```text
CampusAssist/
├── app_enhanced.py       # Main Streamlit application
├── faq_engine.py         # FAQ matching and retrieval
├── faqs.json             # FAQ knowledge base
├── ollama_service.py     # Local AI integration
├── requirements.txt      # Python dependencies
└── README.md             # Project documentation
```

This is the intended structure; the actual repository should include the files required by the application.

## 🔒 Privacy and Limitations

- FAQ answers depend on the information available in the knowledge base.
- General AI-generated responses require Ollama and the configured model.
- AI-generated responses may occasionally be inaccurate.
- CampusAssist does not independently access private college databases or student records.
- For unverified college policies, deadlines, marks, or attendance records, students should consult official college sources.

## 🎯 Project Objective

CampusAssist aims to make student support more accessible by combining FAQ retrieval and local AI assistance in a simple, interactive web application.

## 👩‍💻 Project Status

Developed as a student project demonstrating FAQ-based chatbot development, local AI integration, and interactive web application design.
