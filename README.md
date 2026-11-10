# Inovate Resume

An ATS (Applicant Tracking System) resume checker and creator. Upload a resume to get an ATS score and a clean, ATS-friendly rebuild, or create a new resume from scratch using ATS-safe templates.

## Features

- **ATS Checker:** upload a `.docx` or `.pdf`, get a 0-100 score, a breakdown by category and fix recommendations.
- **Auto-tailoring:** if a resume is not ATS friendly, regenerate it with standard headings in a single-column layout.
- **Resume Creator:** enter your details and generate a resume in one of 4 templates (Classic, Modern, Compact, Elegant).
- **Export:** download as `.docx`, or save as PDF from the browser's print dialog.
- **AI job match (optional):** a Hugging Face model compares your resume with a pasted job description.
- **UI:** Bootstrap 5 with a burgundy and cream theme, hover and shadow effects.

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, Bootstrap 5, Bootstrap Icons |
| Backend | Python 3.9+, Flask, Jinja2 |
| Parsing | python-docx (.docx), pypdf (.pdf) |
| AI model | `sentence-transformers/all-MiniLM-L6-v2` (Hugging Face) |

## Project structure

```
inovate-resume/
├── app.py               # Flask routes
├── ats.py               # text extraction, scoring, resume structuring, DOCX export
├── requirements.txt
├── static/style.css     # theme, hover/shadow effects, resume templates
└── templates/
    ├── base.html        # navbar, footer, shared layout
    ├── index.html       # home / features
    ├── checker.html     # upload form + score dashboard
    ├── creator.html     # resume form + template picker
    └── resume_view.html # preview, template switch, downloads
```

## Getting started

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000.

Next time, only run `source venv/bin/activate` and `python app.py`.

`sentence-transformers` installs PyTorch, so the first install is large. To skip the AI model, remove that line from `requirements.txt` and start the app with:

```bash
INOVATE_USE_MODEL=0 python app.py
```

## How to use

1. **Check a resume:** go to **ATS Checker**, upload your file (optionally paste a job description) and click **Analyze**. Click **Generate ATS-friendly resume** to get a tailored version.
2. **Create a resume:** go to **Resume Creator**, choose a template, fill in the form (one entry per line in the text areas) and click **Generate resume**.
3. **Export:** on the preview, switch template if needed, then click **Download .docx** or **Save as PDF**.

## Scoring

| Category | Points | What is checked |
|---|---|---|
| Contact details | 15 | email, phone, LinkedIn or GitHub |
| Standard section headings | 25 | Experience, Education, Skills (required); Summary, Projects, Certifications |
| Parsable formatting | 20 | penalties for tables, images, more than 2 pages, very short text |
| Action verbs and metrics | 20 | strong verbs, numbers and percentages |
| Length | 10 | about 300-900 words |
| Job-description match | 10 | AI model similarity, only when a job description is provided |

Without a job description, the score is scaled over the other 90 points. Verdicts: **75+** ATS friendly, **50-74** Needs improvement, **below 50** Not ATS friendly.

## Hugging Face model

The model `sentence-transformers/all-MiniLM-L6-v2` is downloaded automatically on first use and cached locally. It turns the resume and the job description into embeddings, and their cosine similarity becomes the job-match score. To try another embedding model, change `HF_MODEL` in `ats.py`.

## Configuration

| Setting | Where | Default |
|---|---|---|
| `INOVATE_USE_MODEL` | environment variable | `1` (set `0` to disable the AI model) |
| `secret_key` | `app.py` | change before any deployment |
| Max upload size | `app.py` (`MAX_CONTENT_LENGTH`) | 5 MB |

## Troubleshooting

- **`externally-managed-environment` on macOS:** use the virtual environment steps above instead of installing system-wide.
- **Port 5000 already in use:** macOS AirPlay Receiver can take it. Run `flask run --port 5001` or change the port in `app.py`.
- **Layout looks unstyled:** Bootstrap loads from a CDN, so an internet connection is needed.
- **Empty or low score on a PDF:** scanned PDFs (images of text) cannot be read. Upload a text-based PDF or a `.docx`.

## Limitations

- Scoring is rule-based; the Hugging Face model only affects the job-description match.
- Tailoring relies on detecting section headings, so unusual headings may need a manual edit.
- PDF output uses the browser's Save as PDF rather than server-side generation.

## Roadmap

- Keyword suggestions per job description
- Fine-tuned resume-parsing model
- User accounts with saved resumes and score history
- Server-side PDF export
