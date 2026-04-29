import streamlit as st
from supabase import create_client

# 1. إعدادات الربط مع قاعدة البيانات (Supabase)
url = "https://iptsrwpxylqlnpekscuh.supabase.co"
key = "sb_publishable_VK9dQHxf8bT43L3Wr6oGWA_QNdoNh9L"
supabase = create_client(url, key)

# إعداد شكل الصفحة
st.set_page_config(page_title="نظام التحضير المدرسي", layout="centered")

# --- واجهة تسجيل الدخول ---
if 'teacher' not in st.session_state:
    st.header("🔑 تسجيل دخول المعلم")
    nid = st.text_input("أدخل رقم السجل المدني:", type="password")
    
    if st.button("دخول"):
        if nid:
            # البحث عن المعلم برقم السجل
            res = supabase.table("teachers").select("*").eq("national_id", nid).execute()
            if res.data:
                st.session_state.teacher = res.data[0]
                st.rerun()
            else:
                st.error("رقم السجل غير موجود في قاعدة البيانات!")
        else:
            st.warning("الرجاء إدخال رقم السجل")

# --- واجهة التحضير بعد الدخول ---
else:
    teacher = st.session_state.teacher
    st.sidebar.success(f"مرحباً: {teacher['name']}")
    
    if st.sidebar.button("تسجيل الخروج"):
        del st.session_state.teacher
        st.rerun()

    st.title("📋 نافذة التحضير اليومي")
    
    # جلب قائمة اللجان المتاحة من جدول الطلاب
    try:
        res_com = supabase.table("students").select("committee").execute()
        # استخراج اللجان بدون تكرار
        all_comms = [str(row['committee']) for row in res_com.data]
        committees = sorted(list(set(all_comms)))
        
        selected_comm = st.selectbox("اختر اللجنة التي تريد تحضيرها:", ["-- اختر --"] + committees)
        
        if selected_comm != "-- اختر --":
            # جلب طلاب هذه اللجنة فقط
            res_stu = supabase.table("students").select("*").eq("committee", selected_comm).execute()
            students = res_stu.data
            
            if students:
                st.subheader(f"طلاب لجنة: {selected_comm}")
                st.info(f"عدد الطلاب في اللجنة: {len(students)}")
                
                # نموذج التحضير
                with st.form("attendance_form"):
                    attendance_results = {}
                    
                    for stu in students:
                        # عرض اسم الطالب وفصله
                        col_info, col_status = st.columns([2, 1])
                        col_info.write(f"👤 **{stu['student_name']}**")
                        col_info.caption(f"الفصل: {stu['section']}")
                        
                        # خيارات الحالة (حاضر هو الافتراضي)
                        status = col_status.radio(
                            "الحالة", 
                            ["حاضر", "غائب", "متأخر"], 
                            key=f"status_{stu['id']}", 
                            horizontal=True,
                            label_visibility="collapsed"
                        )
                        
                        attendance_results[stu['id']] = {
                            "name": stu['student_name'],
                            "section": stu['section'],
                            "status": status
                        }
                    
                    submit = st.form_submit_button("حفظ وإرسال الكشف")
                    
                    if submit:
                        # تجهيز البيانات للحفظ في جدول attendance_records
                        final_records = []
                        for s_id, info in attendance_results.items():
                            final_records.append({
                                "student_name": info['name'],
                                "committee": selected_comm,
                                "section": info['section'],
                                "status": info['status'],
                                "teacher_name": teacher['name']
                            })
                        
                        # إرسال البيانات لـ Supabase
                        supabase.table("attendance_records").insert(final_records).execute()
                        st.success(f"تم حفظ تحضير لجنة {selected_comm} بنجاح!")
            else:
                st.warning("لا يوجد طلاب في هذه اللجنة.")
                
    except Exception as e:
        st.error(f"حدث خطأ أثناء جلب البيانات: {e}")
