import os
import uuid

from flask import Flask, flash, redirect, render_template, request, url_for, send_from_directory
import crud

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
ALLOWED_EXTENSIONS = {"pdf", "txt", "md", "docx"}

os.makedirs(UPLOAD_DIR, exist_ok=True)
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev")
@app.route("/")
def index():
    return render_template("index.html")
@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file or file.filename == "":
        flash("Файл не выбран")
        return redirect(url_for("index"))

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        flash(f"Недопустимый формат: {ext or 'без расширения'}")
        return redirect(url_for("index"))

    stored_name = f"{uuid.uuid4().hex}.{ext}"
    original_name = file.filename
    size_bytes = len(file.read())
    file.seek(0)
    file.save(os.path.join(UPLOAD_DIR, stored_name))
    flash(f"Файл сохранён как {stored_name}")

    crud.add_file(stored_name, original_name, size_bytes, ext)
    return redirect(url_for("index"))
@app.route("/documents-list")
def documents_list():
    documents = crud.get_by_query()
    return render_template("documents_list.html", documents=documents)
@app.route("/documents/<path:name>")
def serve_document(name):
    return send_from_directory(UPLOAD_DIR, name)
@app.route("/delete/<int:id>", methods=["POST"])
def delete_document(id):
    file_data = crud.get_by_id(id)
    if file_data:
        try:
            crud.remove_file(id)
        except Exception as e:
            print("[+]", e)

        try:
            os.remove(os.path.join(UPLOAD_DIR, file_data["stored_name"]))
        except Exception as e:
            print("[-]", e)

    return redirect(url_for("documents_list"))

@app.route("/documents-filter", methods=["POST"])
def documents_filter():
    q = request.form.get("q", "")
    print("[+]", q)
    documents = crud.get_by_query(q)
    return render_template("documents_list.html", documents=documents)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
