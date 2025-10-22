import os
from datetime import datetime
from pathlib import Path

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"


def create_app():
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "devkey"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL", f"sqlite:///{BASE_DIR / 'companyhub.db'}"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=str(UPLOAD_FOLDER),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16 MB limit
    )

    db.init_app(app)

    @app.before_request
    def ensure_upload_dir():
        UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

    @app.context_processor
    def inject_now():
        return {"now": datetime.utcnow()}

    register_routes(app)

    with app.app_context():
        db.create_all()

    return app


db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    uploads = db.relationship("FileUpload", back_populates="user", cascade="all, delete")
    tasks = db.relationship("Task", back_populates="assignee")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<User {self.name}>"


class FileUpload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    description = db.Column(db.Text, nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", back_populates="uploads")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<FileUpload {self.original_name} by {self.user.name}>"


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.Date, nullable=True)
    completed = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    assignee_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    assignee = db.relationship("User", back_populates="tasks")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Task {self.title}>"


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf", "docx", "xlsx"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_or_create_user(username: str) -> User:
    user = User.query.filter_by(name=username).first()
    if user is None:
        user = User(name=username)
        db.session.add(user)
        db.session.commit()
    return user


def register_routes(app: Flask) -> None:
    @app.get("/")
    def dashboard():
        tasks = (
            Task.query.order_by(Task.completed, Task.due_date.is_(None), Task.due_date)
            .limit(10)
            .all()
        )
        uploads = FileUpload.query.order_by(FileUpload.uploaded_at.desc()).limit(8).all()
        users = User.query.order_by(User.name).all()
        return render_template(
            "index.html", tasks=tasks, uploads=uploads, users=users, title="Panel"
        )

    @app.get("/uploads/<path:filename>")
    def uploaded_file(filename: str):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=False)

    @app.route("/upload", methods=["GET", "POST"])
    def upload():
        users = User.query.order_by(User.name).all()
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            description = request.form.get("description")
            file = request.files.get("file")

            if not username:
                flash("Debe indicar el nombre del usuario responsable de la subida.", "error")
            elif file is None or file.filename == "":
                flash("Seleccione un archivo para subir.", "error")
            elif not allowed_file(file.filename):
                flash("Tipo de archivo no permitido.", "error")
            else:
                user = get_or_create_user(username)
                filename = secure_filename(f"{datetime.utcnow().timestamp()}_{file.filename}")
                file_path = Path(app.config["UPLOAD_FOLDER"]) / filename
                file.save(file_path)

                upload_record = FileUpload(
                    filename=filename,
                    original_name=file.filename,
                    description=description,
                    user=user,
                )
                db.session.add(upload_record)
                db.session.commit()
                flash("Archivo cargado correctamente.", "success")
                return redirect(url_for("dashboard"))

        return render_template("upload.html", users=users, title="Subir archivo")

    @app.route("/tasks", methods=["GET", "POST"])
    def manage_tasks():
        users = User.query.order_by(User.name).all()
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            description = request.form.get("description")
            due_date_raw = request.form.get("due_date")
            assignee_name = request.form.get("assignee")

            if not title:
                flash("El título de la tarea es obligatorio.", "error")
            else:
                due_date = datetime.strptime(due_date_raw, "%Y-%m-%d").date() if due_date_raw else None
                assignee = None
                if assignee_name:
                    assignee = get_or_create_user(assignee_name)
                task = Task(
                    title=title,
                    description=description,
                    due_date=due_date,
                    assignee=assignee,
                )
                db.session.add(task)
                db.session.commit()
                flash("Tarea creada correctamente.", "success")
                return redirect(url_for("manage_tasks"))

        tasks = Task.query.order_by(Task.completed, Task.due_date.is_(None), Task.due_date).all()
        return render_template("tasks.html", tasks=tasks, users=users, title="Tareas")

    @app.post("/tasks/<int:task_id>/toggle")
    def toggle_task(task_id: int):
        task = Task.query.get_or_404(task_id)
        task.completed = not task.completed
        db.session.commit()
        flash("Estado de la tarea actualizado.", "success")
        return redirect(url_for("manage_tasks"))


if __name__ == "__main__":
    application = create_app()
    application.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
