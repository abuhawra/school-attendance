import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
import urllib.parse

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

st.set_page_config(page_title="نظام غياب الطلاب - أ. عارف الحداد", layout="wide")

def get_system_status():
    try:
        res = supabase.table("settings").select("is_open").eq("setting_name", "attendance_status").execute()
        return res.data[0]['is_open'] if res.data else True
    except: return True

st.sidebar.title("🏫 القائمة الرئيسية")
page = st.sidebar.radio("انتقل إلى:", ["🔑 دخول المعلم", "📊 لوحة الإدارة"])

# --- 1. واجهة المعلم ---
if page == "🔑 دخول المعلم":
    is_open = get_system_status()
    if not is_open:
        st.error("🚫 نظام رصد الغياب مغلق حالياً.")
    else:
        if not st.session_state.get('logged_in', False):
            st.header("🔑 تسجيل دخول المعلم")
            nid_input = st.text_input("أدخل رقم السجل المدني:", key="nid_login")
            if st.button("دخول"):
                res = supabase.table("teachers").select("*").eq("national_id", nid_input.strip()).execute()
                if res.data:
                    st.session_state.logged_in = True
                    st.session_state.teacher_name = res.data[0].get('name_tech', 'المعلم')
                    st.rerun()
                else: st.error("❌ السجل غير مسجل.")
        else:
            st.success(f"✅ مرحباً أستاذ: {st.session_state.teacher_name}")
            target_date = st.date_input("📅 تاريخ الرصد", datetime.now())
            s_data = supabase.table('students').select("committee").execute()
            all_comms = sorted(list(set([str(i['committee']) for i in s_data.data if i['committee']])), key=smart_sort)
            selected_comm = st.selectbox("🎯 اختر اللجنة:", ["---"] + all_comms)
            
            if selected_comm != "---":
                students = supabase.table('students').select("*").eq('committee', selected_comm).execute()
                old_att = supabase.table('attendance').select("*").eq('committee', selected_comm).eq('date', str(target_date)).execute()
                history = {r['student_name']: r['status'] for r in old_att.data}
                
                attendance_results = []
                for s in students.data:
                    prev = history.get(s['student_name'], "حاضر")
                    col1, col2 = st.columns([2, 1])
                    with col1: st.write(s['student_name'])
                    with col2: status = st.radio("الحالة", ["حاضر", "غائب", "متأخر"], index=["حاضر", "غائب", "متأخر"].index(prev), key=s['id'], horizontal=True)
                    attendance_results.append({"student_name": s['student_name'], "committee": selected_comm, "status": status, "date": str(target_date), "teacher_name": st.session_state.teacher_name})
                
                if st.button("💾 حفظ الكشف"):
                    supabase.table('attendance').delete().eq('committee', selected_comm).eq('date', str(target_date)).execute()
                    supabase.table('attendance').insert(attendance_results).execute()
                    st.success("✅ تم الحفظ!"); time.sleep(1); st.rerun()

# --- 2. لوحة الإدارة (الإصلاحات هنا) ---
elif page == "📊 لوحة الإدارة":
    st.header("📊 لوحة الإدارة والتقارير")
    if st.sidebar.text_input("كلمة المرور", type="password") == "1234":
        
        # التحكم في النظام
        status = get_system_status()
        if status:
            st.success("🟢 النظام الآن: مفتوح")
            if st.button("🔴 إغلاق الرصد"):
                supabase.table("settings").update({"is_open": False}).eq("setting_name", "attendance_status").execute()
                st.rerun()
        else:
            st.error("🔴 النظام الآن: مغلق")
            if st.button("🟢 تفعيل الرصد"):
                supabase.table("settings").update({"is_open": True}).eq("setting_name", "attendance_status").execute()
                st.rerun()

        st.divider()
        report_date = st.date_input("📅 تاريخ المتابعة", datetime.now())
        
        # جلب البيانات
        att_res = supabase.table('attendance').select("*").eq('date', str(report_date)).execute()
        std_res = supabase.table('students').select("student_name, section, committee").execute()
        
        tab1, tab2 = st.tabs(["⚠️ كشف الغياب التفصيلي", "🚩 حالة اللجان"])
        
        with tab1:
            if att_res.data:
                df_att = pd.DataFrame(att_res.data)
                df_std = pd.DataFrame(std_res.data)
                merged = pd.merge(df_att, df_std, on='student_name', how='left')
                
                # تصفية الغائبين والمتأخرين
                report_df = merged[merged['status'].isin(['غائب', 'متأخر'])][['student_name', 'section', 'committee_x', 'status']]
                report_df.columns = ['الاسم', 'الشعبة', 'اللجنة', 'الحالة']
                
                # --- إصلاح زر الواتساب التفصيلي ---
                wa_msg = f"*تقرير الغياب التفصيلي - {report_date}*\n\n"
                for _, row in report_df.iterrows():
                    wa_msg += f"👤 {row['الاسم']}\n🏢 الشعبة: {row['الشعبة']} | 🎯 اللجنة: {row['اللجنة']}\n🚩 الحالة: *{row['الحالة']}*\n"
                    wa_msg += "------------------\n"
                
                st.link_button("📱 إرسال الكشف التفصيلي عبر واتساب", f"https://wa.me/?text={urllib.parse.quote(wa_msg)}")
                st.table(report_df)
            else: st.info("لا توجد سجلات لهذا التاريخ.")

        with tab2:
            # --- إعادة إظهار تقرير اللجان التي رصدت/لم ترصد ---
            all_c = set([str(s['committee']) for s in std_res.data if s['committee']])
            done_c = set([str(a['committee']) for a in att_res.data])
            not_done = sorted(list(all_c - done_c), key=smart_sort)
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.success(f"✅ لجان رصدت ({len(done_c)}):")
                st.write(", ".join(sorted(list(done_c), key=smart_sort)))
            with col_b:
                st.error(f"❌ لجان لم ترصد ({len(not_done)}):")
                st.write(", ".join(not_done))
    else: st.info("أدخل كلمة المرور في القائمة الجانبية.")
