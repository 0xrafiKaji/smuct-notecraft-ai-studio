import os
import re
import json
import base64
import time
import urllib.request
from typing import Optional, List
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from backend.sheet_sync import sync_all_sheets, SHEET_ID, update_sheet_id, _update_env_var

load_dotenv()

app = FastAPI(title="NoteCraft AI Studio — SMUCT Production Suite", version="5.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def check_admin_auth(password: Optional[str]) -> bool:
    """Verifies that provided passcode matches the configured ADMIN_PASSWORD."""
    expected = os.getenv("ADMIN_PASSWORD", "rafik2026").strip()
    return bool(password and password.strip() == expected)

def get_api_key() -> str:
    raw = os.getenv("GEMINI_API_KEY", "").strip()
    aq_m = re.search(r"AQ\.[0-9A-Za-z_\-\.]{25,90}", raw)
    aiza_m = re.search(r"AIza[0-9A-Za-z_\-]{30,45}", raw)
    key = aq_m.group(0) if aq_m else (aiza_m.group(0) if aiza_m else raw)
    return key

# Resilient model priority list (avoiding deprecated 404 models)
MODEL_CANDIDATES = [
    "gemini-flash-lite-latest",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-pro-latest"
]

@app.get("/api/health")
def health_check():
    key = get_api_key()
    has_key = bool(key and len(key) > 20)
    from backend.sheet_sync import SHEET_ID as CURRENT_SHEET_ID
    return {
        "status": "ok",
        "service": "NoteCraft AI Studio Backend",
        "version": "5.0.0",
        "creator": "Abdul Awal Ibn Rafi",
        "has_gemini_key": has_key,
        "sheet_id": CURRENT_SHEET_ID
    }

@app.post("/api/admin/verify")
def admin_verify(password: str = Form(...)):
    if not check_admin_auth(password):
        raise HTTPException(status_code=401, detail="Invalid Admin passcode. Access restricted to creator Abdul Awal Ibn Rafi.")
    from backend.sheet_sync import SHEET_ID as CURRENT_SHEET_ID
    return {
        "status": "ok",
        "authenticated": True,
        "creator": "Abdul Awal Ibn Rafi",
        "sheet_id": CURRENT_SHEET_ID
    }

@app.post("/api/admin/set-sheet")
def admin_set_sheet(sheet_id_or_url: str = Form(...), password: str = Form(...)):
    if not check_admin_auth(password):
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid Admin passcode.")
    try:
        clean_id = update_sheet_id(sheet_id_or_url)
        fresh_data = sync_all_sheets(force_refresh=True)
        return {
            "status": "ok",
            "sheet_id": clean_id,
            "message": f"Successfully connected to Google Sheet ({clean_id}) and refreshed all curriculum records.",
            "counts": fresh_data.get("counts", {})
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update Google Sheet: {str(e)}")

@app.post("/api/admin/update-config")
def admin_update_config(
    password: str = Form(...),
    gemini_key: Optional[str] = Form(None),
    new_admin_password: Optional[str] = Form(None),
    sheet_id: Optional[str] = Form(None)
):
    if not check_admin_auth(password):
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid Admin passcode.")
    if gemini_key and len(gemini_key.strip()) > 10:
        os.environ["GEMINI_API_KEY"] = gemini_key.strip()
        _update_env_var("GEMINI_API_KEY", gemini_key.strip())
    if new_admin_password and len(new_admin_password.strip()) >= 4:
        os.environ["ADMIN_PASSWORD"] = new_admin_password.strip()
        _update_env_var("ADMIN_PASSWORD", new_admin_password.strip())
    if sheet_id and len(sheet_id.strip()) > 10:
        update_sheet_id(sheet_id.strip())
    return {"status": "ok", "message": "Admin configuration successfully updated."}

@app.get("/api/sheet-data")
def get_sheet_data(force: bool = Query(False)):
    try:
        data = sync_all_sheets(force_refresh=force)
        return data
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Google Sheet fetch failed: {str(e)}")

@app.post("/api/sync-sheet")
def post_sync_sheet():
    try:
        data = sync_all_sheets(force_refresh=True)
        return data
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Google Sheet sync failed: {str(e)}")

def call_gemini_rest(contents: list, api_key: str) -> dict:
    last_err = "No models attempted"
    body = {
        "contents": contents,
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.2
        }
    }
    encoded_body = json.dumps(body).encode("utf-8")

    for model_name in MODEL_CANDIDATES:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        try:
            req = urllib.request.Request(
                url,
                data=encoded_body,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=35) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                text = res_data["candidates"][0]["content"]["parts"][0]["text"]
                # Clean up any potential markdown code fence wrapping
                cleaned = text.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                parsed = json.loads(cleaned.strip())
                return {"model": model_name, "note": parsed}
        except Exception as e:
            err_str = str(e)
            if hasattr(e, "read"):
                try:
                    err_str += " " + e.read().decode("utf-8")[:200]
                except Exception:
                    pass
            last_err = f"[{model_name}] {err_str}"
            time.sleep(0.3)

    raise HTTPException(status_code=502, detail=f"Gemini generation error: {last_err}")

@app.post("/api/convert-notes")
async def convert_notes(
    images: Optional[List[UploadFile]] = File(None),
    image: Optional[UploadFile] = File(None),
    prompt_text: Optional[str] = Form(None),
    course_code: str = Form("CSE 1201"),
    course_title: str = Form("Data Structure"),
    style: str = Form("normal_class_note"),
    hint: str = Form(""),
    exam_mode: Optional[str] = Form(None),
    exam_total_marks: Optional[str] = Form(None),
    exam_duration: Optional[str] = Form(None),
    exam_question_marks: Optional[str] = Form(None),
    exam_focus_topics: Optional[str] = Form(None),
    exam_difficulty: Optional[str] = Form(None),
    exam_question_types: Optional[str] = Form(None)
):
    key = get_api_key()
    if not key:
        raise HTTPException(status_code=500, detail="Gemini API key is not configured.")

    parts = []
    # Collect all uploaded images (supports up to 10 photos)
    uploaded_files = []
    if images:
        uploaded_files.extend(images)
    if image:
        uploaded_files.append(image)

    for idx, f in enumerate(uploaded_files[:10]):
        if f and f.filename:
            img_bytes = await f.read()
            if img_bytes and len(img_bytes) > 0:
                b64 = base64.b64encode(img_bytes).decode("utf-8")
                parts.append({
                    "inline_data": {
                        "mime_type": f.content_type or "image/jpeg",
                        "data": b64
                    }
                })

    topic_instruction = ""
    if prompt_text and prompt_text.strip():
        topic_instruction = f"\nTopic / Lecture notes to process:\n\"\"\"{prompt_text.strip()}\"\"\"\n"

    # Compile custom blueprints based on selected style
    exam_blueprint = ""
    is_exam_style = style in ["ct_exam_style", "master_docx"] or bool(exam_mode or exam_total_marks)
    if is_exam_style:
        e_type = exam_mode or ("Class Test (CT / Quiz)" if style == "ct_exam_style" else "Mid / Final Semester Examination")
        tot_m = exam_total_marks or ("20 Marks" if style == "ct_exam_style" else "40-60 Marks")
        dur = exam_duration or ("30 Minutes" if style == "ct_exam_style" else "1.5 - 2 Hours")
        q_marks = exam_question_marks or "2-mark short questions (Part A) & 5-mark broad workouts (Part B)"
        focus_spec = f"• Focused Topics: {exam_focus_topics}\n" if exam_focus_topics else ""
        diff_spec = f"• Exam Difficulty: {exam_difficulty}\n" if exam_difficulty else ""
        qtypes_spec = f"• Expected Question Types: {exam_question_types}\n" if exam_question_types else ""

        exam_blueprint = f"""
=== SMUCT OFFICIAL EXAMINATION SPECIFICATION ===
Exam Format: {e_type}
Total Marks: {tot_m}
Duration / Time Limit: {dur}
Marks Distribution Pattern: {q_marks}
{focus_spec}{diff_spec}{qtypes_spec}
Instructions:
1. In 'conventions', provide probable Short Answer & Formula questions labeled clearly with their marks (e.g. '[2 Marks] Definition/Concept').
2. In 'isolated_logic', provide complete Broad Model Questions and Step-by-Step Solutions with marked rubrics.
3. In 'traps', highlight specific exam traps, negative marking risks, and time management hacks for a {dur} exam.
=================================================
"""

    assignment_blueprint = ""
    if style == "assignment_paper":
        assignment_blueprint = f"""
=== SMUCT OFFICIAL ASSIGNMENT PAPER SPECIFICATION ===
University: Shanto-Mariam University of Creative Technology (SMUCT)
Faculty: Faculty of Engineering and Technology — Department of CSE & CSIT
Course: {course_code} - {course_title}
Assignment Format: Official University Academic Assignment Paper
Total Marks: {exam_total_marks or "10-20 Marks"}
Instructions:
1. In 'title', provide the formal assignment title (e.g. 'Adjusting Entries & Break-Even Analysis' or the user's assignment topic).
2. In 'subtitle', state 'Department of CSE & CSIT • Shanto-Mariam University of Creative Technology'.
3. In 'intuition_en' (and intuition_bn), provide Section 1: Executive Summary, Problem Definition & Theoretical Foundations with real-world motivation.
4. In 'conventions', provide the Table of Contents & Key Theoretical Definitions as a list of [Section / Concept, Theoretical Framework / Formula, Detailed Scope / Description].
5. In 'pseudo_minus1', provide 'Part A: Comprehensive Theoretical Breakdown & Analytical Formulations' with rigorous KaTeX equations.
6. In 'pseudo_zero', provide 'Part B: Step-by-Step Mathematical Derivations & Analytical Framework'.
7. In 'isolated_logic', provide 'Part C: Step-by-Step Solved Problem Sets & Numerical Workouts' as [Problem Statement / Case Study, Analytical Workout / Step-by-Step Solution, Final Calculated Answer / Result].
8. In 'full_code_minus1', provide 'Part D: Real-Life Engineering Applications & Practical Case Studies'.
9. In 'traps', highlight Key Analytical Insights, Limitations & Common Academic Misconceptions.
=====================================================
"""

    lab_report_blueprint = ""
    if style == "lab_report":
        lab_report_blueprint = f"""
=== SMUCT OFFICIAL LAB REPORT SPECIFICATION ===
University: SHANTO-MARIAM UNIVERSITY OF CREATIVE TECHNOLOGY
Campus: Plot 06, Road 06, Sector 17, Uttara, Dhaka-1230
Faculty: Faculty of Engineering and Technology
Departments: Departments of CSE and CSIT
Format: Official Laboratory Experiment Sessional Report
Course: {course_code} - {course_title}
Instructions:
1. In 'title', state the Experiment Title (e.g. 'Verification of Series and Parallel Circuit').
2. In 'subtitle', state 'Experiment No: 02 • Faculty of Engineering and Technology'.
3. In 'intuition_en' (and intuition_bn), provide Section 1: Objectives as a clear, enumerated list of specific laboratory goals.
4. In 'pseudo_minus1', provide Section 2: Theory & Governing Equations (Ohm's law, series-parallel resistance formulas, KCL/KVL, and the standard percentage error formula: % Error = |(Theoretical - Practical) / Theoretical| * 100) typeset in clean KaTeX.
5. In 'conventions', provide Section 3: Apparatus / Equipment Required as [Name of Apparatus, Specification / Model / Rating, Quantity / Function].
6. In 'pseudo_zero', provide Section 4: Experimental Procedure written cleanly in PAST TENSE (e.g. '1. First, we measured the resistances...', '2. We connected the resistors...', '3. We recorded the voltage and current readings...').
7. In 'isolated_logic', provide Section 5: Experimental Observation & Data Tables and Section 6: Sample Calculations as [Table Name / Parameter, Theoretical vs Practical Data & Steps, % Error & Verification Result].
8. In 'full_code_minus1', provide Section 7: Results & In-Depth Discussion analyzing practical vs theoretical findings.
9. In 'traps', provide Section 8: Sources of Experimental Error & Precautions (breadboard contact resistance, meter internal resistance, parallax error, wiring precautions).
===============================================
"""

    multi_page_instruction = ""
    if len(parts) > 1:
        multi_page_instruction = f"\nNotice: The user has uploaded {len(parts)} sequential pages of handwritten notes / exam questions / lab handouts / circuit photos. Synthesize all pages sequentially into a unified, coherent and comprehensive study guide.\n"

    system_prompt = f"""You are NoteCraft Academic Engine for Shanto-Mariam University of Creative Technology (SMUCT).
Course: {course_code} - {course_title} (Style: {style}).
Creator Credit: Abdul Awal Ibn Rafi (Lead Architect, SMUCT Production Suite).
{exam_blueprint}
{assignment_blueprint}
{lab_report_blueprint}
{multi_page_instruction}
{hint if hint else ""}
{topic_instruction}

CRITICAL MATHEMATICS & FORMULA MANDATE (KATEX TYPESETTING):
- ALWAYS typeset all equations, formulas, variables, derivatives, integrals, fractions, vectors, matrices, and physics laws using standard LaTeX enclosed in single dollar signs $...$ (for inline math) or double dollar signs $$...$$ (for display equations).
- Example: $a = \\frac{{v - u}}{{t}}$, $\\vec{{r}} = x\\hat{{i}} + y\\hat{{j}} + z\\hat{{k}}$, $\\nabla \\cdot \\vec{{r}} = 3$, $F = -kx$, $R_1 = \\frac{{R_B R_C}}{{R_A + R_B + R_C}}$.
- NEVER use unicode combining marks (do NOT write î, ĵ, k̂, r̄, or Ā). Always write \\hat{{i}}, \\hat{{j}}, \\hat{{k}}, \\vec{{r}}, \\vec{{A}}.
- NEVER write plain text fractions like (x^2+y^2)^(1/2) or (v-u)/t. Always use \\sqrt{{x^2+y^2}} and \\frac{{v-u}}{{t}}.
- This ensures KaTeX renders clean, unbreakable mathematics in PDF and Word exports.

Carefully read the provided note image(s) or topic details and return ONLY a valid JSON object with these exact keys:
{{
  "title": "Main topic or exam title",
  "subtitle": "Comprehensive scope summary",
  "course": "{course_code} - {course_title}",
  "exam_meta": "{tot_m if is_exam_style else ''} {dur if is_exam_style else ''}".strip(),
  "intuition_bn": "Detailed Bengali explanation with a real-life analogy (The 'Aha!' Intuition)",
  "intuition_en": "Detailed English explanation",
  "conventions": [["Key Concept / Question 1", "Primary Formula / Rule / Step 1", "Result / Explanation"]],
  "pseudo_minus1": "Step-by-step algorithm, derivation, or workout Part 1",
  "pseudo_zero": "Alternative step-by-step workout Part 2",
  "isolated_logic": [["Example / Problem 1", "Detailed step-by-step solution", "Final Answer / Output"]],
  "full_code_minus1": "Complete compilable code or mathematical workout",
  "full_code_zero": "",
  "sim_steps_minus1": [
    {{
      "step": 1,
      "title": "Initial State",
      "cells": ["10", "20", "30"],
      "active": 0,
      "stale": [],
      "top": 0,
      "front": null,
      "rear": null,
      "outside": false,
      "before": "Initial pointers",
      "check": "Valid boundaries",
      "action": "Element inspected",
      "after": "Pointers updated",
      "status": "OK",
      "err": false
    }}
  ],
  "traps": ["Important exam trap 1", "Important exam trap 2"]
}}"""

    parts.append({"text": system_prompt})
    result = call_gemini_rest(contents=[{"parts": parts}], api_key=key)
    note_payload = result["note"]
    note_payload["_creator"] = "Abdul Awal Ibn Rafi"
    note_payload["_suite"] = "NoteCraft AI Studio"
    return {"status": "ok", "model": result["model"], "note": note_payload}

# Serve frontend static assets and index.html
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.api_route("/", methods=["GET", "HEAD"])
    def serve_index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))

    @app.get("/manifest.json")
    def serve_manifest():
        return FileResponse(os.path.join(frontend_dir, "manifest.json"), media_type="application/manifest+json")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
