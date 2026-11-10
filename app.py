import json
from flask import Flask, render_template, request, send_file, flash
import ats

app = Flask(__name__)
app.secret_key = "inovate-change-me"
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
STYLE_NAMES = {"classic": "Classic", "modern": "Modern", "compact": "Compact", "elegant": "Elegant"}

@app.get("/")
def index(): return render_template("index.html")

@app.route("/checker", methods=["GET", "POST"])
def checker():
    result = tailored = None
    if request.method == "POST":
        f = request.files.get("resume")
        if not f or not f.filename:
            flash("Please choose a resume file.")
        else:
            try:
                text, flags = ats.extract(f)
                result = ats.score(text, flags, request.form.get("jd", ""))
                tailored = json.dumps(ats.to_resume(text))
            except Exception as e:
                flash(f"Could not read the file: {e}")
    return render_template("checker.html", result=result, tailored=tailored)

@app.route("/creator", methods=["GET", "POST"])
def creator():
    if request.method == "POST":
        g = lambda k: request.form.get(k, "").strip()
        lines = lambda k: [l.strip() for l in g(k).splitlines() if l.strip()]
        data = {"name": g("name") or "Your Name", "title": g("title"),
                "contact": [x for x in [g("email"), g("phone"), g("address"), g("link")] if x],
                "sections": [{"title": t, "lines": lines(k)} for t, k in [
                    ("Summary", "about"), ("Experience", "experience"), ("Education", "education"),
                    ("Skills", "skills"), ("Projects", "projects"), ("Certifications", "certificates"),
                    ("Volunteering", "volunteering"), ("Achievements", "achievements")]]}
        return render_template("resume_view.html", data=data, data_json=json.dumps(data),
                               style=g("style") or "classic", styles=STYLE_NAMES)
    return render_template("creator.html", styles=STYLE_NAMES)

@app.post("/preview")
def preview():
    data_json = request.form["data_json"]
    return render_template("resume_view.html", data=json.loads(data_json), data_json=data_json,
                           style=request.form.get("style", "classic"), styles=STYLE_NAMES)

@app.post("/download")
def download():
    data = json.loads(request.form["data_json"])
    buf = ats.build_docx(data, request.form.get("style", "classic"))
    return send_file(buf, as_attachment=True, download_name="inovate_resume.docx")

if __name__ == "__main__":
    app.run(debug=True)
