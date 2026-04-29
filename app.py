import streamlit as st
from supabase import create_client

url = "https://iptsrwpxylqlnpekscuh.supabase.co"
key = "sb_publishable_VK9dQHxf8bT43L3Wr6oGWA_QNdoNh9L"
supabase = create_client(url, key)

if 'teacher' not in st.session_state:
    st.header("🔑 دخول المعلم")
    nid = st.text_input("أدخل رقم السجل المدني:")
    if st.button("دخول"):
        if nid:
            res = supabase.table("teachers").select("*").eq("teacher_id", nid.strip()).execute()
            if res.data:
                st.session_state.teacher = res.data[0]
                st.rerun()
            else:
                st.error(f"السجل {nid.strip()} غير موجود. تأكد من الرفع من Colab.")
else:
    # (بقية كود التحضير كما هو، فقط تأكد من تغيير الجزء العلوي)
    st.write(f"مرحباً {st.session_state.teacher['name']}")
    # اضف هنا كود التحضير السابق...
