import os
import csv
import io
import re
import json
import time
import urllib.request
from typing import Dict, Any, List

SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "1Dg4poYmMlhm6WDUl0XYwhgSR33BDsi7DjGCQOLqz0R0")

# Tab GID mapping
SHEET_GIDS = {
    "routine": "1459761998",
    "faculty": "1822914331",
    "advisors": "812632386",
    "crs": "1985387739",
    "rooms": "2130384851",
    "courses": "909736649",
    "equiv": "1750138643"
}

_CACHE: Dict[str, Any] = {
    "timestamp": 0,
    "data": None
}
CACHE_TTL = 300  # 5 minutes in memory

def extract_sheet_id(raw_input: str) -> str:
    """Extract clean Google Sheet ID from raw ID or full Google Sheet URL."""
    raw = (raw_input or "").strip()
    match = re.search(r"/d/([a-zA-Z0-9-_]{20,})", raw)
    if match:
        return match.group(1)
    match_direct = re.search(r"^[a-zA-Z0-9-_]{20,}$", raw)
    if match_direct:
        return match_direct.group(0)
    # Fallback to any 25+ token
    match_fallback = re.search(r"[a-zA-Z0-9-_]{25,}", raw)
    return match_fallback.group(0) if match_fallback else raw

def _update_env_var(key: str, val: str):
    try:
        env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
        lines = []
        found = False
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        new_lines = []
        for l in lines:
            if l.strip().startswith(f"{key}="):
                new_lines.append(f"{key}={val}\n")
                found = True
            else:
                new_lines.append(l)
        if not found:
            new_lines.append(f"{key}={val}\n")
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
    except Exception as e:
        print(f"Failed to persist {key} to .env: {e}")

def update_sheet_id(new_id_or_url: str) -> str:
    global SHEET_ID, _CACHE
    clean_id = extract_sheet_id(new_id_or_url)
    if not clean_id or len(clean_id) < 15:
        raise ValueError(f"Invalid Google Sheet ID or URL: '{new_id_or_url}'")
    SHEET_ID = clean_id
    _CACHE["timestamp"] = 0
    _CACHE["data"] = None
    _update_env_var("GOOGLE_SHEET_ID", clean_id)
    return clean_id

def fetch_sheet_csv(gid: str) -> List[List[str]]:
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        content = resp.read().decode("utf-8", errors="ignore")
        return list(csv.reader(io.StringIO(content)))

def parse_faculty(rows: List[List[str]]) -> List[Dict[str, Any]]:
    faculty_list = []
    header_idx = -1
    for i, r in enumerate(rows[:5]):
        if any("name" in c.lower() for c in r) and any("initial" in c.lower() for c in r):
            header_idx = i
            break
    start = header_idx + 1 if header_idx != -1 else 2
    for r in rows[start:]:
        if not any(cell.strip() for cell in r) or len(r) < 3:
            continue
        name = r[1].strip() if len(r) > 1 else ""
        init = r[2].strip() if len(r) > 2 else ""
        if not name or not init or name.lower() == "name":
            continue
        role = r[3].strip() if len(r) > 3 else ""
        phone = r[4].strip() if len(r) > 4 else ""
        if phone and not phone.startswith("0") and len(phone) == 10:
            phone = "0" + phone
        email = r[5].strip() if len(r) > 5 else ""
        weekend = r[6].strip() if len(r) > 6 else ""
        ho = r[7].strip() if len(r) > 7 else ""
        faculty_list.append({
            "sl": len(faculty_list) + 1,
            "name": name,
            "init": init,
            "role": role,
            "phone": phone,
            "email": email,
            "room": "1502" if "head" in role.lower() or "coordinator" in role.lower() else "1502 / 1803",
            "consult": f"Weekend: {weekend}" if weekend else "Available during office hours",
            "off": f"{weekend}, {ho} (HO)" if ho else weekend
        })
    return faculty_list

def parse_advisors(rows: List[List[str]]) -> List[Dict[str, Any]]:
    advisors = []
    last_batch = ""
    for r in rows[2:]:
        if not any(c.strip() for c in r):
            continue
        batch = r[0].strip() if len(r) > 0 and r[0].strip() else last_batch
        sem = r[1].strip() if len(r) > 1 else ""
        name = r[2].strip() if len(r) > 2 else ""
        init = r[3].strip() if len(r) > 3 else ""
        role = r[4].strip() if len(r) > 4 else ""
        phone = r[5].strip() if len(r) > 5 else ""
        email = r[6].strip() if len(r) > 6 else ""
        weekend = r[7].strip() if len(r) > 7 else ""
        last_batch = batch
        if name and name.lower() != "name":
            advisors.append({
                "batch": batch,
                "sem": sem,
                "name": name,
                "init": init,
                "role": role,
                "phone": phone,
                "email": email,
                "weekend": weekend
            })
    return advisors

