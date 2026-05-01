import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
import io

# 1. إعدادات الاتصال
url = "https://lsmevvsogsqqqjyuqzbx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzbWV2dnNvZ3NxcXFqeXVxemJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MDMyOTgsImV4cCI6MjA5Mjk3OTI5OH0.ecqJS75fPbKqwSAiBzP6Qonn4cuymgwjB96tIGek8j0"

if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(url, key)
supabase = st.session_state.supabase

# 2. تصميم الواجهة الكلاسيكية الهادئة
st.set_page_config(page_title="نظام مدرسة القطيف التقني", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; background-color: #f0f2f6; }
    .main-card {
        background-color: #1a237e; color: white; padding: 40px; border-radius: 20px;
        text-align: center; border-bottom: 6px solid #ffd700; box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    }
    .hr-line { border: 0; height: 1px; background: rgba(255,255,255,0.3); width: 40%; margin: 25px auto; }
    .stButton>button { border-radius: 12px; font-weight: bold; height: 55px; font-size: 18px !important; transition: 0.3s; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
    .whatsapp-btn { background-color: #25D366; color: white; padding: 15px; border-radius: 12px; text-align: center; display: block; text-decoration: none; font-weight: bold; margin: 20px auto; max-width: 400px; }
    th { background-color: #1a237e !important; color: white !important; text-align: center !important; }
    td { text-align: center !important; vertical-align: middle !important; }
    </style>
    """, unsafe_allow_html=True)

if 'page' not in st.session_state: st.session_state.page = "home"

# --- الصفحة الرئيسية (الواجهة المطلوبة) ---
if st.session_state.page == "home":
    st.markdown("""
        <div class="main-card">
            <div style="font-size:38px; font-weight:800; margin-bottom:5px;">التحضير التقني</div>
            <div style="font-size:28px; font-weight:700; opacity:0.9;">مدرسة القطيف الثانوية</div>
            <div class="hr-line"></div>
            <div style="font-size:18px; color:#ffd700; margin-bottom:5px;">فكرة وبرمجة</div>
            <div style="font-size:26px; font-weight:bold; margin-bottom:25px;">أ. عارف أحمد الحداد</div>
            <div style="font-size:18px; color:#cfd8dc; margin-bottom:5px;">مدير المدرسة</div>
            <div style="font-size:22px; font-weight:bold;">أ. فراس عبدالله آل عبد المحسن</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.write(" ")
    col_1, col_2, col_3 = st.columns([1, 1.2, 1])
    with col_2:
        if st.button("📝 رصد غياب الطلاب", type="primary"): st.session_state.page = "t_login"; st.rerun()
        st.write(" ")
        if st.button("⚙️ لوحة الإدارة والتقارير"): st.session_state.page = "a_login"; st.rerun()

# --- دخول المعلمين ---
elif st.session_state.page == "t_login":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    t_id = st.text_input("أدخل رقم السجل المدني:", type="password")
    if st.button("دخول"):
        res = supabase.table("teachers").select("*").eq("national_id", t_id.strip()).execute()
        if res.data:
            st.session_state.teacher = res.data[0]['name_tech']
            st.session_state.page = "marking"; st.rerun()
        else: st.error("السجل المدني غير مسجل")

elif st.session_state.page == "marking":
    today = str(datetime.now().date())
    st.info(f"المعلم: {st.session_state.teacher} | التاريخ: {today}")
    
    # جلب اللجان (الحل الجذري: جلب الكل ثم الفلترة)
    s_raw = supabase.table('students').select("*").execute()
    df_s = pd.DataFrame(s_raw.data)
    coms = sorted(df_s['committee'].unique().tolist(), key=lambda x: int(x) if str(x).isdigit() else 0)
    
    sel_c = st.selectbox("اختر اللجنة:", ["---"] + [str(c) for c in coms])
    if sel_c != "---":
        st_committee = df_s[df_s['committee'].astype(str) == sel_c]
        
        # جلب الحالات السابقة لتثبيتها
        att_raw = supabase.table('attendance').select("*").eq("committee", sel_c).eq("date", today).execute()
        old_map = {i['student_name']: i['status'] for i in att_raw.data}
        
        results = []
        for _, s in st_committee.iterrows():
            prev = old_map.get(s['student_name'], "حاضر")
            choice = st.radio(f"👤 {s['student_name']}", ["حاضر", "غائب", "متأخر"], 
                              index=["حاضر", "غائب", "متأخر"].index(prev), key=f"s_{s['student_name']}", horizontal=True)
            results.append({"student_name": s['student_name'], "committee": sel_c, "status": choice, "date": today, "teacher_name": st.session_state.teacher})
        
        if st.button("💾 حفظ الرصد نهائياً"):
            supabase.table('attendance').delete().eq("committee", sel_c).eq("date", today).execute()
            supabase.table('attendance').insert(results).execute()
            st.success("✅ تم حفظ البيانات بنجاح"); time.sleep(1); st.session_state.page = "home"; st.rerun()

# --- لوحة الإدارة ---
elif st.session_state.page == "a_login":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    if st.text_input("رمز الدخول:", type="password") == "1234": st.session_state.page = "admin"; st.rerun()

elif st.session_state.page == "admin":
    if st.button("⬅️ تسجيل الخروج"): st.session_state.page = "home"; st.rerun()
    tab1, tab2, tab3 = st.tabs(["📊 التقارير الموحدة", "🏘️ متابعة حالة اللجان", "💾 إدارة البيانات"])
    
    with tab1:
        rep_date = st.date_input("اختر تاريخ التقرير:", datetime.now())
        att_data = supabase.table("attendance").select("*").eq("date", str(rep_date)).execute()
        
        if att_data.data:
            df_att = pd.DataFrame(att_data.data)
            df_abs = df_att[df_att['status'].isin(['غائب', 'متأخر'])].copy()
            
            if st.button(f"🗑️ حذف كافة سجلات يوم {rep_date}"):
                supabase.table('attendance').delete().eq("date", str(rep_date)).execute(); st.rerun()
            
            if not df_abs.empty:
                # الحل الجذري: دمج الشعبة من بيانات الطلاب الموجودة فعلياً
                std_all = supabase.table('students').select("*").execute()
                df_std = pd.DataFrame(std_all.data)
                # استخدام map لتجنب أخطاء الاستعلام الفردي
                s_map = dict(zip(df_std['student_name'], df_std['class_name']))
                df_abs['الشعبة'] = df_abs['student_name'].map(s_map).fillna("غير محدد")
                
                df_abs['c_num'] = pd.to_numeric(df_abs['committee'], errors='coerce')
                df_abs = df_abs.sort_values(by='c_num')
                
                st.table(df_abs[['committee', 'student_name', 'الشعبة', 'status', 'teacher_name']].rename(columns={'committee':'اللجنة','student_name':'الطالب'}))
                
                msg = f"🗓️ *تقرير مدرسة القطيف التقني - يوم {rep_date}*%0A"
                for _, r in df_abs.iterrows():
                    msg += f"📍 لجنة {r['committee']} | {r['student_name']} ({r['status']})%0A"
                st.markdown(f'<a href="https://wa.me/?text={msg}" target="_blank" class="whatsapp-btn">📲 إرسال التقرير عبر واتساب</a>', unsafe_allow_html=True)
        else: st.info("لا توجد بيانات غياب مسجلة لهذا التاريخ")

    with tab2:
        st.subheader("🏘️ حالة رصد اللجان لليوم")
        all_st = supabase.table('students').select("*").execute()
        df_all_s = pd.DataFrame(all_st.data)
        all_coms = sorted(df_all_s['committee'].unique().astype(str).tolist(), key=lambda x: int(x) if x.isdigit() else 0)
        
        done_att = supabase.table('attendance').select("*").eq("date", str(datetime.now().date())).execute()
        done_dict = {str(i['committee']): i['teacher_name'] for i in done_att.data}
        
        c1, c2 = st.columns(2)
        with c1:
            st.success("✅ لجان تم رصدها")
            for c in all_coms:
                if c in done_dict: st.write(f"لجنة {c} (المعلم: {done_dict[c]})")
        with c2:
            st.error("❌ لجان لم تُرصد بعد")
            for c in all_coms:
                if c not in done_dict: st.write(f"لجنة {c}")

    with tab3:
        if st.text_input("كلمة مرور الإدارة (4321):", type="password") == "4321":
            std_res = supabase.table('students').select("*").execute()
            if std_res.data:
                df_bk = pd.DataFrame(std_res.data)
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    st.download_button("💾 نسخة CSV", df_bk.to_csv(index=False).encode('utf-8-sig'), "backup.csv")
                    out = io.BytesIO()
                    with pd.ExcelWriter(out, engine='xlsxwriter') as wr: df_bk.to_excel(wr, index=False)
                    st.download_button("📊 نسخة XLSX", out.getvalue(), "backup.xlsx")
                with col_d2:
                    up = st.file_uploader("تحديث البيانات (رفع ملف جديد):")
                    if up and st.button("🚀 استيراد البيانات"):
                        df_new = pd.read_csv(up) if up.name.endswith('.csv') else pd.read_excel(up)
                        supabase.table('students').delete().neq('student_name', 'none').execute()
                        recs = df_new.to_dict('records')
                        for r in recs: r.pop('id', None)
                        supabase.table('students').insert(recs).execute(); st.success("تم التحديث بنجاح")
