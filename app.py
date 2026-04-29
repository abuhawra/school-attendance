import streamlit as st
from supabase import create_client

# الربط
url = "https://iptsrwpxylqlnpekscuh.supabase.co"
key = "sb_publishable_VK9dQHxf8bT43L3Wr6oGWA_QNdoNh9L"
supabase = create_client(url, key)

st.set_page_config(page_title="نظام التحضير المدرسي", layout="centered")

# --- تسجيل الدخول ---
if 'teacher' not in st.session_state:
    st.header("🔑 دخول المعلم")
    nid_input = st.text_input("أدخل رقم السجل المدني:")
    
    if st.button("دخول"):
        if nid_input:
            clean_nid = nid_input.strip()
            res = supabase.table("teachers").select("*").eq("national_id", clean_nid).execute()
            if res.data:
                st.session_state.teacher = res.data[0]
                st.rerun()
            else:
                st.error("السجل غير موجود! تأكد من رفعه من Colab أولاً.")
        else:
            st.warning("يرجى إدخال السجل المدني")

# --- نافذة التحضير ---
else:
    teacher = st.session_state.teacher
    st.sidebar.success(f"المعلم: {teacher['name']}")
    
    if st.sidebar.button("خروج"):
        del st.session_state.teacher
        st.rerun()

    st.title("📋 تحضير الطلاب")
    
    try:
        # جلب اللجان
        res_com = supabase.table("students").select("committee").execute()
        committees = sorted(list(set([str(row['committee']) for row in res_com.data])))
        
        selected_comm = st.selectbox("اختر اللجنة:", ["-- اختر --"] + committees)
        
        if selected_comm != "-- اختر --":
            res_stu = supabase.table("students").select("*").eq("committee", selected_comm).execute()
            students = res_stu.data
            
            if students:
                with st.form("att_form"):
                    st.subheader(f"قائمة لجنة {selected_comm}")
                    results = {}
                    for stu in students:
                        c1, c2 = st.columns([2, 1])
                        c1.write(f"👤 **{stu['student_name']}** (فصل: {stu['section']})")
                        results[stu['student_name']] = {
                            "status": c2.radio("الحالة", ["حاضر", "غائب", "متأخر"], key=f"s_{stu['id']}", horizontal=True, label_visibility="collapsed"),
                            "section": stu['section']
                        }
                    
                    if st.form_submit_button("إرسال التحضير"):
                        final_data = []
                        for s_name, info in results.items():
                            final_data.append({
                                "student_name": s_name,
                                "committee": selected_comm,
                                "section": info['section'],
                                "status": info['status'],
                                "teacher_name": teacher['name']
                            })
                        supabase.table("attendance_records").insert(final_data).execute()
                        st.success("تم الحفظ بنجاح!")
    except Exception as e:
        st.error(f"خطأ: {e}")