def parse_crs(rows: List[List[str]]) -> List[Dict[str, Any]]:
    crs = []
    last_batch = ""
    for r in rows[2:]:
        if not any(c.strip() for c in r):
            continue
        batch = r[2].strip() if len(r) > 2 and r[2].strip() else last_batch
        sem = r[3].strip() if len(r) > 3 else ""
        cr1_id = r[4].strip() if len(r) > 4 else ""
        cr1_name = r[5].strip() if len(r) > 5 else ""
        cr1_phone = r[6].strip() if len(r) > 6 else ""
        cr1_email = r[7].strip() if len(r) > 7 else ""
        cr2_id = r[8].strip() if len(r) > 8 else ""
        cr2_name = r[9].strip() if len(r) > 9 else ""
        cr2_phone = r[10].strip() if len(r) > 10 else ""
        cr2_email = r[11].strip() if len(r) > 11 else ""
        last_batch = batch
        if sem and (cr1_name or cr2_name):
            crs.append({
                "batch": batch,
                "sem": sem,
                "cr1": {"id": cr1_id, "name": cr1_name, "phone": cr1_phone, "email": cr1_email},
                "cr2": {"id": cr2_id, "name": cr2_name, "phone": cr2_phone, "email": cr2_email} if cr2_name else None
            })
    return crs

def parse_rooms(rows: List[List[str]]) -> List[Dict[str, Any]]:
    rooms = []
    for r in rows[1:]:
        if not any(c.strip() for c in r):
            continue
        c_type = r[0].strip()
        room_name = r[1].strip() if len(r) > 1 else ""
        if not room_name or room_name.lower() == "room":
            continue
        cap = r[2].strip() if len(r) > 2 else ""
        rem = r[3].strip() if len(r) > 3 else ""
        rooms.append({
            "type": c_type,
            "room": room_name,
            "capacity": cap,
            "remarks": rem
        })
    return rooms

def parse_courses(rows: List[List[str]]) -> List[Dict[str, Any]]:
    courses = []
    last_batch = ""
    last_sem = ""
    last_code = ""
    last_title = ""
    last_cr = "3.0"

    for r in rows[4:]:
        if not any(c.strip() for c in r):
            continue
        batch = r[1].strip() if len(r) > 1 and r[1].strip() else last_batch
        sem_raw = r[2].strip() if len(r) > 2 and r[2].strip() else last_sem
        code = r[3].strip() if len(r) > 3 and r[3].strip() else last_code
        title = r[4].strip() if len(r) > 4 and r[4].strip() else last_title
        cr = r[5].strip() if len(r) > 5 and r[5].strip() else last_cr
        sec = r[7].strip() if len(r) > 7 else ""
        fac = r[9].strip() if len(r) > 9 else ""

        last_batch = batch
        last_sem = sem_raw
        last_code = code
        last_title = title
        last_cr = cr

        if code and title and "course" not in code.lower():
            sem_num = re.search(r"\d+", sem_raw)
            sem_val = sem_num.group(0) if sem_num else sem_raw

            rec_style = "normal_class_note"
            t_lower = title.lower() + " " + code.lower()
            if any(w in t_lower for w in ["lab", "sessional", "project", "algorithm", "structure", "program"]):
                rec_style = "simulation_pdf"
            elif any(w in t_lower for w in ["math", "phy", "circuit", "signal", "microprocessor", "electronic", "statistics", "logic"]):
                rec_style = "engineering_math"
            elif any(w in t_lower for w in ["network", "cyber", "database", "dbms", "oop", "java", "cloud"]):
                rec_style = "master_docx"
            else:
                rec_style = "lecture_cornell"

            is_lab = "sessional" in t_lower or "lab" in t_lower or "project" in t_lower

            courses.append({
                "sem": sem_val,
                "semName": sem_raw,
                "batch": batch.replace("\n", " "),
                "code": code,
                "title": title,
                "cr": cr,
                "type": "Lab" if is_lab else "Theory",
                "sec": sec,
                "teacher": fac,
                "recStyle": rec_style
            })

    # Group / deduplicate by (sem, code)
    dedup: Dict[str, Dict[str, Any]] = {}
    for c in courses:
        key = f"{c['sem']}_{c['code']}"
        if key not in dedup:
            dedup[key] = c
        else:
            if c["teacher"] and c["teacher"] not in dedup[key]["teacher"]:
                dedup[key]["teacher"] += f" / {c['teacher']} ({c['sec']})"
    return list(dedup.values())

