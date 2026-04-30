import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
import urllib.parse
from fpdf import FPDF
import base64

# 1. إعدادات الاتصال بقاعدة البيانات
url = "https://lsmevvsogsqqqjyuqzbx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzbWV2dnNvZ3NxcXFqeXVxemJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MDMyOTgsImV4cCI6MjA5Mjk3OTI5OH0.ecqJS75fPbKqwSAiBzP6Qonn4cuymgwjB96tIGek8j0"

if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(url, key)
supabase = st.session_state.supabase

# 2. إخفاء عناصر Streamlit وتنسيق الأزرار
st.set_page_config(page_title="نظام غياب مدرسة القطيف الثانوية", layout="wide")

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            .stAppDeployButton, [data-testid="stStatusWidget"], .st-emotion-cache-zq5wmm { display: none !important; }

            /* زر تحضير الطلاب - أزرق فاتح */
            button[kind="primary"] {
                background-color: #ADD8E6 !important;
                color: #000000 !important;
                border: 2px solid #ADD8E6 !important;
            }
            /* زر إدارة التطبيق - برتقالي */
            button[kind="secondary"] {
                background-color: #FFA500 !important;
                color: #FFFFFF !important;
                border: 2px solid #FFA500 !important;
            }
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# 3. دوال مساعدة
def smart_sort(x):
    try: return int(x)
    except: return str(x)

def get_system_status():
    try:
        res = supabase.table("settings").select("is_open").eq("setting_name", "attendance_status").execute()
        return res.data[0]['is_open'] if res.data else True
    except: return True

def create_pdf(df, report_date):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font('Arial', '', '', unicode=True) # تأكد من توفر خط يدعم العربية إذا أردت العربية بالكامل
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Attendance Report - {report_date}", ln=True, align='C')
    pdf.ln(10)
    
    # أعمدة الجدول
    pdf.cell(80, 10, "Student Name", 1)
    pdf.cell(30, 10, "Section", 1)
    pdf.cell(40, 10, "Committee", 1)
    pdf.cell(30, 10, "Status", 1)
    pdf.ln()
    
    for _, row in df.iterrows():
        pdf.cell(80, 10, str(row['الاسم']), 1)
        pdf.cell(30, 10, str(row['الشعبة']), 1)
        pdf.cell(40, 10, str(row['اللجنة']), 1)
        pdf.cell(30, 10, str(row['الحالة']), 1)
        pdf.ln()
    
    return pdf.output(dest='S').encode('latin-1')

# تهيئة متغيرات الجلسة
if 'page' not in st.session_state: st.session_state.page = "home"
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 4. الصفحة الرئيسية ---
if st.session_state.page == "home":
    st.write("<br><br>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style="text-align: center; border: 2px solid #1f77b4; padding: 40px; border-radius: 20px; background-color: #f8f9fa;">
            <h1 style="color: #1f77b4;">برنامج تحضير الغياب</h1>
            <h2>مدرسة القطيف الثانوية</h2>
            <h3 style="color: #2c3e50;">أ. عارف أحمد الحداد</h3>
        </div>
    """, unsafe_allow_html=True)
    
    st.write("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 تحضير الطلاب", use_container_width=True, type="primary"):
            st.session_state.page = "attendance"; st.rerun()
    with col2:
        if st.button("⚙️ إدارة التطبيق", use_container_width=True, type="secondary"):
            st.session_state.page = "admin"; st.rerun()

# --- 5. صفحة التحضير ---
elif st.session_state.page == "attendance":
    if st.button("⬅️ العودة"): st.session_state.page = "home"; st.rerun()
    if not get_system_status():
        st.error("🚫 النظام مغلق حالياً.")
    else:
        if not st.session_state.logged_in:
            nid = st.text_input("أدخل السجل المدني:", type="password")
            if st.button("دخول"):
                res = supabase.table("teachers").select("*").eq("national_id", nid.strip()).execute()
                if res.data:
                    st.session_state.logged_in = True
                    st.session_state.teacher_name = res.data[0].get('name_tech', 'المعلم')
                    st.rerun()
        else:
            st.success(f"مرحباً: {st.session_state.teacher_name}")
            t_date = st.date_input("التاريخ", datetime.now())
            s_data = supabase.table('students').select("committee").execute()
            committees = sorted(list(set([str(i['committee']) for i in s_data.data if i['committee']])), key=smart_sort)
            sel_c = st.selectbox("اختر اللجنة:", ["---"] + committees)
            if sel_c != "---":
                students = supabase.table('students').select("*").eq('committee', sel_c).execute()
                results = []
                for s in students.data:
                    c1, c2 = st.columns([2, 1])
                    c1.write(s['student_name'])
                    stat = c2.radio("الحالة", ["حاضر", "غائب", "متأخر"], key=s['id'], horizontal=True)
                    results.append({"student_name": s['student_name'], "committee": sel_c, "status": stat, "date": str(t_date), "teacher_name": st.session_state.teacher_name})
                if st.button("💾 حفظ"):
                    supabase.table('attendance').delete().eq('committee', sel_c).eq('date', str(t_date)).execute()
                    supabase.table('attendance').insert(results).execute()
                    st.success("تم الحفظ!"); time.sleep(1); st.session_state.page = "home"; st.rerun()

# --- 6. صفحة الإدارة والتقارير ---
elif st.session_state.page == "admin":
    if st.button("⬅️ العودة"): st.session_state.page = "home"; st.rerun()
    pw = st.text_input("كلمة المرور", type="password")
    if pw == "1234":
        st.header("📊 التقارير والمتابعة")
        rep_date = st.date_input("تاريخ التقرير", datetime.now())
        att = supabase.table('attendance').select("*").eq('date', str(rep_date)).execute()
        std = supabase.table('students').select("student_name, section, committee").execute()

        if att.data:
            df_a, df_s = pd.DataFrame(att.data), pd.DataFrame(std.data)
            m = pd.merge(df_a, df_s, on='student_name', how='left')
            final = m[m['status'].isin(['غائب', 'متأخر'])][['student_name', 'section', 'committee_x', 'status']]
            final.columns = ['الاسم', 'الشعبة', 'اللجنة', 'الحالة']
            
            st.table(final)

            # زر الواتساب (متوافق مع ويب والأعمال)
            msg = f"*تقرير الغياب - {rep_date}*\n\n"
            for _, r in final.iterrows():
                msg += f"👤 {r['الاسم']} | {r['الحالة']}\n"
            
            whatsapp_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg)}"
            st.link_button("📱 إرسال عبر الواتساب (Web/Business)", whatsapp_url)

            # زر PDF
            if st.button("📄 عرض وتحميل PDF"):
                pdf_data = create_pdf(final, rep_date)
                b64 = base64.b64encode(pdf_data).decode('latin-1')
                href = f'<a href="data:application/octet-stream;base64,{b64}" download="attendance_{rep_date}.pdf">اضغط هنا لتحميل ملف PDF</a>'
                st.markdown(href, unsafe_allow_html=True)
        else:
            st.info("لا توجد بيانات لهذا التاريخ.")
