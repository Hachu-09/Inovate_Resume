"""ATS analysis + resume structuring + DOCX export for Inovate Resume."""
import io, os, re
from docx import Document
from docx.shared import Pt, RGBColor
from pypdf import PdfReader

# ---------- Hugging Face model (lazy, optional) ----------
HF_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
_model = None
def _get_model():
    global _model
    if _model is None and os.getenv("INOVATE_USE_MODEL", "1") == "1":
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer(HF_MODEL)
        except Exception as e:
            print("HF model unavailable:", e); _model = False
    return _model or None

def semantic_match(resume, jd):
    """Cosine similarity (0-1) between resume and job description using the HF model."""
    m = _get_model()
    if not m: return None
    from sentence_transformers import util
    a, b = m.encode([resume[:4000], jd[:4000]], convert_to_tensor=True)
    return max(0.0, min(1.0, (float(util.cos_sim(a, b)) - 0.2) / 0.5))

# ---------- Extraction ----------
def extract(file):
    name = file.filename.lower(); flags = {"tables": 0, "images": 0, "pages": 1}
    if name.endswith(".docx"):
        d = Document(file)
        text = "\n".join(p.text for p in d.paragraphs)
        flags["tables"] = len(d.tables)
        flags["images"] = len(d.inline_shapes)
        for t in d.tables:
            for r in t.rows:
                text += "\n" + " ".join(c.text for c in r.cells)
    elif name.endswith(".pdf"):
        r = PdfReader(file); flags["pages"] = len(r.pages)
        text = "\n".join((p.extract_text() or "") for p in r.pages)
        flags["images"] = sum(len(p.images) for p in r.pages)
    else:
        raise ValueError("Please upload a .docx or .pdf file")
    return text, flags

# ---------- Sectioning ----------
SECTIONS = {
    "Summary": r"summary|objective|about|profile",
    "Education": r"education|academic",
    "Experience": r"experience|employment|work history|internship",
    "Skills": r"skills|technologies|competenc|tech stack",
    "Projects": r"projects?",
    "Certifications": r"certif|courses|licen",
    "Volunteering": r"volunteer",
    "Achievements": r"achievements?|awards?|honou?rs",
}
def split_sections(text):
    out, cur = {"Header": []}, "Header"
    for line in text.splitlines():
        s = line.strip()
        if not s: continue
        key = re.sub(r"[^a-z &]", "", s.lower()).strip()
        hit = next((k for k, p in SECTIONS.items()
                    if len(s) < 40 and re.fullmatch(rf"(?:{p})[a-z &]*", key)), None)
        if hit: cur = hit; out.setdefault(cur, []); continue
        out.setdefault(cur, []).append(s)
    return out

def to_resume(text):
    """Turn raw resume text into the clean structure used by templates/DOCX."""
    s = split_sections(text); head = s.pop("Header", [])
    email = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text)
    phone = re.search(r"\+?\d[\d\s().-]{8,}\d", text)
    contact = [x for x in [email and email.group(), phone and phone.group().strip()] if x]
    order = list(SECTIONS)
    return {"name": head[0] if head else "Your Name", "title": "", "contact": contact,
            "sections": [{"title": k, "lines": [l.lstrip("•-*· ").strip() for l in s[k]]}
                         for k in order if k in s]}

# ---------- Scoring ----------
VERBS = "led managed built developed designed implemented created improved increased reduced delivered launched optimized automated analyzed deployed collaborated achieved trained mentored engineered".split()

def score(text, flags, jd=""):
    words = len(text.split()); low = text.lower(); s = split_sections(text)
    items, tips = [], []
    def add(label, pts, mx, tip=None):
        items.append({"label": label, "pts": round(pts), "max": mx})
        if tip and pts < mx * 0.7: tips.append(tip)
    has = lambda r: re.search(r, text)
    c = 5*bool(has(r"[\w.+-]+@[\w-]+\.[\w.]+")) + 5*bool(has(r"\+?\d[\d\s().-]{8,}\d")) + 5*("linkedin" in low or "github" in low)
    add("Contact details", c, 15, "Add a professional email, phone number and LinkedIn/GitHub link.")
    must = ["Experience", "Education", "Skills"]; nice = ["Summary", "Projects", "Certifications"]
    sec = sum(6 for k in must if k in s) + sum(2.3 for k in nice if k in s)
    add("Standard section headings", sec, 25, "Use standard headings: Summary, Experience, Education, Skills, Projects, Certifications.")
    fmt = 20 - 8*(flags["tables"] > 0) - 6*(flags["images"] > 0) - 4*(flags["pages"] > 2) - 8*(words < 150)
    add("Parsable formatting", max(fmt, 0), 20, "Remove tables, columns, images/icons and keep to 1-2 pages so ATS can read your text.")
    verbs = sum(low.count(v) for v in VERBS); nums = len(re.findall(r"\d+%|\$\s?\d|\b\d{2,}\b", text))
    cont = min(verbs, 8) * 1.25 + min(nums, 5) * 2
    add("Action verbs & metrics", cont, 20, "Start bullets with action verbs and quantify results (e.g. 'cut load time by 35%').")
    ln = 10 if 300 <= words <= 900 else 6 if 150 <= words < 300 or 900 < words <= 1200 else 2
    add("Length", ln, 10, "Aim for roughly 300-900 words (1-2 pages).")
    total, mx = sum(i["pts"] for i in items), sum(i["max"] for i in items)
    sem = semantic_match(text, jd) if jd.strip() else None
    if sem is not None:
        add("Job-description match (AI model)", sem * 10, 10, "Add keywords and skills from the job description that you genuinely have.")
        total, mx = sum(i["pts"] for i in items), 100
    final = round(100 * total / mx)
    grade = "ATS friendly" if final >= 75 else "Needs improvement" if final >= 50 else "Not ATS friendly"
    return {"score": final, "grade": grade, "items": items, "tips": tips, "words": words,
            "model_used": sem is not None}

# ---------- DOCX export ----------
STYLES = {"classic": ("Times New Roman", 11, None), "modern": ("Calibri", 11, "7B1E2B"),
          "compact": ("Arial", 10, None), "elegant": ("Georgia", 11, "7B1E2B")}
def build_docx(r, style="classic"):
    font, size, color = STYLES.get(style, STYLES["classic"])
    d = Document(); st = d.styles["Normal"]; st.font.name = font; st.font.size = Pt(size)
    p = d.add_paragraph(); run = p.add_run(r["name"]); run.bold = True; run.font.size = Pt(20)
    if color: run.font.color.rgb = RGBColor.from_string(color)
    if r.get("title"): d.add_paragraph(r["title"])
    if r.get("contact"): d.add_paragraph(" | ".join(r["contact"]))
    for sec in r["sections"]:
        if not sec["lines"]: continue
        h = d.add_paragraph(); hr = h.add_run(sec["title"].upper()); hr.bold = True
        if color: hr.font.color.rgb = RGBColor.from_string(color)
        for l in sec["lines"]: d.add_paragraph(l, style="List Bullet")
    buf = io.BytesIO(); d.save(buf); buf.seek(0); return buf
