import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import io

# 1. إعدادات الاتصال بقاعدة البيانات
url = "https://lsmevvsogsqqqjyuqzbx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzbWV2dnNvZ3NxcXFqeXVxemJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MDMyOTgsImV4cCI6MjA5Mjk3OTI5OH0.ecqJS75fPbKqwSAiBzP6Qonn4cuymgwjB96tIGek8j0"

if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(url, key)
supabase = st.session_state.supabase

# --- 🎨 التنسيق والمظهر ---
st.set_page_config(page_title="نظام مدرسة القطيف التقني", layout="wide")
st.markdown('''
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .main-header { background-color: #1a237e; padding: 30px; text-align: center; color: white; border-radius: 20px; border-bottom: 8px solid #ffd700; margin-bottom: 25px; }
    .teacher-tag { background-color: #f0f2f6; color: #1a237e; padding: 6px 15px; border-radius: 20px; font-weight: bold; font-size: 14px; border: 1px solid #d1d9e6; margin-left: 5px; display: inline-block; }
    .arrow-sep { color: #1a237e; font-weight: bold; margin: 0 8px; font-size: 20px; }
    .wa-link { text-decoration: none; color: white !important; display: block; text-align: center; padding: 12px; border-radius: 10px; font-weight: bold; margin-bottom: 10px; }
    </style>
''', unsafe_allow_html=True)

if 'page' not in st.session_state:
    st.session_state.page = "home"

# --- 1. الصفحة الرئيسية ---
if st.session_state.page == "home":
    st.markdown('''
        <div class="main-header">
            <h2 style="color:#ffd700; font-size: 45px; font-weight: 800; margin-bottom:0;">بصمة تميز</h2>
            <h3 style="margin-top:10px; font-size: 24px;">مدرسة القطيف الثانوية</h3>
            <hr style="border: 0.5px solid rgba(255,255,255,0.2); width: 50%; margin: 20px auto;">
            <p style="font-size: 18px; opacity: 0.9;">مدير المدرسة: أ. فراس آل عبدالمحسن | برمجة: أ. عارف أحمد الحداد</p>
        </div>
    ''', unsafe_allow_html=True)
    
    col_b = st.columns([1, 2, 1])[1]
    with col_b:
        # زر الرصد مفتوح دائماً الآن
        if st.button("📝 رصد غياب الطلاب اليومي", use_container_width=True, type="primary"):
            st.session_state.page = "t_log"; st.rerun()
        
        st.write("")
        if st.button("⚙️ لوحة الإدارة والتقارير الموحدة", use_container_width=True):
            st.session_state.page = "a_log"; st.rerun()

# --- 2. تسجيل دخول المعلم ---
elif st.session_state.page == "t_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    tid = st.text_input("أدخل السجل المدني للمعلم:", type="password")
    if st.button("دخول للنظام"):
        res = supabase.table("teachers").select("*").eq("national_id", tid.strip()).execute()
        if res.data:
            st.session_state.teacher = res.data[0]['name_tech']
            st.session_state.page = "mark"; st.rerun()
        else: st.error("عذراً، السجل المدني غير مسجل.")

