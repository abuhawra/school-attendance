import streamlit as st
from supabase import create_client

# 1. إعدادات الربط
url = "https://iptsrwpxylqlnpekscuh.supabase.co"
key = "sb_publishable_VK9dQHxf8bT43L3Wr6oGWA_QNdoNh9L"
supabase = create_client(url, key)

st.set_page_config(page_title="نظام التحضير المدرسي", layout="centered")

# --- نظام تسجيل الدخول ---
if 'teacher' not in st.session_state:
    st.header("🔑 تسجيل دخول المعلم")
    nid_input = st.text_input("أدخل رقم السجل المدني للبدء:")
    
    if st.button("دخول"):
        if nid_input:
            clean_nid = nid_input.strip()
            # البحث عن المعلم في قاعدة البيانات
            res = supabase.table("teachers").select("*").eq("national_id", clean_nid).execute()
            
            if res.data:
                st.session_state.teacher = res.data[0]
                st.rerun()
            else:
                st.error("رقم السجل غير مسجل! تأكد من صحته أو رفعه من Colab.")
        else:
            st.warning("الرجاء إدخال رقم السجل أولاً")

# --- واجهة التحضير (بعد نجاح الدخول) ---
else:
    teacher = st.session_state.teacher
    st.sidebar.success(f"المعلم: {teacher['name']}")
    
    if st.sidebar.button("تسجيل الخروج"):
        del st.session_state.teacher
        st.rerun()

    st.title("📋 نافذة التحضير اليومي")
    
    try:
        # جلب قائمة اللجان المتاحة
        res_com = supabase.table("students").select("committee").execute()
        committees = sorted(list(set([str(row['committee']) for row in res_com.data])))
        
        selected_comm = st.selectbox("اختر اللجنة:", ["-- اختر اللجنة --"] + committees)
        
        if selected_comm != "-- اختر اللجنة --":
            # جلب طلاب اللجنة المختارة
            res_stu = supabase.table("students").select("*").eq("committee", selected_comm).execute()
            students = res_stu.data
            
            if students:
                with st.form("attendance_form"):
                    st.subheader(f"طلاب لجنة {selected_comm}")
                    results = {}
                    
                    for stu in students:
                        # عرض اسم الطالب وفصله في سطر واحد
                        col_info, col_status = st.columns([2, 1])
                        col_info.write(f"👤 **{stu['student_name']}**")
                        col_info.caption(f"الفصل: {stu['section']}")
                        
                        # خيارات التحضير
                        status = col_status.radio(
                            "الحالة", ["حاضر", "غائب", "متأخر"], 
                            key=f"s_{stu['id']}", 
                            horizontal=True, 
                            label_visibility="collapsed"
                        )
                        
                        results[stu['id']] = {
                            "name": stu['student_name'],
                            "section": stu['section'],
                            "status": status
                        }
                    
                    if st.form_submit_button("حفظ وإرسال الكشف"):
                        final_records = []
                        for sid, info in results.items():
                            final_records.append({
                                "student_name": info['name'],
                                "committee": selected_comm,
                                "section": info['section'],
                                "status": info['status'],
                                "teacher_name": teacher['name']
                            })
                        
                        # حفظ في جدول الغياب
                        supabase.table("attendance_records").insert(final_records).execute()
                        st.success(f"تم حفظ تحضير {len(final_records)} طالب بنجاح!")
            else:
                st.warning("لا يوجد طلاب مسجلين في هذه اللجنة.")
                
    except Exception as e:
        st.error(f"خطأ في جلب البيانات: {e}")
