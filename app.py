import streamlit as st
from supabase import create_client
import pandas as pd

# --- 1. إعدادات الربط بمشروعك (روابطك الخاصة) ---
URL = "https://iptsrwpxylqlnpekscuh.supabase.co"
KEY = "sb_publishable_VK9dQHxf8bT43L3Wr6oGWA_QNdoNh9L"
supabase = create_client(URL, KEY)

# --- 2. تهيئة الصفحة وتنسيق اللغة العربية ---
st.set_page_config(page_title="نظام رصد الغياب", layout="centered")

# تنسيق CSS لضمان مظهر احترافي ودعم العربية
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo&display=swap');
    html, body, [class*="css"]  {
        font-family: 'Cairo', sans-serif;
        direction: rtl;
        text-align: right;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #007bff;
        color: white;
    }
    div[data-baseweb="input"] {
        direction: ltr; /* لجعل كتابة الأرقام من اليسار لليمين أسهل */
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📋 نظام رصد غياب الطلاب")

# --- 3. نظام التحقق من المعلم (تسجيل الدخول) ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.subheader("🔐 دخول المعلم")
    # استخدام strip() لإزالة أي مسافات زائدة
    input_id = st.text_input("أدخل السجل المدني الخاص بك").strip()
    
    if st.button("تسجيل الدخول"):
        if input_id:
            with st.spinner('جاري التحقق من السجل...'):
                # الخطوة أ: البحث عن المدخل كـ "نص" (String)
                res = supabase.table("teachers").select("*").eq("national_id", input_id).execute()
                
                # الخطوة ب: إذا لم يجد نتيجة، يحاول البحث عنه كـ "رقم" (Integer)
                if not res.data and input_id.isdigit():
                    res = supabase.table("teachers").select("*").eq("national_id", int(input_id)).execute()
                
                if res.data:
                    st.session_state.authenticated = True
                    st.session_state.teacher_name = res.data[0]['teacher_name']
                    st.success("تم الدخول بنجاح!")
                    st.rerun()
                else:
                    st.error(f"السجل ({input_id}) غير مسجل. تأكد من رفعه في ملف الإكسل بشكل صحيح.")
        else:
            st.warning("يرجى إدخال السجل المدني أولاً.")
else:
    # --- 4. واجهة رصد الغياب بعد الدخول ---
    st.info(f"مرحباً بك أ/ {st.session_state.teacher_name}")
    
    # جلب قوائم اللجان المتوفرة من جدول الطلاب
    try:
        res_comm = supabase.table("students").select("committee").execute()
        committees = sorted(list(set([r['committee'] for r in res_comm.data])))
        
        selected_comm = st.selectbox("اختر اللجنة المراد رصدها", [""] + committees)

        if selected_comm:
            # جلب طلاب اللجنة المختارة
            res_students = supabase.table("students").select("*").eq("committee", selected_comm).execute()
            students = res_students.data
            
            st.subheader(f"قائمة طلاب لجنة: {selected_comm}")
            st.write("---")
            
            attendance_to_save = []

            for std in students:
                col1, col2 = st.columns([3, 2])
                
                with col1:
                    st.write(f"👤 {std['student_name']}")
                
                with col2:
                    status = st.radio(
                        f"حالة {std['student_name']}",
                        ["حاضر", "غائب", "متأخر"],
                        key=f"status_{std['id']}",
                        horizontal=True,
                        label_visibility="collapsed"
                    )
                    
                    if status != "حاضر":
                        attendance_to_save.append({
                            "student_name": std['student_name'],
                            "committee": selected_comm,
                            "status": status,
                            "teacher_name": st.session_state.teacher_name
                        })
                st.write("---")

            if st.button("إرسال تقرير الغياب إلى الإدارة"):
                if attendance_to_save:
                    with st.spinner('جاري إرسال البيانات...'):
                        supabase.table("attendance_records").insert(attendance_to_save).execute()
                        st.success(f"تم رصد {len(attendance_to_save)} حالة بنجاح! ✅")
                else:
                    st.warning("لم يتم رصد أي غياب أو تأخر (الجميع حضور).")
    except Exception as e:
        st.error(f"حدث خطأ في جلب البيانات: {e}")
                
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.authenticated = False
        st.rerun()
