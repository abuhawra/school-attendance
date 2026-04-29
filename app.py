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

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'teacher_name' not in st.session_state:
    st.session_state.teacher_name = ""

st.set_page_config(page_title="نظام غياب الطلاب - أ. عارف الحداد", layout="wide")

def check_system_status():
    try:
        res = supabase.table("settings").select("is_open").eq("setting_name", "attendance_status").execute()
        return res.data[0]['is_open'] if res.data else True
    except: return True

st.sidebar.title("🏫 القائمة الرئيسية")
page = st.sidebar.radio("انتقل إلى:", ["🔑 دخول المعلم", "📊 لوحة الإدارة"])

# --- 1. واجهة المعلم (مع ميزة استرجاع البيانات للتعديل) ---
if page == "🔑 دخول المعلم":
    is_open = check_system_status()
    if not is_open:
        st.error("🚫 نظام رصد الغياب مغلق حالياً من قبل الإدارة.")
    else:
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
                    else: st.error("❌ رقم السجل المدني غير موجود.")
        else:
            st.success(f"✅ مرحباً بك أستاذ: **{st.session_state.teacher_name}**")
            st.divider()
            target_date = st.date_input("📅 تاريخ الرصد", datetime.now())
            
            s_data = supabase.table('students').select("committee").execute()
            committees = sorted(list(set([item['committee'] for item in s_data.data if item['committee']])))
            selected_committee = st.selectbox("🎯 اختر اللجنة", ["اختر اللجنة..."] + committees)
            
            if selected_committee != "اختر اللجنة...":
                # جلب الطلاب وجلب الحالات المرصودة سابقاً اليوم
                students_query = supabase.table('students').select("*").eq('committee', selected_committee).execute()
                old_att_query = supabase.table('attendance').select("student_name, status").eq('committee', selected_committee).eq('date', str(target_date)).execute()
                
                # تحويل الحالات القديمة لقاموس لسهولة البحث: { 'اسم الطالب': 'الحالة' }
                history = {row['student_name']: row['status'] for row in old_att_query.data}
                
                if students_query.data:
                    attendance_results = []
                    st.info("💡 يتم عرض الحالات التي رُصدت سابقاً (إن وجدت). يمكنك التعديل ثم الحفظ.")
                    
                    for student in students_query.data:
                        s_name = student['student_name']
                        # تحديد الحالة الافتراضية: إذا كان مسجلاً سابقاً نضع حالته، وإلا نضعه "حاضر"
                        prev_status = history.get(s_name, "حاضر")
                        options = ["حاضر", "غائب", "متأخر"]
                        default_index = options.index(prev_status)
                        
                        col1, col2 = st.columns([2, 1])
                        with col1: st.write(f"👤 {s_name}")
                        with col2:
                            status = st.radio("الحالة", options, index=default_index, key=f"s_{student['id']}", horizontal=True)
                        
                        attendance_results.append({
                            "student_name": s_name, "committee": selected_committee,
                            "status": status, "date": str(target_date), "teacher_name": st.session_state.teacher_name
                        })
                    
                    if st.button("💾 حفظ التعديلات وإرسال الكشف"):
                        try:
                            # حذف القديم لنفس اللجنة والتاريخ ثم إدخال الجديد
                            supabase.table('attendance').delete().eq('committee', selected_committee).eq('date', str(target_date)).execute()
                            supabase.table('attendance').insert(attendance_results).execute()
                            st.balloons()
                            st.success("✅ تم تحديث ورصد الغياب بنجاح!")
                            time.sleep(2)
                            st.session_state.logged_in = False
                            st.rerun()
                        except Exception as e: st.error(f"خطأ في الحفظ: {e}")

# --- 2. لوحة الإدارة ---
elif page == "📊 لوحة الإدارة":
    st.header("📊 لوحة الإدارة")
    password = st.sidebar.text_input("كلمة مرور الإدارة", type="password")
    if password == "1234":
        # نظام التحكم
        current_status = check_system_status()
        st.subheader("⚙️ إعدادات النظام")
        if st.button("إغلاق النظام" if current_status else "فتح النظام"):
            supabase.table("settings").update({"is_open": not current_status}).eq("setting_name", "attendance_status").execute()
            st.rerun()
        
        st.divider()
        # التقارير
        report_date = st.date_input("📅 تاريخ المتابعة", datetime.now())
        att_res = supabase.table('attendance').select("*").eq('date', str(report_date)).execute()
        if att_res.data:
            df = pd.DataFrame(att_res.data).rename(columns={'student_name':'الاسم','committee':'اللجنة','status':'الحالة','teacher_name':'المعلم'})
            tab1, tab2 = st.tabs(["⚠️ كشف الغياب/التأخر", "🚩 حالة اللجان"])
            with tab1: st.table(df[df['الحالة'].isin(['غائب','متأخر'])][['الاسم','اللجنة','الحالة','المعلم']])
            with tab2: st.write("✅ اللجان التي رصدت:", list(df['اللجنة'].unique()))
        else: st.warning("لا توجد بيانات.")
    else: st.info("أدخل كلمة المرور.")