# --- 3. واجهة الرصد ---
elif st.session_state.page == "mark":
    today = str(datetime.now().date())
    st.info(f"المعلم الحالي: {st.session_state.teacher} | التاريخ: {today}")
    res_s = supabase.table('students').select("committee").execute()
    if res_s.data:
        coms = sorted(list(set([str(i['committee']) for i in res_s.data if i['committee']])), key=lambda x: int(x) if x.isdigit() else 0)
        sel_c = st.selectbox("اختر اللجنة:", ["---"] + coms)
        if sel_c != "---":
            students = supabase.table('students').select("*").eq("committee", sel_c).execute()
            old_att = supabase.table('attendance').select("*").eq("committee", sel_c).eq("date", today).execute()
            
            # منطق ترتيب المعلمين
            if old_att.data:
                prev_list = []
                for entry in old_att.data:
                    for n in entry.get('teacher_name', '').split(" | "):
                        if n.strip() and n.strip() not in prev_list: prev_list.append(n.strip())
                if st.session_state.teacher not in prev_list: prev_list.append(st.session_state.teacher)
                all_t = " | ".join(prev_list)
                old_map = {i['student_name']: i['status'] for i in old_att.data}
            else:
                all_t = st.session_state.teacher
                old_map = {}

            results = []
            for s in students.data:
                prev = old_map.get(s['student_name'], "حاضر")
                choice = st.radio(f"👤 {s['student_name']}", ["حاضر", "غائب", "متأخر"], index=["حاضر", "غائب", "متأخر"].index(prev), key=s['student_name'], horizontal=True)
                results.append({"student_name": s['student_name'], "committee": str(sel_c), "status": choice, "date": today, "teacher_name": all_t})
            
            if st.button("💾 حفظ الرصد النهائي", use_container_width=True):
                supabase.table('attendance').delete().eq("committee", sel_c).eq("date", today).execute()
                supabase.table('attendance').insert(results).execute()
                st.session_state.page = "thank_you"; st.rerun()

# --- 4. صفحة الشكر ---
elif st.session_state.page == "thank_you":
    st.snow()
    st.markdown('<div style="text-align:center; padding:50px;"><h1>✅ تم الحفظ بنجاح</h1><p>شكراً لتعاونكم أستاذنا الفاضل</p></div>', unsafe_allow_html=True)
    if st.button("🏠 العودة للرئيسية", use_container_width=True):
        st.session_state.page = "home"; st.rerun()

# --- 5. لوحة الإدارة ---
elif st.session_state.page == "a_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    if st.text_input("كلمة مرور الإدارة:", type="password") == "1234": 
        st.session_state.page = "admin"; st.rerun()

elif st.session_state.page == "admin":
    if st.button("⬅️ خروج من الإدارة"): st.session_state.page = "home"; st.rerun()
    tab1, tab2, tab3 = st.tabs(["📊 التقارير", "🏘️ حالة اللجان", "💾 إدارة البيانات"])
    
    with tab2:
        st.subheader("🏘️ حالة اللجان اليوم")
        att_today = supabase.table('attendance').select("committee, teacher_name").eq("date", str(datetime.now().date())).execute()
        comm_map = {}
        for row in att_today.data:
            c = str(row['committee'])
            if c not in comm_map:
                names = [n.strip() for n in row['teacher_name'].split(" | ") if n.strip()]
                seen = set()
                comm_map[c] = [x for x in names if not (x in seen or seen.add(x))]
        
        res_s = supabase.table('students').select("committee").execute()
        all_c = sorted(list(set([str(i['committee']) for i in res_s.data])), key=lambda x: int(x) if x.isdigit() else 0)
        for c in all_c:
            if c in comm_map:
                html = ""
                for i, n in enumerate(comm_map[c]):
                    html += f"<span class='teacher-tag'>{n}</span>"
                    if i < len(comm_map[c]) - 1: html += "<span class='arrow-sep'>⬅️</span>"
                st.markdown(f"📍 **لجنة {c}:** {html}", unsafe_allow_html=True)

    with tab3:
        if st.text_input("رمز الحماية:", type="password") == "4321":
            st.subheader("💾 النسخ الاحتياطي")
            res_std = supabase.table('students').select("*").execute()
            if res_std.data:
                df_s = pd.DataFrame(res_std.data)
                c1, c2 = st.columns(2)
                with c1: st.download_button("📥 تحميل CSV", df_s.to_csv(index=False).encode('utf-8-sig'), "backup.csv", use_container_width=True)
                with c2:
                    buf = io.BytesIO()
                    with pd.ExcelWriter(buf, engine='openpyxl') as wr: df_s.to_excel(wr, index=False)
                    st.download_button("📊 تحميل Excel", buf.getvalue(), "backup.xlsx", use_container_width=True)
