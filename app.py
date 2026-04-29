import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time

# بيانات الاتصال
url = "https://lsmevvsogsqqqjyuqzbx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzbWV2dnNvZ3NxcXFqeXVxemJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MDMyOTgsImV4cCI6MjA5Mjk3OTI5OH0.ecqJS75fPbKqwSAiBzP6Qonn4cuymgwjB96tIGek8j0"

if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(url, key)
supabase = st.session_state.supabase

def smart_sort(x):
    try: return int(x)
    except: return str(x)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'teacher_name' not in st.session_state:
    st.session_state.teacher_name = ""

st.set_page_config(page_title="نظام غياب الطلاب - أ. عارف الحداد", layout="wide")

# دالة لتحويل الجدول إلى HTML أنيق جاهز للطباعة (PDF)
def create_pdf_html(df, report_date):
    html_table = df.to_html(index=False, classes='report-table')
    html_content = f"""
    <div dir="rtl" style="font-family: Arial; padding: 20px; border: 2px solid #333;">
        <h2 style="text-align: center; color: #2c3e50;">كشف الغياب والتأخر اليومي</h2>
        <p style="text-align: center;"><b>التاريخ:</b> {report_date}</p>
        <hr>
        <style>
            .report-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            .report-table th, .report-table td {{ border: 1px solid #ddd; padding: 12px; text-align: center; }}
            .report-table th {{ background-color: #f2f2f2; color: #333; }}
            .report-table tr:nth-child(even) {{ background-color: #fafafa; }}
        </style>
        {html_table}
        <div style="margin-top: 30px; text-align: left;">
            <p>ختم الإدارة: ........................</p>
        </div>
    </div>
    """
    return html_content

def get_system_status():
    try:
        res = supabase.table("settings").select("is_open").eq("setting_name", "attendance_status").execute()
        if not res.data:
            supabase.table("settings").insert({"setting_name": "attendance_status", "is_open": True}).execute()
            return True
        return res.data[0]['is_open']
    except: return True

st.sidebar.title("🏫 القائمة الرئيسية")
page = st.sidebar.radio("انتقل إلى:", ["🔑 دخول المعلم", "📊 لوحة الإدارة"])

# --- 1. واجهة المعلم ---
if page == "🔑 دخول المعلم":
    is_open = get_system_status()
    if not is_open:
        st.error("🚫 نظام رصد الغياب مغلق حالياً من قبل الإدارة.")
    else:
        if not st.session_state.logged_in:
            st.header("🔑 تسجيل دخول المعلم")
            nid_input = st.text_input("أدخل رقم السجل المدني:")
            if st.button("دخول"):
                res = supabase.table("teachers").select("*").eq("national_id", nid_input.strip()).execute()
                if res.data:
                    st.session_state.logged_in = True
                    st.session_state.teacher_name = res.data[0].get('name_tech', 'المعلم')
                    st.rerun()
                else: st.error("❌ رقم السجل المدني غير موجود.")
        else:
            st.success(f"✅ مرحباً بك أستاذ: **{st.session_state.teacher_name}**")
            target_date = st.date_input("📅 تاريخ الرصد", datetime.now())
            s_data = supabase.table('students').select("committee").execute()
            sorted_committees = sorted(list(set([i['committee'] for i in s_data.data if i['committee']])), key=smart_sort)
            selected_committee = st.selectbox("🎯 اختر اللجنة", ["اختر اللجنة..."] + sorted_committees)
            
            if selected_committee != "اختر اللجنة...":
                students_query = supabase.table('students').select("*").eq('committee', selected_committee).execute()
                old_att = supabase.table('attendance').select("student_name, status").eq('committee', selected_committee).eq('date', str(target_date)).execute()
                history = {row['student_name']: row['status'] for row in old_att.data}
                
                attendance_results = []
                for student in students_query.data:
                    s_name = student['student_name']
                    prev_status = history.get(s_name, "حاضر")
                    options = ["حاضر", "غائب", "متأخر"]
                    col1, col2 = st.columns([2, 1])
                    with col1: st.write(f"👤 {s_name}")
                    with col2: status = st.radio("الحالة", options, index=options.index(prev_status), key=f"s_{student['id']}", horizontal=True)
                    attendance_results.append({"student_name": s_name, "committee": selected_committee, "status": status, "date": str(target_date), "teacher_name": st.session_state.teacher_name})
                
                if st.button("💾 حفظ التعديلات وإرسال الكشف"):
                    try:
                        supabase.table('attendance').delete().eq('committee', selected_committee).eq('date', str(target_date)).execute()
                        supabase.table('attendance').insert(attendance_results).execute()
                        st.balloons(); st.success("✅ تم الحفظ بنجاح!"); time.sleep(1); st.session_state.logged_in = False; st.rerun()
                    except Exception as e: st.error(f"خطأ: {e}")

