import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time

# 1. بيانات الاتصال
url = "https://lsmevvsogsqqqjyuqzbx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzbWV2dnNvZ3NxcXFqeXVxemJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MDMyOTgsImV4cCI6MjA5Mjk3OTI5OH0.ecqJS75fPbKqwSAiBzP6Qonn4cuymgwjB96tIGek8j0"

if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(url, key)
supabase = st.session_state.supabase

# حفظ حالة تسجيل الدخول
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'teacher_name' not in st.session_state:
    st.session_state.teacher_name = ""

st.set_page_config(page_title="نظام غياب الطلاب - أ. عارف الحداد", layout="wide")

st.sidebar.title("🏫 القائمة الرئيسية")
page = st.sidebar.radio("انتقل إلى:", ["🔑 دخول المعلم", "📊 لوحة الإدارة"])

# زر خروج يدوي في القائمة الجانبية
if st.session_state.logged_in:
    if st.sidebar.button("تسجيل الخروج اليدوي"):
        st.session_state.logged_in = False
        st.session_state.teacher_name = ""
        st.rerun()

# --- 1. واجهة المعلم ---
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
                        "student_name": student['student_name'], "committee": selected_committee,
                        "status": status, "date": str(target_date), "teacher_name": st.session_state.teacher_name
                    })
                
                st.divider()
                # التعديل المطلوب: الحفظ ثم الخروج التلقائي
                if st.button("💾 إرسال كشف الغياب (حفظ وخروج)"):
                    try:
                        with st.spinner('جاري الحفظ وتسجيل الخروج...'):
                            supabase.table('attendance').insert(attendance_results).execute()
                            st.balloons()
                            st.success("✅ تم الحفظ بنجاح! سيتم تسجيل خروجك الآن...")
                            
                            # تأخير بسيط ليتمكن المعلم من رؤية رسالة النجاح
                            time.sleep(2)
                            
                            # مسح بيانات الجلسة (الخروج)
                            st.session_state.logged_in = False
                            st.session_state.teacher_name = ""
                            st.rerun()
                    except Exception as e:
                        st.error(f"حدث خطأ أثناء الحفظ: {e}")

# --- 2. لوحة الإدارة ---
elif page == "📊 لوحة الإدارة":
    st.header("📊 لوحة الإدارة والتقارير")
    password = st.sidebar.text_input("كلمة مرور الإدارة", type="password")
    if password == "1234":
        report_date = st.date_input("📅 اختر التاريخ للمتابعة", datetime.now())
        att_res = supabase.table('attendance').select("*").eq('date', str(report_date)).execute()
        all_std_res = supabase.table('students').select("committee").execute()
        
        if att_res.data:
            df = pd.DataFrame(att_res.data)
            tab1, tab2 = st.tabs(["⚠️ الغائبين والمتأخرين", "🚩 حالة اللجان"])
            with tab1:
                absent_df = df[df['status'].isin(['غائب', 'متأخر'])]
                st.table(absent_df[['student_name', 'committee', 'status', 'teacher_name']])
            with tab2:
                submitted = set(df['committee'].unique())
                all_comm = set([item['committee'] for item in all_std_res.data if item['committee']])
                st.write("🟢 لجان مكتملة:", sorted(list(submitted)))
                st.write("🔴 لجان متبقية:", sorted(list(all_comm - submitted)))
        else:
            st.warning("لا توجد بيانات لهذا التاريخ.")
    else:
        st.info("أدخل كلمة المرور في الجانب.")
