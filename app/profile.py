import streamlit as st

class ProfilePage:
    def __init__(self, db):
        self.db = db
        # Inisialisasi state untuk mode edit profil
        if "edit_mode" not in st.session_state:
            st.session_state.edit_mode = False
        
        # Load data dari DB saat pertama kali masuk halaman
        if "user_data" not in st.session_state:
            self.load_user_data()

    def load_user_data(self):
        """Mengambil data user menggunakan fetchone dari DatabaseService"""
        query = "SELECT nama, username, role, foto FROM users LIMIT 1"
        try:
            # Menggunakan fetchone sesuai yang ada di DatabaseService kamu
            row = self.db.fetchone(query)
            
            if row:
                st.session_state.user_data = {
                    "name": row['nama'],
                    "username": row['username'],
                    "role": row['role'],
                    "photo": row['foto']
                }
            else:
                # Data fallback jika tabel users masih kosong
                st.session_state.user_data = {
                    "name": "Administrator",
                    "username": "admin",
                    "role": "Admin",
                    "photo": None
                }
        except Exception as e:
            st.error(f"Gagal memuat data user: {e}")

    def render(self):
        st.title("Profile User")
        st.caption("Informasi akun dan aktivitas sistem")

        # Gunakan data dari session state
        user = st.session_state.user_data

        # --- BAGIAN INFORMASI AKUN ---
        col1, col2 = st.columns([1, 3])

        with col1:
            # Tampilkan foto (BLOB) atau default avatar
            if user.get("photo"):
                st.image(user["photo"], width=150)
            else:
                st.image("https://ui-avatars.com/api/?name=Admin", width=150)
            
            if st.session_state.edit_mode:
                uploaded_file = st.file_uploader("Ganti Foto", type=["jpg", "png", "jpeg"])
                if uploaded_file:
                    # Ambil bytes dari foto untuk disimpan ke BLOB
                    user["photo"] = uploaded_file.getvalue()
                    st.session_state.user_data = user

        with col2:
            if not st.session_state.edit_mode:
                st.subheader(user.get("name"))
                st.write(f"**Username:** {user.get('username')}")
                st.write(f"**Role:** {user.get('role')}")
                
                if st.button("Edit Profil", type="secondary"):
                    st.session_state.edit_mode = True
                    st.rerun()
            else:
                new_name = st.text_input("Nama Lengkap", value=user.get("name"))
                new_user = st.text_input("Username", value=user.get("username"))
                
                # Jarak tombol proporsional (Spacer 0.1 agar tidak nempel tapi tidak jauh)
                c_simpan, spacer, c_batal, c_filler = st.columns([0.4, 0.1, 0.4, 2])
                
                with c_simpan:
                    if st.button("Simpan", type="primary", use_container_width=True):
                        # Simpan ke DB menggunakan fungsi execute()
                        query = "UPDATE users SET nama = ?, username = ?, foto = ? WHERE id = 1"
                        try:
                            self.db.execute(query, (new_name, new_user, user.get("photo")))
                            
                            # Update session state
                            st.session_state.user_data["name"] = new_name
                            st.session_state.user_data["username"] = new_user
                            st.session_state.edit_mode = False
                            st.success("Perubahan disimpan!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal menyimpan: {e}")
                
                with c_batal:
                    if st.button("Batal", use_container_width=True):
                        st.session_state.edit_mode = False
                        st.rerun()

        st.divider()

        # --- BAGIAN STATISTIK ---
        st.subheader("Aktivitas Sistem")
        col3, col4, col5 = st.columns(3)
        # Menghitung data laporan dari DB menggunakan DatabaseService
        laporan_count = len(self.db.get_laporan_history())
        
        with col3:
            st.metric("Total Laporan", laporan_count)
        with col4:
            st.metric("Total Prediksi", 112) # Sesuaikan jika ada fungsi count prediksi
        with col5:
            st.metric("Upload Dataset", 8)

        st.divider()

        # --- BAGIAN UPDATE PASSWORD ---
        st.subheader("Pengaturan Keamanan")
        col_pass, _ = st.columns([1.5, 1])

        with col_pass:
            with st.form("ubah_password", clear_on_submit=True):
                st.write("Ganti Password")
                old_pass = st.text_input("Password lama", type="password")
                new_pass = st.text_input("Password baru", type="password")
                confirm_pass = st.text_input("Konfirmasi password", type="password")

                submit = st.form_submit_button("Update Password")

                if submit:
                    if new_pass == confirm_pass and len(new_pass) >= 6:
                        # Update password di database
                        query = "UPDATE users SET password = ? WHERE id = 1"
                        self.db.execute(query, (new_pass,))
                        st.success("Password berhasil diperbarui!")
                    else:
                        st.error("Pastikan konfirmasi password sama dan minimal 6 karakter.")