# --- 2. لوحة الإدارة ---
elif page == "📊 لوحة الإدارة":
    st.header("📊 لوحة الإدارة والتقارير")
    if st.sidebar.text_input("كلمة المرور", type="password") == "1234":
        current_status = get_system_status()
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if current_status:
                st.success("🟢 النظام الآن: مفتوح")
                if st.button("🔴 إيقاف الرصد"):
                    supabase.table("settings").update({"is_open": False}).eq("setting_name", "attendance_status").execute()
                    st.rerun()
            else:
                st.error("🔴 النظام الآن: مغلق")
                if st.button("🟢 تفعيل الرصد"):
                    supabase.table("settings").update({"is_open": True}).eq("setting_name", "attendance_status").execute()
                    st.rerun()

        st.divider()
        col_date, col_reset = st.columns([2, 1])
        with col_date:
            report_date = st.date_input("📅 تاريخ المتابعة / المسح", datetime.now())
        
        with col_reset:
            if st.button("⚠️ مسح غياب هذا التاريخ", use_container_width=True):
                try:
                    supabase.table('attendance').delete().eq('date', str(report_date)).execute()
                    st.success(f"🗑️ تم المسح بنجاح."); time.sleep(1); st.rerun() 
                except Exception as e: st.error(f"حدث خطأ: {e}")

        st.divider()
        att_res = supabase.table('attendance').select("*").eq('date', str(report_date)).execute()
        
        tab1, tab2 = st.tabs(["⚠️ كشف الغياب/التأخر", "🚩 حالة اللجان"])
        
        with tab1:
            if att_res.data:
                df = pd.DataFrame(att_res.data).rename(columns={'student_name':'الاسم','committee':'اللجنة','status':'الحالة','teacher_name':'المعلم'})
                report_df = df[df['الحالة'].isin(['غائب','متأخر'])][['الاسم','اللجنة','الحالة','المعلم']]
                
                if not report_df.empty:
                    st.table(report_df)
                    
                    # --- ميزة تصدير PDF/صورة ---
                    col_pdf, col_csv = st.columns(2)
                    with col_pdf:
                        # إنشاء زر يقوم بفتح نافذة الطباعة
                        if st.button("📄 تصدير الكشف كـ PDF (جاهز للطباعة)"):
                            report_html = create_pdf_html(report_df, report_date)
                            st.markdown(report_html, unsafe_allow_html=True)
                            st.info("⬆️ يظهر الكشف أعلاه بشكل رسمي. اضغط (Ctrl + P) أو 'طباعة' من الجوال لحفظه كـ PDF فوراً.")
                    
                    with col_csv:
                        csv = report_df.to_csv(index=False).encode('utf-8-sig')
                        st.download_button(label="📥 تحميل كملف Excel", data=csv, file_name=f"غياب_{report_date}.csv")
                else: st.success("الكل حاضر لهذا اليوم!")
            else: st.info("لا توجد سجلات غياب لهذا التاريخ.")
            
        with tab2:
            all_std = supabase.table('students').select("committee").execute()
            all_comm = set([i['committee'] for i in all_std.data if i['committee']])
            submitted = set(row['committee'] for row in att_res.data) if att_res.data else set()
            not_submitted = all_comm - submitted
            col1, col2 = st.columns(2)
            with col1: st.success(f"✅ رصدت: {', '.join(map(str, sorted(list(submitted), key=smart_sort)))}")
            with col2: st.error(f"❌ لم ترصد: {', '.join(map(str, sorted(list(not_submitted), key=smart_sort)))}")
    else: st.sidebar.info("أدخل كلمة المرور.")
