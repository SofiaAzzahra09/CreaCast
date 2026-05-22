from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

import base64

from services.database_service import DatabaseService

profile_bp = Blueprint(
    "profile",
    __name__,
    url_prefix="/profile"
)

db = DatabaseService()

# =====================================================
# GET USER
# =====================================================

def get_user():

    query = """
        SELECT
            id,
            nama,
            username,
            role,
            foto
        FROM users
        LIMIT 1
    """

    row = db.fetchone(query)

    if row:

        photo_base64 = None

        if row["foto"]:

            photo_base64 = base64.b64encode(
                row["foto"]
            ).decode("utf-8")

        return {
            "id": row["id"],
            "name": row["nama"],
            "username": row["username"],
            "role": row["role"],
            "photo": photo_base64
        }

    return {
        "id": 1,
        "name": "Administrator",
        "username": "admin",
        "role": "Admin",
        "photo": None
    }

# =====================================================
# PROFILE PAGE
# =====================================================

@profile_bp.route("/")
def index():

    user = get_user()

    laporan_count = len(
        db.get_laporan_history()
    )

    return render_template(
        "profile/index.html",
        user=user,
        laporan_count=laporan_count
    )

# =====================================================
# UPDATE PROFILE
# =====================================================

@profile_bp.route(
    "/update",
    methods=["POST"]
)
def update_profile():

    user_id = request.form.get("id")

    nama = request.form.get("nama")

    username = request.form.get("username")

    foto = None

    uploaded = request.files.get("foto")

    if uploaded and uploaded.filename != "":

        foto = uploaded.read()

    try:

        if foto:

            query = """
                UPDATE users
                SET
                    nama = ?,
                    username = ?,
                    foto = ?
                WHERE id = ?
            """

            db.execute(
                query,
                (
                    nama,
                    username,
                    foto,
                    user_id
                )
            )

        else:

            query = """
                UPDATE users
                SET
                    nama = ?,
                    username = ?
                WHERE id = ?
            """

            db.execute(
                query,
                (
                    nama,
                    username,
                    user_id
                )
            )

        flash(
            "Profil berhasil diperbarui",
            "success"
        )

    except Exception as e:

        flash(
            f"Gagal update profil: {e}",
            "danger"
        )

    return redirect(
        url_for("profile.index")
    )

# =====================================================
# UPDATE PASSWORD
# =====================================================

@profile_bp.route(
    "/update-password",
    methods=["POST"]
)
def update_password():

    user_id = request.form.get("id")

    old_password = request.form.get(
        "old_password"
    )

    new_password = request.form.get(
        "new_password"
    )

    confirm_password = request.form.get(
        "confirm_password"
    )

    user = db.fetchone(
        "SELECT password FROM users WHERE id=?",
        (user_id,)
    )

    if not user:

        flash(
            "User tidak ditemukan",
            "danger"
        )

        return redirect(
            url_for("profile.index")
        )

    if old_password != user["password"]:

        flash(
            "Password lama salah",
            "danger"
        )

        return redirect(
            url_for("profile.index")
        )

    if new_password != confirm_password:

        flash(
            "Konfirmasi password tidak cocok",
            "danger"
        )

        return redirect(
            url_for("profile.index")
        )

    if len(new_password) < 6:

        flash(
            "Password minimal 6 karakter",
            "warning"
        )

        return redirect(
            url_for("profile.index")
        )

    try:

        db.execute(
            """
            UPDATE users
            SET password=?
            WHERE id=?
            """,
            (
                new_password,
                user_id
            )
        )

        flash(
            "Password berhasil diperbarui",
            "success"
        )

    except Exception as e:

        flash(
            f"Gagal update password: {e}",
            "danger"
        )

    return redirect(
        url_for("profile.index")
    )