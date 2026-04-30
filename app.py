import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time

# 1. إعدادات الاتصال
url = "https://lsmevvsogsqqqjyuqzbx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzbWV2dnNvZ3NxcXFqeXVxemJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MDMyOTgsImV4cCI6MjA5Mjk3OTI5OH0.ecqJS75fPbKqwSAiBzP6Qonn4cuymgwjB96tIGek8j0"

if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(url, key)
supabase = st.session_state.supabase

# 2. الواجهة والتنسيق
st.set_page_config(page_title="نظام مدرسة القطيف", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; direction: rtl; }
    .main-title { font-size: 30px; font-weight: 800; color: #1a237e; text-align: center; }
    .whatsapp-btn { background-color: #25D366; color: white; padding: 18px; border-radius: 12px; text-align: center; text-decoration: none; display: block; font-weight: bold; margin: 10px auto; max-width: 500px; font-size: 20px; border: 1px solid #128C7E; }
    div.stButton > button { width: 100%; max-width: 400px; height: 50px; border-radius: 12px; font-weight: bold; margin: 10px auto; display: block; }
    .status-box { padding: 15px; border-radius: 10px; margin: 10px 0; text-align: center; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

if 'page' not in st.session_state: st.session_state.page = "home"

# --- الصفحة الرئيسية ---
if st.session_state.page == "home":
    st.markdown('<p class="main-title">التحضير التقني لمدرسة القطيف الثانوية</p>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center;">بإشراف أ. عارف الحداد | مدير المدرسة أ. فراس آل عبدالمحسن</p><hr>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📝 دخول المعلمين للرصد", type="primary"): st.session_state.page = "att_login"; st.rerun()
        if st.button("⚙️ لوحة الإدارة والتقارير", type="secondary"): st.session_state.page = "admin_login"; st.rerun()

# --- رصد الحضور ---
elif st.session_state.page == "att_login":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    t_id = st.text_input("أدخل رقم السجل المدني:", type="password")
    if st.button("دخول"):
        res = supabase.table("teachers").select("*").eq("national_id", t_id.strip()).execute()
        if res.data:
            st.session_state.teacher_name = res.data[0]['name_tech']
            st.session_state.page = "taking_attendance"; st.rerun()
        else: st.error("السجل غير مسجل")

elif st.session_state.page == "taking_attendance":
    today = str(datetime.now().date())
    st.info(f"المعلم: {st.session_state.teacher_name} | التاريخ: {today}")
    s_data = supabase.table('students').select("committee").execute()
    coms = sorted(list(set([str(i['committee']) for i in s_data.data if i['committee']])), key=lambda x: int(x) if x.isdigit() else 0)
    sel_c = st.selectbox("اختر اللجنة للرصد:", ["---"] + coms)
    if sel_c != "---":
        students = supabase.table('students').select("*").eq('committee', sel_c).execute()
        results = []
        for s in students.data:
            stat = st.radio(f"👤 {s['student_name']}", ["حاضر", "غائب", "متأخر"], key=f"std_{s['id']}", horizontal=True)
            results.append({"student_name": s['student_name'], "committee": str(sel_c), "status": stat, "date": today, "teacher_name": st.session_state.teacher_name})
        if st.button("💾 حفظ الكشف"):
            supabase.table('attendance').delete().eq('committee', sel_c).eq('date', today).execute()
            supabase.table('attendance').insert(results).execute()
            st.success("تم الحفظ بنجاح"); time.sleep(1); st.session_state.page = "home"; st.rerun()

# --- لوحة الإدارة (المتابعة والتقارير) ---
elif st.session_state.page == "admin_login":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    if st.text_input("رمز الدخول:", type="password") == "1234": st.session_state.page = "admin_panel"; st.rerun()

elif st.session_state.page == "admin_panel":
    if st.button("⬅️ خروج"): st.session_state.page = "home"; st.rerun()
    tab1, tab2 = st.tabs(["📊 تقرير الغياب الموحد", "🏘️ متابعة حالة اللجان"])
    
    today_date = str(datetime.now().date())
    
    with tab1:
        d = st.date_input("تاريخ التقرير", datetime.now())
        res = supabase.table("attendance").select("*").eq("date", str(d)).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df_abs = df[df['status'].isin(['غائب', 'متأخر'])].copy()
            if not df_abs.empty:
                df_abs['committee_num'] = pd.to_numeric(df_abs['committee'], errors='coerce')
                df_abs = df_abs.sort_values(by='committee_num')
                
                # جلب الشعبة للعرض فقط
                ch_list = []
                for n in df_abs['student_name']:
                    si = supabase.table('students').select("class_name").eq("student_name", n).execute()
                    ch_list.append(si.data[0]['class_name'] if si.data else "---")
                df_abs['الشعبة'] = ch_list

                st.subheader(f"📋 تقرير الحالات ليوم {d}")
                disp = df_abs[['committee', 'student_name', 'الشعبة', 'status', 'teacher_name']].copy()
                disp.columns = ['اللجنة', 'الاسم', 'الشعبة', 'الحالة', 'المعلم']
                st.table(disp)
                
                msg = f"🗓️ *تقرير مدرسة القطيف*%0A📅 *التاريخ:* {d}%0A"
                for _, r in df_abs.iterrows():
                    msg += f"📦 *لجنة:* {r['committee']} | 🏫 *شعبة:* {r['الشعبة']}%0A👤 *الاسم:* {r['student_name']} ({r['status']})%0A"
                st.markdown(f'<a href="https://wa.me/?text={msg}" target="_blank" class="whatsapp-btn">إرسال التقرير الموحد 📲</a>', unsafe_allow_html=True)
            else: st.success("لا يوجد غياب")

    with tab2:
        st.subheader(f"🏘️ حالة اللجان لتاريخ: {today_date}")
        # جلب كل اللجان المتاحة
        all_s = supabase.table('students').select("committee").execute()
        all_coms = sorted(list(set([str(i['committee']) for i in all_s.data if i['committee']])), key=lambda x: int(x) if x.isdigit() else 0)
        
        # جلب اللجان التي رصدت فعلياً اليوم
        done_res = supabase.table('attendance').select("committee, teacher_name").eq("date", today_date).execute()
        done_dict = {str(i['committee']): i['teacher_name'] for i in done_res.data}
        
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.markdown('<div class="status-box" style="background-color:#d4edda; color:#155724;">✅ لجان تم رصدها</div>', unsafe_allow_html=True)
            if done_dict:
                for c, t in done_dict.items():
                    st.write(f"📍 لجنة **{c}** - المعلم: {t}")
            else: st.write("لم يتم رصد أي لجنة بعد")
            
        with col_r2:
            st.markdown('<div class="status-box" style="background-color:#f8d7da; color:#721c24;">❌ لجان لم ترصد بعد</div>', unsafe_allow_html=True)
            missing = [c for c in all_coms if c not in done_dict]
            if missing:
                for c in missing:
                    st.write(f"⚠️ لجنة رقم: **{c}**")
            else: st.success("اكتمل رصد جميع اللجان!")
