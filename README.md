# 📝 NoteCraft AI Studio — SMUCT Academic & Engineering Suite

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://python.org)
[![KaTeX](https://img.shields.io/badge/Math-KaTeX_v0.16.8-00d1b2.svg?style=flat)](https://katex.org)
[![Tailwind CSS](https://img.shields.io/badge/Frontend-TailwindCSS-38B2AC.svg?style=flat&logo=tailwind-css)](https://tailwindcss.com)
[![Google Gemini](https://img.shields.io/badge/AI-Gemini_Flash_Vision-4285F4.svg?style=flat&logo=google)](https://ai.google.dev)
[![University](https://img.shields.io/badge/SMUCT-CSE_%26_CSIT-8A2BE2.svg?style=flat)](https://smuct.ac.bd)

> **NoteCraft AI Studio** is an all-in-one academic document synthesizer, study guide architect, and interactive computer science lab simulator engineered specifically for university students and educators at **Shanto-Mariam University of Creative Technology (SMUCT)**.

---

## 👨‍💻 Creator & Engineering Credits

* **Lead Architect & Developer:** **Abdul Awal Ibn Rafi** ([@0xrafiKaji](https://github.com/0xrafiKaji))
* **Student ID:** `261071044`
* **Department:** Department of Computer Science & Engineering (CSE & CSIT)
* **Faculty:** Faculty of Engineering and Technology
* **Institution:** Shanto-Mariam University of Creative Technology (SMUCT)

---

## 🚀 Key Features & Capabilities

### 1. 📑 8 Professional Academic & Engineering Templates
NoteCraft transforms raw inputs into publication-ready academic formats adhering strictly to SMUCT university standards:

1. **Standard Class Note:** Deep bilingual intuitions (Bangla + English), core syntax conventions, pseudo-code analysis, and common misconception traps.
2. **Executive Cheat Sheet:** Ultra-dense reference cards optimized for last-minute revision.
3. **Formula & Intuition Sheet:** Pure mathematical derivations with step-by-step logic.
4. **Deep Architecture & Flow:** System engineering breakdowns, memory diagrams, and runtime complexity tables.
5. **Class Test (CT / Quiz) Blueprint:** 2-mark definitions, 5-mark broad workouts, and mark-distribution rubrics.
6. **Mid & Final Exam Master Guide:** Full semester preparation blueprints, past question predictions, and high-yield topics.
7. **Official University Assignment Paper:**
   - Formal SMUCT cover page (Course Code, Title, Student ID, Submission Date, Department of CSE & CSIT).
   - Table of contents & theoretical foundation.
   - Step-by-step mathematical derivations.
   - Solved numerical workouts & real-world engineering case studies.
   - Academic citation references.
8. **Official University Lab Report:**
   - Formal SMUCT Laboratory Experiment cover page with **Teacher Signature** evaluation section.
   - Objectives & Experimental Theory with KaTeX formulas (including $\%$ Error calculation).
   - Apparatus & Equipment specification table.
   - Third-person past-tense step-by-step experimental procedures.
   - Observation & Experimental Data tables (Theoretical vs Measured vs Percentage Error).
   - Discussion, precautions, and engineering takeaways.

---

### 2. ⚡ Dual Input Modality (Prompt Only or Prompt + Photo)
- **Prompt Only:** Type your assignment topic, lab experiment title, or lecture notes directly (e.g. *"Verification of Ohm's Law in Series Circuits"* or *"Adjusting Entries and Break-Even Analysis"*).
- **Prompt + Photo / Draft Copy:** Upload photos of breadboard setups, circuit diagrams, lecture whiteboards, or handwritten drafts alongside custom prompt instructions. The multi-modal Gemini Vision pipeline extracts, transcribes, and synthesizes them into structured documents.

---

### 3. 📐 KaTeX Mathematical Rendering (Zero Math Breakage)
- Embedded local offline **KaTeX v0.16.8** engine (`auto-render`, fonts, and styles) ensures that mathematical formulas never break, distort, or render as unreadable glyphs.
- Supports inline math (`$Q_{BE} = \frac{FC}{P - VC}$`) and full-width block equations (`$$\% \text{Error} = \left| \frac{V_{th} - V_{exp}}{V_{th}} \right| \times 100\%$$`).
- Perfect KaTeX math rendering in web preview, print dialogs, and exported vector PDFs.

---

### 4. 🔬 Interactive Dry Run Lab
- Dynamic step-by-step computer science execution simulator (Linear Array, Stack, Queue, Circular Queue, Memory Pointers).
- Visual state inspection with active cell highlights, before/after status conditions, and time complexity badges.
- Fully responsive, overflow-free layout tested across desktop, tablet, and mobile screens.

---

### 5. 🗓️ Live SMUCT Routine & Faculty Hub
- Live synchronization with Google Sheets for CSE & CSIT class routines.
- Real-time room numbers, course teacher information, and direct email contacts.
- Quick filtering by day of the week and section.

---

## 🛠️ Architecture & Tech Stack

```
smuct_notecraft_ai_studio/
├── backend/
│   ├── main.py          # FastAPI server, Gemini Vision pipeline & multi-page synthesizer
│   └── sheet_sync.py    # SMUCT Class Routine & Faculty Google Sheet crawler
├── frontend/
│   ├── index.html       # Single-page studio interface with Tailwind CSS & KaTeX
│   ├── manifest.json    # PWA web manifest
│   └── vendor/
│       └── katex/       # Local offline KaTeX styles, JS auto-renderer, and math fonts
├── run.sh               # One-click startup script with port detection
├── requirements.txt     # Python production dependencies
├── .env.example         # Template for environment variables
└── README.md            # Project documentation
```

---

## 💻 Quick Start & Installation

### Prerequisites
- Python 3.10 or higher installed on your computer ([Download Python](https://www.python.org/downloads/))
- Google Gemini API Key (Get a free key from [Google AI Studio](https://aistudio.google.com/app/apikey))

---

### 1. Clone or Download the Repository
```bash
git clone https://github.com/0xrafiKaji/smuct-notecraft-ai-studio.git
cd smuct-notecraft-ai-studio
```
*(Or click **Code ➔ Download ZIP** on GitHub and extract it).*

---

### 2. Configure Environment (Optional)
```bash
cp .env.example .env
```
Open `.env` and paste your Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
PORT=8000
ADMIN_PASSWORD=rafik2026
```
> **Note:** If you don't edit `.env`, you can also enter your Gemini API Key directly inside the web browser UI when prompted!

---

### 3. Run the Studio (One-Click)

#### 🪟 On Windows:
Simply double-click **`run.bat`** (or open Command Prompt / PowerShell in the folder and run `run.bat`).
It will automatically create the virtual environment, install requirements, and open the app in your default browser at `http://localhost:8000`.

#### 🐧 On Linux / macOS:
```bash
chmod +x run.sh
./run.sh
```

---

### ☁️ Free 1-Click Cloud Deployment (Render / Railway)

You can also host this for free on [Render](https://render.com):
1. Create a new **Web Service** on Render and connect this repository.
2. Configure settings:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
3. Add Environment Variable:
   - `GEMINI_API_KEY` = *your_gemini_api_key*
4. Click **Deploy Web Service**!

---

## 📄 License & Attribution

Developed with passion by **Abdul Awal Ibn Rafi** (`@0xrafiKaji`), Department of CSE & CSIT, **Shanto-Mariam University of Creative Technology**.

Distributed under the **MIT License**. See `LICENSE` for more information.
