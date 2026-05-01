import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
import io
import urllib.parse

# 1. إعدادات الاتصال بقاعدة البيانات
url = "https://lsmevvsogsqqqjyuqzbx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzbWV2dnNvZ3NxcXFqeXVxemJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MDMyOTgsImV4cCI6MjA5Mjk3OTI5OH0.ecqJS75fPbKqwSAiBzP6Qonn4cuymgwjB96tIGek8j0"

if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(url, key)
supabase = st.session_state.supabase

# --- 🎨 منطقة التنسيق (CSS & HTML) ---
STYLE_CSS = '''
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .stButton>button { border-radius: 10px; font-weight: bold; height: 50px; width: 100%; font-size: 18px; }
    .wa-link { text-decoration: none; color: white !important; display: block; text-align: center; padding: 12px; border-radius: 10px; font-weight: bold; margin-bottom: 10px; }
    .wa-absent { background-color: #dc3545; }
    .wa-late { background-color: #fd7e14; }
    th { background-color: #1a237e !important; color: white !important; text-align: center !important; }
    td { text-align: center !important; }
    </style>
'''

HEADER_HTML = '''
    <div style="background-color: #1a237e; padding: 40px 20px; text-align: center; color: white; border-bottom: 8px solid #ffd700; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); margin-bottom: 30px;">
        <div style="font-size: 38px; font-weight: 800; margin-bottom: 5px;">التحضير التقني</div>
        <div style="font-size: 34px; font-weight: 700; margin-bottom: 20px;">مدرسة القطيف الثانوية</div>
        <div style="margin: 25px 0; border-top: 1px solid rgba(255,255,255,0.2); width: 50%; margin-left: auto; margin-right: auto;"></div> 
        <div style="font-size: 22px; font-weight: 500; color: #cfd8dc; margin-bottom: 5px;">فكرة وبرمجة</div>
        <div style="font-size: 32px; font-weight: 700; color: #ffd700; margin-bottom: 25px;">أ. عارف أحمد الحداد</div>
        <div style="font-size: 20px; font-weight: 500; color: #cfd8dc; margin-bottom: 5px;">مدير المدرسة</div>
        <div style="font-size: 26px; font-weight: 600; color: #ffffff;">أ. فراس آل عبدالمحسن</div>
    </div>
'''

# 2. تطبيق الإعدادات الأساسية
st.set_page_config(page_title="نظام مدرسة القطيف التقني", layout="wide")
st.markdown(STYLE_CSS, unsafe_allow_html=True)

# تأمين تعريف الصفحة عند أول تشغيل
if 'page' not in st.session_state:
    st.session_state.page = "home"

# --- 🛠️ دالة بناء روابط الواتساب ---
def get_wa_link(df, status_type, d):
    if df.empty: return None
    emoji = "🔴" if status_type == "غائب" else "⏳"
    msg = f"*{emoji} قائمة {status_type}*\n📅 *التاريخ:* {d}\n" + "---------------------------\n"
    for _, r in df.iterrows():
        msg += f"📦 لجنة: {r['committee']}\n👤 الطالب: {r['student_name']}\n🏫 الشعبة: {r.get('الشعبة','--')}\n" + "---------------------------\n"
    return f"https://wa.me/?text={urllib.parse.quote(msg)}"

