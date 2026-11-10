# Inovate Resume
ATS resume checker + creator. Flask backend, Bootstrap 5 (burgundy & cream) HTML/CSS frontend.

## Run
    python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
    pip install -r requirements.txt
    python app.py   # open http://127.0.0.1:5000

## Hugging Face model
`sentence-transformers/all-MiniLM-L6-v2` (downloaded on first use) compares the resume with a pasted job description
and contributes up to 10 points. Disable with `INOVATE_USE_MODEL=0` (rule-based scoring still works).
Swap the model in `ats.py` (`HF_MODEL`) for any other sentence-embedding or resume model.

## Structure
- `app.py` routes · `ats.py` extraction, scoring, resume structuring, DOCX export
- `templates/` index, checker, creator, resume_view (4 ATS templates: classic, modern, compact, elegant)
- `static/style.css` theme, hover and shadow effects
