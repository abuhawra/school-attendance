import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
import io

# 1. الاتصال بقاعدة البيانات
url = "https://lsmevvsogsqqqjyuqzbx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzbWV2dnNvZ3NxcXFqeXVxemJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MDMyOTgsImV4cCI6MjA5Mjk3OTI5OH0.ecqJS75fPbKqwSAiBzP6Qonn4cuymgwjB96tIGek8j0"

if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(url, key)
supabase = st.session_state.supabase

# 2. الواجهة الكلاسيكية المحسنة
st.set_page_config(page_title="التحضير التقني - مدرسة القطيف", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; background-color: #f8f9fa; }
    .header-box {
        background-color: #1a237e; color: white; padding: 40px; border-radius: 15px;
        text-align: center; border-bottom: 6px solid #ffd700; box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .hr-center { border: 0; height: 1px; background: rgba(255,255,255,0.3); width: 35%; margin: 25px auto; }
    .stButton>button { border-radius: 10px; font-weight: bold; height: 50px; width: 100%; }
    .whatsapp-btn { background-color: #25D366; color: white; padding: 12px; border-radius: 8px; text-align: center; display: block; text-decoration: none; font-weight: bold; }
    th { background-color: #1a237e !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

if 'page' not in st.session_state: st.session_state.page = "home"

# --- 🏠 الصفحة الرئيسية ---
if st.session_state.page == "home":
    st.markdown("""
        <div class="header-box">
            <h1 style="margin:0; font-size:36px;">التحضير التقني</h1>
            <h2 style="margin:5px 0 0 0; font-size:28px; opacity:0.9;">مدرسة القطيف الثانوية</h2>
            <div class="hr-center"></div>
            <p style="margin:0; color:#ffd700; font-size:18px;">فكرة وبرمجة</p>
            <p style="margin:0 0 20px 0; font-size:24px; font-weight:bold;">أ. عارف أحمد الحداد</p>
            <p style="margin:0; color:#cfd8dc; font-size:18px;">مدير المدرسة</p>
            <p style="margin:0; font-size:22px; font-weight:bold;">أ. فراس عبدالله آل عبد المحسن</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.write(" ")
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        if st.button("📝 رصد غياب الطلاب", type="primary"): st.session_state.page = "login_t"; st.rerun()
        if st.button("⚙️ لوحة الإدارة والتقارير"): st.session_state.page = "login_a"; st.rerun()

# --- 🔐 دخول المعلمين ---
elif st.session_state.page == "login_t":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    tid = st.text_input("أدخل رقم السجل المدني:", type="password")
    if st.button("دخول"):
        res = supabase.table("teachers").select("*").eq("national_id", tid.strip()).execute()
        if res.data:
            st.session_state.t_name = res.data[0]['name_tech']
            st.session_state.page = "marking"; st.rerun()
        else: st.error("السجل غير مسجل")

elif st.session_state.page == "marking":
    today = str(datetime.now().date())
    st.info(f"المعلم: {st.session_state.t_name} | التاريخ: {today}")
    
    # جلب اللجان
    all_s = supabase.table('students').select("committee").execute()
    coms = sorted(list(set([str(i['committee']) for i in all_s.data if i['committee']])), key=lambda x: int(x) if x.isdigit() else 0)
    
    sel_c = st.selectbox("اختر اللجنة:", ["---"] + coms)
    if sel_c != "---":
        st.subheader(f"رصد اللجنة {sel_c}")
        st_list = supabase.table('students').select("*").eq("committee", sel_c).execute()
        
        # جلب الحالات السابقة لتثبيتها
        old = supabase.table('attendance').select("student_name, status").eq("committee", sel_c).eq("date", today).execute()
        old_m = {i['student_name']: i['status'] for i in old.data}
        
        results = []
        for s in st_list.data:
            prev = old_m.get(s['student_name'], "حاضر")
            choice = st.radio(f"👤 {s['student_name']}", ["حاضر", "غائب", "متأخر"], 
                              index=["حاضر", "غائب", "متأخر"].index(prev), key=s['id'], horizontal=True)
            results.append({"student_name": s['student_name'], "committee": str(sel_c), "status": choice, "date": today, "teacher_name": st.session_state.t_name})
        
        if st.button("💾 حفظ البيانات"):
            supabase.table('attendance').delete().eq("committee", sel_c).eq("date", today).execute()
            supabase.table('attendance').insert(results).execute()
            st.success("تم الحفظ بنجاح"); time.sleep(1); st.session_state.page = "home"; st.rerun()

# --- ⚙️ لوحة الإدارة ---
elif st.session_state.page == "login_a":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    if st.text_input("رمز الإدارة:", type="password") == "1234": st.session_state.page = "admin"; st.rerun()

elif st.session_state.page == "admin":
    if st.button("⬅️ تسجيل خروج"): st.session_state.page = "home"; st.rerun()
    t1, t2, t3 = st.tabs(["📊 التقارير الموحدة", "🏘️ حالة اللجان", "💾 إدارة البيانات"])
    
    with t1:
        d = st.date_input("اختر التاريخ:", datetime.now())
        att = supabase.table("attendance").select("*").eq("date", str(d)).execute()
        if att.data:
            df = pd.DataFrame(att.data)
            df_abs = df[df['status'].isin(['غائب', 'متأخر'])].copy()
            if st.button(f"🗑️ حذف سجلات يوم {d}"):
                supabase.table('attendance').delete().eq("date", str(d)).execute(); st.rerun()
            
            if not df_abs.empty:
                # دمج الشعبة برمجياً لتجنب APIError
                st_data = supabase.table('students').select("student_name, class_name").execute()
                s_map = {i['student_name']: i['class_name'] for i in st_data.data}
                df_abs['الشعبة'] = df_abs['student_name'].map(s_map).fillna("---")
                
                # عرض الجدول المرتب
                st.table(df_abs[['committee', 'student_name', 'الشعبة', 'status', 'teacher_name']].rename(columns={'committee':'اللجنة','student_name':'الطالب'}))
                
                wa_msg = f"🗓️ *تقرير غياب يوم {d}*%0A"
                for _, r in df_abs.iterrows():
                    wa_msg += f"📍 لجنة {r['committee']} | {r['student_name']} ({r['status']})%0A"
                st.markdown(f'<a href="https://wa.me/?text={wa_msg}" target="_blank" class="whatsapp-btn">📲 إرسال عبر واتساب</a>', unsafe_allow_html=True)
        else: st.info("لا توجد سجلات")

    with t2:
        st.subheader("تحضير اللجان لليوم")
        all_c = supabase.table('students').select("committee").execute()
        all_set = sorted(list(set([str(i['committee']) for i in all_c.data])), key=lambda x: int(x) if x.isdigit() else 0)
        done = supabase.table('attendance').select("committee, teacher_name").eq("date", str(datetime.now().date())).execute()
        done_m = {str(i['committee']): i['teacher_name'] for i in done.data}
        
        col1, col2 = st.columns(2)
        with col1:
            st.success("✅ لجان اكتملت")
            for c in all_set:
                if c in done_m: st.write(f"لجنة {c} (بواسطة: {done_m[c]})")
        with col2:
            st.error("❌ لجان متبقية")
            for c in all_set:
                if c not in done_m: st.write(f"لجنة {c}")

    with t3:
        if st.text_input("كلمة سر البيانات:", type="password") == "4321":
            sd = supabase.table('students').select("*").execute()
            if sd.data:
                df_all = pd.DataFrame(sd.data)
                st.download_button("💾 تحميل نسخة CSV", df_all.to_csv(index=False).encode('utf-8-sig'), "students.csv")
                # نسخة Excel
                out = io.BytesIO()
                with pd.ExcelWriter(out, engine='xlsxwriter') as wr: df_all.to_excel(wr, index=False)
                st.download_button("📊 تحميل نسخة XLSX", out.getvalue(), "students.xlsx")
            
            up = st.file_uploader("رفع ملف بيانات جديد:")
            if up and st.button("🚀 تحديث قاعدة البيانات"):
                df_up = pd.read_csv(up) if up.name.endswith('.csv') else pd.read_excel(up)
                supabase.table('students').delete().neq('id', 0).execute()
                recs = df_up.to_dict('records')
                for r in recs: r.pop('id', None)
                supabase.table('students').insert(recs).execute()
                st.success("تم التحديث")
