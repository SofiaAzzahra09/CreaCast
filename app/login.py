# app/login.py

import streamlit as st
from config import CREDENTIALS

class LoginPage:
    def authenticate(self, username: str, password: str) -> bool:
        if (
            username == CREDENTIALS["username"]
            and password == CREDENTIALS["password"]
        ):
            st.session_state["logged_in"] = True
            return True
        return False

    def render(self):
        col1, col2, col3 = st.columns([1.3, 1, 1.3])

        with col2:
            st.markdown('<div class="login-box">', unsafe_allow_html=True)

            st.title("Creatroka")
            st.caption("Sistem Prediksi Permintaan Buku & Optimasi Stok")
            st.markdown("---")

            inner1, inner2, inner3 = st.columns([0.1, 1, 0.1])

            with inner2:
                username = st.text_input(
                    "Username",
                    label_visibility="collapsed",
                    placeholder="Username"
                )

                password = st.text_input(
                    "Password",
                    type="password",
                    label_visibility="collapsed",
                    placeholder="Password"
                )

                st.markdown("")

                if st.button("Masuk"):
                    if self.authenticate(username, password):
                        st.rerun()
                    else:
                        st.error("Username atau password salah.")

            st.markdown("</div>", unsafe_allow_html=True)