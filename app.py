import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime

# بيانات الاتصال بمشروعك
url = "https://lsmevvsogsqqqjyuqzbx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzbWV2dnNvZ3NxcXFqeXVxemJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MDMyOTgsImV4cCI6MjA5Mjk3OTI5OH0.ecqJS75fPbKqwSAiBzP6Qonn4cuymgwjB96tIGek8j0"

if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(url, key)
supabase = st.session_state.supabase

# حفظ حالة تسجيل الدخول لمنع الخروج المفاجئ
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'teacher_name' not in st.session_state:
    st.session_state.teacher_name = ""

st.set_page_config(page_title="نظام غياب الطلاب - أ. عارف الحداد", layout="wide")

st.sidebar.title("🏫 القائمة الرئيسية")
page = st.sidebar.radio("انتقل إلى:", ["🔑 دخول المعلم", "📊 لوحة الإدارة"])

if st.session_state.logged_in:
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.logged_in = False
        st.session_state.teacher_name = ""
        st.rerun()

if page == "🔑 دخول المعلم":
    if not st.session_state.logged_in:
        st.header("🔑 تسجيل دخول المعلم")
        nid_input = st.text_input("أدخل رقم السجل المدني:", type="default")
        if st.button("دخول"):
            if nid_input:
                res = supabase.table("teachers").select("*").eq("national_id", nid_input.strip()).execute()
                if res.data:
                    st.session_state.logged_in = True
                    st.session_state.teacher_name = res.data[0].get('name_tech', 'المعلم')
                    st.rerun()
                else:
                    st.error("❌ رقم السجل المدني غير موجود.")
    else:
        st.success(f"✅ مرحباً بك أستاذ: **{st.session_state.teacher_name}**")
        st.divider()
        target_date = st.date_input("📅 تاريخ اليوم", datetime.now())
        
        # جلب اللجان
        s_data = supabase.table('students').select("committee").execute()
        committees = sorted(list(set([item['committee'] for item in s_data.data if item['committee']])))
        selected_committee = st.selectbox("🎯 اختر اللجنة", ["اختر اللجنة..."] + committees)
        
        if selected_committee != "اختر اللجنة...":
            students_query = supabase.table('students').select("*").eq('committee', selected_committee).execute()
            if students_query.data:
                attendance_results = []
                st.write(f"### قائمة طلاب لجنة: {selected_committee}")
                for student in students_query.data:
                    col1, col2 = st.columns([2, 1])
                    with col1: st.write(f"👤 {student['student_name']}")
                    with col2:
                        status = st.radio("الحالة", ["حاضر", "غائب", "متأخر"], key=f"s_{student['id']}", horizontal=True)
                    attendance_results.append({
                        "student_name": student['student_name'],
                        "committee": selected_committee,
                        "status": status,
                        "date": str(target_date),
                        "teacher_name": st.session_state.teacher_name
                    })
                
                st.divider()
                if st.button("💾 إرسال كشف الغياب"):
                    if attendance_results:
                        try:
                            with st.spinner('جاري الحفظ في قاعدة البيانات...'):
                                supabase.table('attendance').insert(attendance_results).execute()
                                st.balloons()
                                st.success(f"✅ تم حفظ غياب {len(attendance_results)} طالب بنجاح!")
                        except Exception as e:
                            st.error("❌ فشل الحفظ. تأكد من مطابقة أسماء الأعمدة في Supabase.")
                            st.write(f"تفاصيل الخطأ: {e}")
                    else:
                        st.warning("لا توجد بيانات لإرسالها.")

elif page == "📊 لوحة الإدارة":
    st.header("⚙️ إدارة النظام والتقارير")
    password = st.sidebar.text_input("كلمة مرور الإدارة", type="password")
    if password == "1234":
        st.info("مرحباً بك في لوحة الإدارة.")
        report_date = st.date_input("اختر التاريخ لعرض الغياب", datetime.now())
        att_data = supabase.table('attendance').select("*").eq('date', str(report_date)).execute()
        if att_data.data:
            st.dataframe(pd.DataFrame(att_data.data), use_container_width=True)
        else:
            st.warning("لا توجد بيانات لهذا التاريخ.")
    else:
        st.info("أدخل كلمة المرور في القائمة الجانبية.")
