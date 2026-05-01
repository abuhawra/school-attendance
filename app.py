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
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; background-color: #f0f2f6; }
    .stApp { background-color: #f0f2f6; }
    .hero-section {
        background: linear-gradient(135deg, #1a237e 0%, #3949ab 100%);
        padding: 40px; border-radius: 20px; color: white; text-align: center; margin-bottom: 30px; box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    .main-title { font-size: 38px; font-weight: 800; margin-bottom: 10px; }
    .credit-box { background: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 15px; margin-top: 20px; display: inline-block; width: 100%; max-width: 600px; }
    .stTextInput > div > div > input { background-color: #ffffff !important; border: 2px solid #1a237e !important; border-radius: 10px !important; color: #1a237e !important; font-weight: bold !important; }
    div.stButton > button { width: 100%; border-radius: 15px; font-weight: bold; height: 60px; font-size: 18px !important; transition: all 0.3s; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .whatsapp-btn { background-color: #25D366; color: white; padding: 18px; border-radius: 15px; text-align: center; text-decoration: none; display: block; font-weight: bold; margin: 20px auto; max-width: 600px; font-size: 20px; border: 1px solid #128C7E; }
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
                <p style="font-size:20px; margin:5px 0;">💡 فكرة وبرمجة: <b>أ. عارف أحمد الحداد</b></p>
                <p style="font-size:18px; color:#e8eaf6;">إشراف مدير المدرسة: <b>أ. فراس عبدالله آل عبد المحسن</b></p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📝 دخول المعلمين للرصد", type="primary"): st.session_state.page = "att_login"; st.rerun()
        st.write(" ")
        if st.button("⚙️ لوحة الإدارة والتقارير"): st.session_state.page = "admin_login"; st.rerun()

# --- 📝 2. نظام رصد المعلمين ---
elif st.session_state.page == "att_login":
    if st.button("⬅️ عودة للرئيسية"): st.session_state.page = "home"; st.rerun()
    st.markdown("### 🔐 منطقة دخول المعلم")
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
    sel_c = st.selectbox("اختر اللجنة:", ["---"] + coms)
    
    if sel_c != "---":
        # 1. جلب بيانات الطلاب
        students = supabase.table('students').select("*").eq('committee', sel_c).execute()
        # 2. جلب التحضير السابق (التعديل الجديد)
        old_att = supabase.table('attendance').select("student_name, status").eq('committee', sel_c).eq('date', today).execute()
        old_map = {item['student_name']: item['status'] for item in old_att.data}
        
        results = []
        for s in students.data:
            # تثبيت الحالة عند الدخول (التعديل الجديد)
            default_val = old_map.get(s['student_name'], "حاضر")
            idx = ["حاضر", "غائب", "متأخر"].index(default_val)
            
            stat = st.radio(f"👤 {s['student_name']}", ["حاضر", "غائب", "متأخر"], index=idx, key=f"s_{s['id']}", horizontal=True)
            results.append({"student_name": s['student_name'], "committee": str(sel_c), "status": stat, "date": today, "teacher_name": st.session_state.teacher_name})
        
        if st.button("💾 حفظ الرصد نهائياً"):
            supabase.table('attendance').delete().eq('committee', sel_c).eq('date', today).execute()
            supabase.table('attendance').insert(results).execute()
            st.success("✅ تم الحفظ بنجاح"); time.sleep(1); st.session_state.page = "home"; st.rerun()

# --- ⚙️ 3. لوحة الإدارة والتقارير ---
elif st.session_state.page == "admin_login":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    admin_code = st.text_input("رمز دخول المسؤول:", type="password")
    if admin_code == "1234": st.session_state.page = "admin_panel"; st.rerun()

elif st.session_state.page == "admin_panel":
    if st.button("⬅️ تسجيل الخروج"): st.session_state.page = "home"; st.rerun()
    tab1, tab2, tab3 = st.tabs(["📊 التقارير", "🏘️ حالة اللجان", "💾 البيانات"])
    
    with tab1:
        # التعديل الجديد: التنقل بين الأيام
        report_date = st.date_input("🗓️ اختر التاريخ لعرض التقرير:", datetime.now())
        res = supabase.table("attendance").select("*").eq("date", str(report_date)).execute()
        
        if res.data:
            df = pd.DataFrame(res.data)
            df_abs = df[df['status'].isin(['غائب', 'متأخر'])].copy()
            
            # التعديل الجديد: زر حذف حسب التاريخ المختار
            col_del1, col_del2 = st.columns([2, 1])
            with col_del2:
                if st.button(f"🗑️ حذف سجلات {report_date}", type="secondary"):
                    supabase.table('attendance').delete().eq('date', str(report_date)).execute()
                    st.warning(f"تم مسح بيانات يوم {report_date}"); time.sleep(1); st.rerun()

            if not df_abs.empty:
                # جلب الشعبة للعرض فقط
                classes = []
                for name in df_abs['student_name']:
                    try:
                        s_info = supabase.table('students').select("class_name").eq("student_name", name).execute()
                        classes.append(s_info.data[0]['class_name'] if s_info.data else "---")
                    except: classes.append("---")
                df_abs['الشعبة'] = classes
                df_abs['committee_num'] = pd.to_numeric(df_abs['committee'], errors='coerce')
                df_abs = df_abs.sort_values(by='committee_num')
                
                st.subheader(f"📋 تقرير يوم {report_date}")
                final_view = df_abs[['committee', 'student_name', 'الشعبة', 'status', 'teacher_name']].copy()
                final_view.columns = ['اللجنة', 'اسم الطالب', 'الشعبة', 'الحالة', 'المعلم']
                st.table(final_view)
                
                msg = f"🗓️ *تقرير مدرسة القطيف التقني*%0A📅 *التاريخ:* {report_date}%0A---------------------------------------%0A"
                for _, r in df_abs.iterrows():
                    msg += f"📦 *لجنة:* {r['committee']}%0A👤 *الاسم:* {r['student_name']} ({r['status']})%0A%0A"
                st.markdown(f'<a href="https://wa.me/?text={msg}" target="_blank" class="whatsapp-btn">إرسال عبر واتساب 📲</a>', unsafe_allow_html=True)
            else: st.success("لا توجد حالات غياب في هذا التاريخ")
        else: st.info("لا توجد بيانات محفوظة لهذا التاريخ")

    with tab2:
        st.subheader(f"🏘️ حالة الرصد اليومي")
        all_s = supabase.table('students').select("committee").execute()
        total_coms = sorted(list(set([str(i['committee']) for i in all_s.data if i['committee']])), key=lambda x: int(x) if x.isdigit() else 0)
        done_res = supabase.table('attendance').select("committee, teacher_name").eq("date", str(datetime.now().date())).execute()
        done_coms = {str(i['committee']): i['teacher_name'] for i in done_res.data}
        c1, c2 = st.columns(2)
        with c1:
            st.success("✅ رُصدت")
            for c in total_coms:
                if c in done_coms: st.write(f"📍 لجنة {c} ({done_coms[c]})")
        with c2:
            st.error("❌ لم تُرصد")
            for c in total_coms:
                if c not in done_coms: st.write(f"⚠️ لجنة {c}")

    with tab3:
        if st.text_input("كلمة سر البيانات (4321):", type="password") == "4321":
            col_a, col_b = st.columns(2)
            with col_a:
                std_res = supabase.table('students').select("*").execute()
                if std_res.data:
                    df_std = pd.DataFrame(std_res.data)
                    st.download_button("💾 نسخة CSV", data=df_std.to_csv(index=False).encode('utf-8-sig'), file_name="students_backup.csv")
            with col_b:
                up_file = st.file_uploader("ارفع ملف الاستعادة:", type=["csv", "xlsx"])
                if up_file and st.button("🚀 استعادة"):
                    df_up = pd.read_csv(up_file) if up_file.name.endswith('.csv') else pd.read_excel(up_file)
                    supabase.table('students').delete().neq('student_name', 'none').execute()
                    recs = df_up.to_dict('records')
                    for r in recs: r.pop('id', None)
                    supabase.table('students').insert(recs).execute()
                    st.success("تمت الاستعادة"); time.sleep(1); st.rerun()
