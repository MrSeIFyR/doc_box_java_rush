import os
import uuid

import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, flash, redirect, render_template, request, url_for, send_from_directory
import crud

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
LOGS_DIR = os.getenv("LOGS_DIR", "logs")

ALLOWED_EXTENSIONS = {"pdf", "txt", "md", "docx"}

os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev")

log_path = os.path.join(LOGS_DIR, "app.log")
handler = RotatingFileHandler(log_path, maxBytes=100000, backupCount=3)
handler.setFormatter(logging.Formatter(
    "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
))
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)
@app.route("/")
def index():
    return render_template("index.html")
@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file or file.filename == "":
        flash("Файл не выбран")
        return redirect(url_for("index"))

    ext = ""
    if "." in file.filename:
        ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        flash(f"Недопустимый формат: {ext or 'без расширения'}")
        return redirect(url_for("index"))

    try:
        data = file.read()
        size_bytes = len(data)
        file.seek(0)

        stored_name = f"{uuid.uuid4().hex}.{ext}"
        original_name = file.filename

        crud.add_file(stored_name, original_name, size_bytes, ext)

        file.save(os.path.join(UPLOAD_DIR, stored_name))

        app.logger.info(f"Файл успешно загружен: {original_name} ({size_bytes} байт), сохранён как {stored_name}")

        flash(f"Файл сохранён: {original_name}")
        return redirect(url_for("index"))

    except Exception as e:
        app.logger.error("Ошибка при загрузке файла: %s", e, exc_info=True)
        flash("Не удалось сохранить файл: ошибка базы данных или файловой системы")
        return redirect(url_for("index"))
@app.route("/documents-list")
def documents_list():
    try:
        page = int(request.args.get("page", 1))
        if page < 1:
            page = 1
    except ValueError:
        page = 1

    per_page = 10
    q = request.args.get("q", "")

    documents = crud.get_by_query(q, page, per_page)

    total = crud.get_count_by_query(q)

    total_pages = max(1, (total + per_page - 1) // per_page)

    return render_template(
        "documents_list.html",
        documents=documents,
        page=page,
        total_pages=total_pages,
        q=q,
        total=total
    )
@app.route("/documents/<path:name>")
def serve_document(name):
    app.logger.info(f"Пользователь запросил файл: {name}")
    return send_from_directory(UPLOAD_DIR, name)
@app.route("/delete/<int:id>", methods=["POST"])
def delete_document(id):
    file_data = crud.get_by_id(id)

    if not file_data:
        app.logger.error(f"Попытка удаления несуществующего документа ID={id}")
        flash("Документ с таким ID не найден.", "error")
        q = request.args.get("q", "")
        return redirect(url_for("documents_list", q=q))

    stored_name = file_data["stored_name"]
    file_path = os.path.join(UPLOAD_DIR, stored_name)

    try:
        crud.remove_file(id)
        app.logger.info(f"Успешно удалена запись документа ID={id} из БД")

        if os.path.exists(file_path):
            os.remove(file_path)
            app.logger.info(f"Файл удалён с диска: {stored_name}")
        else:
            app.logger.warning(f"Файл не найден на диске при удалении документа ID={id}: {stored_name}")

        flash("Документ успешно удалён.", "success")

    except Exception as e:
        app.logger.exception(f"Ошибка при удалении документа ID={id}: {e}")
        flash("Произошла ошибка при удалении документа.", "error")

    q = request.args.get("q", "")
    return redirect(url_for("documents_list", q=q))
@app.route("/documents-filter", methods=["POST"])
def documents_filter():
    q = request.form.get("q", "")
    return redirect(url_for("documents_list", q=q, page=1))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)