def parse_equiv(rows: List[List[str]]) -> List[Dict[str, Any]]:
    equiv = []
    for r in rows[2:]:
        if not any(c.strip() for c in r) or len(r) < 4:
            continue
        eq_code = r[1].strip() if len(r) > 1 else ""
        cur_code = r[2].strip() if len(r) > 2 else ""
        title = r[3].strip() if len(r) > 3 else ""
        credits_val = r[4].strip() if len(r) > 4 else ""
        faculty = r[5].strip() if len(r) > 5 else ""
        if title:
            equiv.append({
                "equiv_code": eq_code,
                "current_code": cur_code,
                "title": title,
                "credits": credits_val,
                "faculty": faculty
            })
    return equiv

def parse_routine(rows: List[List[str]]) -> List[Dict[str, Any]]:
    days = ["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]
    current_day = None
    time_slots = []
    routine_entries = []

    for r in rows:
        if not any(c.strip() for c in r):
            continue
        day_match = next((d for d in days if len(r) > 1 and d.lower() in r[1].lower() or d.lower() in r[0].lower()), None)
        if day_match:
            current_day = day_match
            continue
        if any("AM" in c or "PM" in c for c in r):
            time_slots = []
            for ci, cell in enumerate(r):
                if "AM" in cell or "PM" in cell:
                    time_slots.append({"col": ci, "time": cell.strip()})
            continue
        if any("(sem.)" in c.lower() for c in r):
            continue

        section = r[0].strip()
        if not section or not current_day:
            continue

        for slot in time_slots:
            ci = slot["col"]
            if ci < len(r) and r[ci].strip():
                course = r[ci].strip()
                faculty = r[ci + 1].strip() if ci + 1 < len(r) else ""
                room = r[ci + 2].strip() if ci + 2 < len(r) else ""
                if "\n" in course:
                    parts = [p.strip() for p in course.split("\n") if p.strip()]
                    course = parts[0]
                    if len(parts) > 1 and not faculty:
                        faculty = parts[1]
                    if len(parts) > 2 and not room:
                        room = parts[2]
                routine_entries.append({
                    "day": current_day,
                    "time": slot["time"],
                    "section": section,
                    "course": course,
                    "faculty": faculty,
                    "room": room
                })
    return routine_entries

def sync_all_sheets(force_refresh: bool = False) -> Dict[str, Any]:
    global _CACHE
    now = time.time()
    if not force_refresh and _CACHE["data"] and (now - _CACHE["timestamp"]) < CACHE_TTL:
        return _CACHE["data"]

    try:
        faculty_csv = fetch_sheet_csv(SHEET_GIDS["faculty"])
        faculty_data = parse_faculty(faculty_csv)

        advisors_csv = fetch_sheet_csv(SHEET_GIDS["advisors"])
        advisors_data = parse_advisors(advisors_csv)

        crs_csv = fetch_sheet_csv(SHEET_GIDS["crs"])
        crs_data = parse_crs(crs_csv)

        rooms_csv = fetch_sheet_csv(SHEET_GIDS["rooms"])
        rooms_data = parse_rooms(rooms_csv)

        courses_csv = fetch_sheet_csv(SHEET_GIDS["courses"])
        courses_data = parse_courses(courses_csv)

        equiv_csv = fetch_sheet_csv(SHEET_GIDS["equiv"])
        equiv_data = parse_equiv(equiv_csv)

        routine_csv = fetch_sheet_csv(SHEET_GIDS["routine"])
        routine_data = parse_routine(routine_csv)

        payload = {
            "status": "ok",
            "sheet_id": SHEET_ID,
            "synced_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "counts": {
                "faculty": len(faculty_data),
                "advisors": len(advisors_data),
                "crs": len(crs_data),
                "rooms": len(rooms_data),
                "courses": len(courses_data),
                "equiv": len(equiv_data),
                "routine": len(routine_data)
            },
            "faculty": faculty_data,
            "advisors": advisors_data,
            "crs": crs_data,
            "rooms": rooms_data,
            "courses": courses_data,
            "equiv": equiv_data,
            "routine": routine_data
        }
        _CACHE["timestamp"] = now
        _CACHE["data"] = payload
        return payload
    except Exception as e:
        if _CACHE["data"]:
            # return stale cache if live fetch hits transient network glitch
            stale = dict(_CACHE["data"])
            stale["warning"] = f"Using cached data due to network error: {e}"
            return stale
        raise RuntimeError(f"Failed to sync Google Sheets: {e}")
