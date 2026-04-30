import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
import urllib.parse
import os
from fpdf import FPDF
from arabic_reshaper import reshape
from bidi.algorithm import get_display

# 1. إعدادات الاتصال بقاعدة البيانات
url = "https://lsmevvsogsqqqjyuqzbx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzbWV2dnNvZ3NxcXFqeXVxemJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MDMyOTgsImV4cCI6MjA5Mjk3OTI5OH0.ecqJS75fPbKqwSAiBzP6Qonn4cuymgwjB96tIGek8j0"

if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(url, key)
supabase = st.session_state.supabase

# 2. إعدادات الصفحة وتنسيق الأزرار (أزرق فاتح وبرتقالي)
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
                font-weight: bold !important;
            }
            /* زر إدارة التطبيق - برتقالي */
            button[kind="secondary"] {
                background-color: #FFA500 !important;
                color: #FFFFFF !important;
                border: 2px solid #FFA500 !important;
                font-weight: bold !important;
            }
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# 3. الدوال المساعدة
def smart_sort(x):
    try: return int(x)
    except: return str(x)

def get_system_status():
    try:
        res = supabase.table("settings").select("is_open").eq("setting_name", "attendance_status").execute()
        return res.data[0]['is_open'] if res.data else True
    except: return True

def fix_arabic(text):
    """تهيئة النص العربي للعرض في PDF من اليمين لليسار"""
    try:
        reshaped_text = reshape(str(text))
        return get_display(reshaped_text)
    except:
        return str(text)

def create_pdf(df, report_date):
    pdf = FPDF()
    pdf.add_page()
    
    font_path = "arial.ttf" # يجب رفع هذا الملف على GitHub
    
    if os.path.exists(font_path):
        pdf.add_font("CustomArial", "", font_path)
        pdf.set_font("CustomArial", size=12)
        has_font = True
    else:
        pdf.set_font("Arial", size=12)
        has_font = False

    # عنوان التقرير
    pdf.set_font("Arial", size=16, style='B')
    pdf.cell(200, 10, txt=f"Attendance Report - {report_date}", ln=True, align='C')
    pdf.ln(10)
    
    # رؤوس الجدول
    pdf.set_font("Arial", size=11, style='B')
    pdf.cell(40, 10, "Status", 1, align='C')
    pdf.cell(30, 10, "Committee", 1, align='C')
    pdf.cell(30, 10, "Section", 1, align='C')
    pdf.cell(85, 10, "Student Name", 1, align='C')
    pdf.ln()
    
    # بيانات الجدول
    pdf.set_font("Arial", size=11)
    for _, row in df.iterrows():
        if has_font:
            p_name = fix_arabic(row['الاسم'])
            p_status = fix_arabic(row['الحالة'])
        else:
            p_name = "Upload arial.ttf to GitHub"
            p_status = str(row['الحالة'])
            
        pdf.cell(40, 10, p_status, 1, align='C')
        pdf.cell(30, 10, str(row['اللجنة']), 1, align='C')
        pdf.cell(30, 10, str(row['الشعبة']), 1, align='C')
        pdf.cell(85, 10, p_name, 1, align='R')
        pdf.ln()
    
    return pdf.output()

