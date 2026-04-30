import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
import io

# 1. إعدادات الاتصال بقاعدة البيانات
url = "https://lsmevvsogsqqqjyuqzbx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzbWV2dnNvZ3NxcXFqeXVxemJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MDMyOTgsImV4cCI6MjA5Mjk3OTI5OH0.ecqJS75fPbKqwSAiBzP6Qonn4cuymgwjB96tIGek8j0"

if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(url, key)
supabase = st.session_state.supabase

# 2. إعدادات الواجهة والتنسيق (CSS)
st.set_page_config(page_title="نظام مدرسة القطيف التقني", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
        direction: rtl;
        background-color: #f0f2f6;
    }
    
    .stApp { background-color: #f0f2f6; }
    
    .hero-section {
        background: linear-gradient(135deg, #1a237e 0%, #3949ab 100%);
        padding: 40px;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    
    .main-title { font-size: 38px; font-weight: 800; margin-bottom: 10px; }
    
    .credit-box {
        background: rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 15px;
        margin-top: 20px;
        display: inline-block;
        width: 100%;
        max-width: 600px;
    }
    
    .credit-text { font-size: 20px; margin: 5px 0; }
    .manager-text { font-size: 18px; color: #e8eaf6; font-weight: bold; }
    
    /* تمييز حقول الإدخال بلون مختلف */
    .stTextInput > div > div > input {
        background-color: #ffffff !important;
        border: 2px solid #1a237e !important;
        border-radius: 10px !important;
        color: #1a237e !important;
        font-weight: bold !important;
    }

    div.stButton > button {
        width: 100%;
        border-radius: 15px;
        font-weight: bold;
        height: 70px;
        font-size: 20px !important;
        transition: all 0.3s;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    
    .whatsapp-btn { 
        background-color: #25D366; color: white; padding: 18px; 
        border-radius: 15px; text-align: center; text-decoration: none; 
        display: block; font-weight: bold; margin: 20px auto; 
        max-width: 600px; font-size: 20px; border: 1px solid #128C7E; 
    }
    
    th { background-color: #1a237e !important; color: white !important; text-align: center !important; }
    td { text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

if 'page' not in st.session_state: st.session_state.page = "home"

# --- 🏠 1. الصفحة الرئيسية ---
if st.session_state.page == "home":
    st.markdown("""
        <div class="hero-section">
            <p class="main-title">التحضير التقني لمدرسة القطيف الثانوية</p>
            <div class="credit-box">
                <p class="credit-text">💡 فكرة وبرمجة: <b>أ. عارف أحمد الحداد</b></p>
                <p class="manager-text">إشراف مدير المدرسة: <b>أ. فراس عبدالله آل عبد المحسن</b></p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📝 دخول المعلمين للرصد", type="primary"): 
            st.session_state.page = "att_login"
            st.rerun()
        st.write(" ")
        if st.button("⚙️ لوحة الإدارة والتقارير"): 
            st.session_state.page = "admin_login"
            st.rerun()

# --- 📝 2. نظام رصد المعلمين ---
elif st.session_state.page == "att_login":
    if st.button("⬅️ عودة للرئيسية"): st.session_state.page = "home"; st.rerun()
    st.markdown("### 🔐 منطقة دخول المعلم")
    t_id = st.text_input("أدخل رقم السجل المدني للمعلم:", type="password")
    if st.button("دخول"):
        res = supabase.table("teachers").select("*").eq("national_id", t_id.strip()).execute()
        if res.data:
            st.session_state.teacher_name = res.data[0]['name_tech']
            st.session_state.page = "taking_attendance"; st.rerun()
        else: st.error("السجل غير مسجل في النظام")

elif st.session_state.page == "taking_attendance":
    today = str(datetime.now().date())
    st.info(f"المعلم: {st.session_state.teacher_name} | التاريخ: {today}")
    s_data = supabase.table('students').select("committee").execute()
    coms = sorted(list(set([str(i['committee']) for i in s_data.data if i['committee']])), key=lambda x: int(x) if x.isdigit() else 0)
    sel_c = st.selectbox("اختر اللجنة المراد رصدها:", ["---"] + coms)
    if sel_c != "---":
        students = supabase.table('students').select("*").eq('committee', sel_c).execute()
        results = []
        for s in students.data:
            stat = st.radio(f"👤 {s['student_name']}", ["حاضر", "غائب", "متأخر"], key=f"s_{s['id']}", horizontal=True)
            results.append({"student_name": s['student_name'], "committee": str(sel_c), "status": stat, "date": today, "teacher_name": st.session_state.teacher_name})
        if st.button("💾 حفظ الرصد نهائياً"):
            supabase.table('attendance').delete().eq('committee', sel_c).eq('date', today).execute()
            supabase.table('attendance').insert(results).execute()
            st.success("✅ تم حفظ البيانات بنجاح"); time.sleep(1); st.session_state.page = "home"; st.rerun()

# --- ⚙️ 3. لوحة الإدارة ---
elif st.session_state.page == "admin_login":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    st.markdown("### 🔒 إدارة النظام")
    admin_code = st.text_input("رمز دخول المسؤول:", type="password")
    if admin_code == "1234": 
        st.session_state.page = "admin_panel"
        st.rerun()

elif st.session_state.page == "admin_panel":
    if st.button("⬅️ تسجيل الخروج"): st.session_state.page = "home"; st.rerun()
    tab1, tab2, tab3 = st.tabs(["📊 التقارير الموحدة", "🏘️ متابعة حالة اللجان", "💾 إدارة بيانات الطلاب"])
    today_date = str(datetime.now().date())

    with tab1:
        d = st.date_input("اختر تاريخ عرض التقرير", datetime.now())
        res = supabase.table("attendance").select("*").eq("date", str(d)).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df_abs = df[df['status'].isin(['غائب', 'متأخر'])].copy()
            if not df_abs.empty:
                classes = []
                for name in df_abs['student_name']:
                    try:
                        s_info = supabase.table('students').select("class_name").eq("student_name", name).execute()
                        classes.append(s_info.data[0]['class_name'] if s_info.data else "---")
                    except: classes.append("---")
                df_abs['الشعبة'] = classes
                df_abs['committee_num'] = pd.to_numeric(df_abs['committee'], errors='coerce')
                df_abs = df_abs.sort_values(by='committee_num')
                
                st.subheader(f"📋 كشف الغياب والتأخر ليوم {d}")
                final_view = df_abs[['committee', 'student_name', 'الشعبة', 'status', 'teacher_name']].copy()
                final_view.columns = ['رقم اللجنة', 'اسم الطالب', 'الشعبة', 'الحالة', 'المعلم']
                st.table(final_view)
                
                msg = f"🗓️ *تقرير مدرسة القطيف التقني*%0A📅 *التاريخ:* {d}%0A---------------------------------------%0A"
                for _, r in df_abs.iterrows():
                    msg += f"📦 *لجنة:* {r['committee']}%0A👤 *الاسم:* {r['student_name']} ({r['status']})%0A%0A"
                st.markdown(f'<a href="https://wa.me/?text={msg}" target="_blank" class="whatsapp-btn">إرسال التقرير عبر واتساب 📲</a>', unsafe_allow_html=True)
            else: st.success("جميع الطلاب حاضرون لهذا اليوم")

    with tab2:
        st.subheader(f"🏘️ حالة رصد اللجان اليوم: {today_date}")
        all_s = supabase.table('students').select("committee").execute()
        total_coms = sorted(list(set([str(i['committee']) for i in all_s.data if i['committee']])), key=lambda x: int(x) if x.isdigit() else 0)
        done_res = supabase.table('attendance').select("committee, teacher_name").eq("date", today_date).execute()
        done_coms = {str(i['committee']): i['teacher_name'] for i in done_res.data}
        c1, c2 = st.columns(2)
        with c1:
            st.success("✅ لجان تم رصدها")
            for c in total_coms:
                if c in done_coms: st.write(f"📍 لجنة {c} (الراصد: {done_coms[c]})")
        with c2:
            st.error("❌ لجان لم ترصد")
            for c in total_coms:
                if c not in done_coms: st.write(f"⚠️ لجنة {c}")

    with tab3:
        st.subheader("🛠️ أدوات التحكم بالبيانات")
        admin_pass = st.text_input("أدخل الرقم السري للتحكم بالبيانات (4321):", type="password")
        if admin_pass == "4321":
            st.success("تم تفعيل صلاحيات الإدارة")
            
            # --- أزرار التصدير والاستعادة ---
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("### 📥 تصدير البيانات")
                std_res = supabase.table('students').select("*").execute()
                if std_res.data:
                    df_std = pd.DataFrame(std_res.data)
                    # زر CSV
                    st.download_button("💾 نسخة CSV", data=df_std.to_csv(index=False).encode('utf-8-sig'), file_name=f"students_{today_date}.csv")
                    # زر XLSX
                    out = io.BytesIO()
                    with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
                        df_std.to_excel(writer, index=False)
                    st.download_button("📊 نسخة XLSX", data=out.getvalue(), file_name=f"students_{today_date}.xlsx")
            
            with col_b:
                st.markdown("### 🔄 استعادة النسخة")
                up_file = st.file_uploader("ارفع ملف النسخة الاحتياطية:", type=["csv", "xlsx"])
                if up_file and st.button("🚀 بدء عملية الاستعادة"):
                    df_up = pd.read_csv(up_file) if up_file.name.endswith('.csv') else pd.read_excel(up_file)
                    # مسح القديم
                    supabase.table('students').delete().neq('student_name', 'none').execute()
                    # إدخال الجديد
                    recs = df_up.to_dict('records')
                    for r in recs: r.pop('id', None)
                    supabase.table('students').insert(recs).execute()
                    st.success("تمت الاستعادة بنجاح!"); time.sleep(1); st.rerun()

            st.divider()
            if st.button("🗑️ حذف كافة بيانات الطلاب نهائياً", type="secondary"):
                supabase.table('students').delete().neq('student_name', 'none').execute()
                st.success("تم مسح الجدول بنجاح"); st.rerun()