# --- 🏠 الصفحة الرئيسية ---
if st.session_state.page == "home":
    st.markdown(HEADER_HTML, unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns([1, 1.5, 1])
    with col_b:
        if st.button("📝 رصد غياب الطلاب اليومي", type="primary"): 
            st.session_state.page = "t_log"; st.rerun()
        st.write("")
        if st.button("⚙️ لوحة الإدارة والتقارير الموحدة"): 
            st.session_state.page = "a_log"; st.rerun()

# --- 📝 دخول المعلم ---
elif st.session_state.page == "t_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    tid = st.text_input("أدخل السجل المدني:", type="password")
    if st.button("دخول"):
        res = supabase.table("teachers").select("*").eq("national_id", tid.strip()).execute()
        if res.data:
            st.session_state.teacher = res.data[0]['name_tech']
            st.session_state.page = "mark"; st.rerun()
        else: st.error("السجل غير مسجل.")

# --- 🖊️ رصد الحضور ---
elif st.session_state.page == "mark":
    today = str(datetime.now().date())
    st.info(f"المعلم: {st.session_state.teacher} | التاريخ: {today}")
    res_s = supabase.table('students').select("committee").execute()
    if res_s.data:
        coms = sorted(list(set([str(i['committee']) for i in res_s.data if i['committee']])), key=lambda x: int(x) if x.isdigit() else 0)
        sel_c = st.selectbox("اختر اللجنة:", ["---"] + coms)
        if sel_c != "---":
            students = supabase.table('students').select("*").eq("committee", sel_c).execute()
            old_att = supabase.table('attendance').select("*").eq("committee", sel_c).eq("date", today).execute()
            old_map = {i['student_name']: i['status'] for i in old_att.data}
            results = []
            for s in students.data:
                prev = old_map.get(s['student_name'], "حاضر")
                choice = st.radio(f"👤 {s['student_name']}", ["حاضر", "غائب", "متأخر"], index=["حاضر", "غائب", "متأخر"].index(prev), key=s['student_name'], horizontal=True)
                results.append({"student_name": s['student_name'], "committee": str(sel_c), "status": choice, "date": today, "teacher_name": st.session_state.teacher})
            if st.button("💾 حفظ البيانات"):
                supabase.table('attendance').delete().eq("committee", sel_c).eq("date", today).execute()
                supabase.table('attendance').insert(results).execute()
                st.success("تم الحفظ بنجاح!"); time.sleep(1); st.session_state.page = "home"; st.rerun()

# --- 🔐 دخول الإدارة ---
elif st.session_state.page == "a_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    if st.text_input("كلمة مرور الإدارة:", type="password") == "1234": 
        st.session_state.page = "admin"; st.rerun()

# --- ⚙️ لوحة الإدارة (التقارير وحالة اللجان) ---
elif st.session_state.page == "admin":
    if st.button("⬅️ تسجيل خروج"): st.session_state.page = "home"; st.rerun()
    tab1, tab2, tab3 = st.tabs(["📊 التقارير وواتساب", "🏘️ حالة اللجان", "💾 إدارة البيانات"])
    
    with tab1:
        d = st.date_input("اختر تاريخ التقرير:", datetime.now())
        res_att = supabase.table("attendance").select("*").eq("date", str(d)).execute()
        if res_att.data:
            df_all = pd.DataFrame(res_att.data)
            res_std = supabase.table("students").select("student_name, class_name").execute()
            s_map = dict(zip([i['student_name'] for i in res_std.data], [i['class_name'] for i in res_std.data]))
            df_all['الشعبة'] = df_all['student_name'].map(s_map).fillna("---")
            
            st.dataframe(df_all[df_all['status'].isin(['غائب', 'متأخر'])][['committee', 'student_name', 'الشعبة', 'status']], use_container_width=True)
            
            c1, c2 = st.columns(2)
            with c1:
                link_abs = get_wa_link(df_all[df_all['status'] == "غائب"], "غائبين", d)
                if link_abs: st.markdown(f'<a href="{link_abs}" target="_blank" class="wa-link wa-absent">🚫 إرسال الغائبين</a>', unsafe_allow_html=True)
            with c2:
                link_late = get_wa_link(df_all[df_all['status'] == "متأخر"], "متأخرين", d)
                if link_late: st.markdown(f'<a href="{link_late}" target="_blank" class="wa-link wa-late">⏳ إرسال المتأخرين</a>', unsafe_allow_html=True)

    with tab2:
        st.subheader("🏘️ متابعة رصد اللجان")
        att_today = supabase.table('attendance').select("committee, teacher_name").eq("date", str(datetime.now().date())).execute()
        done_dict = {str(i['committee']): i['teacher_name'] for i in att_today.data}
        res_s = supabase.table('students').select("committee").execute()
        all_c = sorted(list(set([str(i['committee']) for i in res_s.data])), key=lambda x: int(x) if x.isdigit() else 0)
        
        col1, col2 = st.columns(2)
        with col1:
            st.success("✅ رُصدت")
            for c in all_c:
                if c in done_dict: st.write(f"📍 لجنة {c} (بواسطة: {done_dict[c]})")
        with col2:
            st.error("❌ لم تُرصد")
            for c in all_c:
                if c not in done_dict: st.write(f"⚠️ لجنة {c}")