# 4. منطق الصفحات
if 'page' not in st.session_state: st.session_state.page = "home"
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- الصفحة الرئيسية ---
if st.session_state.page == "home":
    st.write("<br><br>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style="text-align: center; border: 2px solid #1f77b4; padding: 40 :px; border-radius: 20px; background-color: #f8f9fa; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);">
            <h1 style="color: #1f77b4; margin-bottom: 5px;">برنامج تحضير الغياب</h1>
            <h2 style="margin-top: 0;">مدرسة القطيف الثانوية</h2>
            <hr style="width: 50%; margin: auto;">
            <p style="font-size: 1.2rem; color: #555; margin-top: 15px;">فكرة وبرمجة: <b>أ. عارف أحمد الحداد</b></p>
        </div>
    """, unsafe_allow_html=True)
    
    st.write("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📝 تحضير الطلاب", use_container_width=True, type="primary"):
            st.session_state.page = "attendance"; st.rerun()
    with c2:
        if st.button("⚙️ إدارة التطبيق", use_container_width=True, type="secondary"):
            st.session_state.page = "admin"; st.rerun()

# --- صفحة التحضير ---
elif st.session_state.page == "attendance":
    if st.button("⬅️ العودة للرئيسية"): st.session_state.page = "home"; st.rerun()
    if not get_system_status():
        st.error("🚫 النظام مغلق حالياً من قبل الإدارة.")
    else:
        if not st.session_state.logged_in:
            st.subheader("🔐 دخول المعلم")
            nid = st.text_input("أدخل رقم السجل المدني:", type="password")
            if st.button("دخول"):
                res = supabase.table("teachers").select("*").eq("national_id", nid.strip()).execute()
                if res.data:
                    st.session_state.logged_in = True
                    st.session_state.teacher_name = res.data[0].get('name_tech', 'المعلم')
                    st.rerun()
                else: st.error("السجل المدني غير مسجل في النظام.")
        else:
            st.success(f"مرحباً أستاذ: {st.session_state.teacher_name}")
            t_date = st.date_input("📅 تاريخ التحضير", datetime.now())
            s_data = supabase.table('students').select("committee").execute()
            coms = sorted(list(set([str(i['committee']) for i in s_data.data if i['committee']])), key=smart_sort)
            sel_c = st.selectbox("🎯 اختر اللجنة:", ["---"] + coms)
            
            if sel_c != "---":
                students = supabase.table('students').select("*").eq('committee', sel_c).execute()
                results = []
                for s in students.data:
                    col_name, col_status = st.columns([2, 1])
                    col_name.write(f"👤 {s['student_name']}")
                    stat = col_status.radio("الحالة", ["حاضر", "غائب", "متأخر"], key=f"s_{s['id']}", horizontal=True)
                    results.append({"student_name": s['student_name'], "committee": sel_c, "status": stat, "date": str(t_date), "teacher_name": st.session_state.teacher_name})
                
                if st.button("💾 حفظ الكشف"):
                    supabase.table('attendance').delete().eq('committee', sel_c).eq('date', str(t_date)).execute()
                    supabase.table('attendance').insert(results).execute()
                    st.success("✅ تم حفظ الغياب بنجاح!"); time.sleep(1)
                    st.session_state.logged_in = False; st.session_state.page = "home"; st.rerun()

# --- صفحة الإدارة ---
elif st.session_state.page == "admin":
    if st.button("⬅️ العودة للرئيسية"): st.session_state.page = "home"; st.rerun()
    pw = st.text_input("🔑 كلمة مرور الإدارة", type="password")
    if pw == "1234":
        st.header("📊 لوحة التقارير")
        rep_date = st.date_input("اختر تاريخ التقرير", datetime.now())
        
        att = supabase.table('attendance').select("*").eq('date', str(rep_date)).execute()
        std = supabase.table('students').select("student_name, section, committee").execute()

        if att.data:
            df_a, df_s = pd.DataFrame(att.data), pd.DataFrame(std.data)
            m = pd.merge(df_a, df_s, on='student_name', how='left')
            final = m[m['status'].isin(['غائب', 'متأخر'])][['student_name', 'section', 'committee_x', 'status']]
            final.columns = ['الاسم', 'الشعبة', 'اللجنة', 'الحالة']
            
            st.dataframe(final, use_container_width=True)

            # واتساب
            msg = f"*تقرير الغياب - مدرسة القطيف الثانوية*\n*التاريخ:* {rep_date}\n\n"
            for _, r in final.iterrows():
                msg += f"• *{r['الاسم']}* | {r['الحالة']}\n"
            
            wa_link = f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg)}"
            st.link_button("📱 إرسال عبر الواتساب (Web/Business)", wa_link, use_container_width=True)

            # PDF
            if not os.path.exists("arial.ttf"):
                st.warning("⚠️ يرجى رفع ملف arial.ttf إلى GitHub لتظهر الأسماء العربية في الـ PDF.")
            
            if st.button("📄 توليد ملف PDF للتحميل", use_container_width=True):
                pdf_bytes = create_pdf(final, rep_date)
                st.download_button(
                    label="⬇️ اضغط هنا لتحميل الملف",
                    data=pdf_bytes,
                    file_name=f"غياب_{rep_date}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        else:
            st.info("لا توجد بيانات غياب مسجلة لهذا التاريخ.")
    else: st.info("الرجاء إدخال كلمة المرور للوصول للتقارير.")
