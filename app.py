import streamlit as st
from supabase import create_client

# --- 1. إعدادات الربط بمشروع AbuHawra ---
URL = "https://iptsrwpxylqlnpekscuh.supabase.co"
KEY = "sb_publishable_VK9dQHxf8bT43L3Wr6oGWA_QNdoNh9L"
supabase = create_client(URL, KEY)

st.set_page_config(page_title="نظام رصد الغياب", layout="centered")

# تنسيق اللغة العربية
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .stButton>button { width: 100%; border-radius: 5px; background-color: #007bff; color: white; }
    </style>
    """, unsafe_allow_html=True)

if 'auth' not in st.session_state:
    st.session_state.auth = False

# --- 2. واجهة تسجيل الدخول ---
if not st.session_state.auth:
    st.header("🔐 دخول النظام")
    user_input = st.text_input("أدخل السجل المدني الخاص بك").strip()
    
    if st.button("دخول"):
        if user_input:
            try:
                # البحث في الجدول الجديد teachers_new
                res = supabase.table("teachers_new").select("*").eq("t_id", user_input).execute()
                
                if res.data:
                    st.session_state.auth = True
                    st.session_state.name = res.data[0]['t_name']
                    st.success("تم الدخول بنجاح!")
                    st.rerun()
                else:
                    st.error(f"السجل ({user_input}) غير مضاف في النظام.")
            except Exception as e:
                st.error("خطأ في الاتصال بقاعدة البيانات. تأكد من إعدادات Supabase.")
        else:
            st.warning("يرجى كتابة رقم السجل.")

# --- 3. واجهة النظام بعد الدخول ---
else:
    st.balloons()
    st.success(f"مرحباً بك أستاذ/ {st.session_state.name}")
    st.info("نظام رصد الغياب جاهز للعمل. يمكنك الآن البدء برفع بيانات الطلاب.")
    
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.auth = False
        st.rerun()
