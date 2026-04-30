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

# 2. تنسيق الواجهة
st.set_page_config(page_title="نظام غياب مدرسة القطيف الثانوية", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display: none !important;}
    
    button[kind="primary"] {
        background-color: #ADD8E6 !important;
        color: #000 !important;
        border: 2px solid #ADD8E6 !important;
        font-weight: bold;
    }
    button[kind="secondary"] {
        background-color: #FFA500 !important;
        color: #fff !important;
        border: 2px solid #FFA500 !important;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. الدوال المساعدة
def smart_sort(x):
    try: return int(x)
    except: return str(x)

def fix_arabic(text):
    try:
        reshaped = reshape(str(text))
        return get_display(reshaped)
    except: return str(text)

def create_pdf(df, report_date):
    pdf = FPDF()
    pdf.add_page()
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(current_dir, "arial.ttf")
    
    has_font = False
    if os.path.exists(font_path):
        try:
            pdf.add_font("ArabicFont", "", font_path)
            pdf.set_font("ArabicFont", size=12)
            has_font = True
        except: has_font = False
    
    if has_font:
        pdf.set_font("ArabicFont", size=16)
        pdf.cell(200, 10, txt=fix_arabic(f"تقرير الغياب ليوم {report_date}"), ln=True, align='C')
        pdf.ln(10)
        pdf.cell(30, 10, fix_arabic("الحالة"), 1, align='C')
        pdf.cell(30, 10, fix_arabic("الشعبة"), 1, align='C')
        pdf.cell(130, 10, fix_arabic("الاسم"), 1, align='C')
        pdf.ln()
        for _, row in df.iterrows():
            pdf.cell(30, 10, fix_arabic(row['الحالة']), 1, align='C')
            pdf.cell(30, 10, fix_arabic(row['الشعبة']), 1, align='C')
            pdf.cell(130, 10, fix_arabic(row['الاسم']), 1, align='R')
            pdf.ln()
    else:
        pdf.set_font("Arial", size=14)
        pdf.cell(200, 10, txt=f"Attendance Report - {report_date}", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", size=10)
        pdf.cell(190, 10, txt="Font Error: Arabic names display in App only.", ln=True, align='C')
            
    return pdf.output()

# 4. التنقل بين الصفحات
if 'page' not in st.session_state: st.session_state.page = "home"
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# الصفحة الرئيسية
if st.session_state.page == "home":
    st.write("<br><br>", unsafe_allow_html=True)
    st.markdown("""
        <div style="text-align: center; border: 2px solid #1f77b4; padding: 30px; border-radius: 15px; background-color: #f8f9fa;">
            <h1 style="color: #1f77b4;">برنامج تحضير الغياب الرقمي</h1>
            <h2>مدرسة القطيف الثانوية</h2>
            <hr style="width: 40%; margin: auto;">
            <p style="margin-top:10px;">إشراف: <b>أ. عارف أحمد الحداد</b></p>
        </div>
    """, unsafe_allow_html=True)
    
    st.write("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 تحضير الطلاب اليومي", use_container_width=True, type="primary"):
            st.session_state.page = "attendance"; st.rerun()
    with col2:
        if st.button("⚙️ لوحة تحكم الإدارة", use_container_width=True, type="secondary"):
            st.session_state.page = "admin"; st.rerun()

# صفحة التحضير
elif st.session_state.page == "attendance":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    
    if not st.session_state.logged_in:
        nid = st.text_input("أدخل السجل المدني للمعلم:", type="password")
        if st.button("تسجيل الدخول"):
            res = supabase.table("teachers").select("*").eq("national_id", nid.strip()).execute()
            if res.data:
                st.session_state.logged_in = True
                st.session_state.teacher_name = res.data[0].get('name_tech', 'المعلم')
                st.rerun()
            else: st.error("عذراً، السجل غير مسجل.")
    else:
        st.info(f"المعلم المسؤول: {st.session_state.teacher_name}")
        t_date = st.date_input("تاريخ اليوم", datetime.now())
        s_data = supabase.table('students').select("committee").execute()
        coms = sorted(list(set([str(i['committee']) for i in s_data.data if i['committee']])), key=smart_sort)
        sel_c = st.selectbox("اختر اللجنة المراد تحضيرها:", ["---"] + coms)
        
        if sel_c != "---":
            students = supabase.table('students').select("*").eq('committee', sel_c).execute()
            results = []
            for s in students.data:
                c1, c2 = st.columns([2, 1])
                c1.write(f"👤 {s['student_name']}")
                stat = c2.radio("الحالة", ["حاضر", "غائب", "متأخر"], key=f"st_{s['id']}", horizontal=True)
                results.append({"student_name": s['student_name'], "committee": sel_c, "status": stat, "date": str(t_date), "teacher_name": st.session_state.teacher_name})
            
            if st.button("💾 اعتماد وحفظ الكشف"):
                supabase.table('attendance').delete().eq('committee', sel_c).eq('date', str(t_date)).execute()
                supabase.table('attendance').insert(results).execute()
                st.success("✅ تم حفظ البيانات بنجاح!"); time.sleep(1)
                st.session_state.page = "home"; st.session_state.logged_in = False; st.rerun()

# صفحة الإدارة
elif st.session_state.page == "admin":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    pw = st.text_input("كلمة مرور الإدارة:", type="password")
    if pw == "1234":
        st.subheader("📊 استخراج تقارير الغياب")
        rep_date = st.date_input("تاريخ التقرير المطلوب", datetime.now())
        att = supabase.table('attendance').select("*").eq('date', str(rep_date)).execute()
        
        if att.data:
            df_att = pd.DataFrame(att.data)
            std = supabase.table('students').select("student_name, section, committee").execute()
            df_s = pd.DataFrame(std.data)
            
            final = pd.merge(df_att, df_s, on='student_name', how='left')
            # فلترة الغائبين والمتأخرين فقط
            final = final[final['status'].isin(['غائب', 'متأخر'])]
            
            display_df = final[['student_name', 'section', 'committee_y', 'status']]
            display_df.columns = ['الاسم', 'الشعبة', 'اللجنة', 'الحالة']
            
            st.table(display_df)
            
            # صياغة رسالة الواتساب المطلوبة
            msg = f"*تقرير غياب مدرسة القطيف الثانوية*\n"
            msg += f"*التاريخ:* {rep_date}\n"
            msg += "--------------------------\n"
            
            for _, r in display_df.iterrows():
                msg += f"👤 *الاسم:* {r['الاسم']}\n"
                msg += f"🏫 *الشعبة:* {r['الشعبة']}\n"
                msg += f"📦 *اللجنة:* {r['اللجنة']}\n"
                msg += f"📍 *الحالة:* {r['الحالة']}\n"
                msg += "--------------------------\n"
            
            encoded_msg = urllib.parse.quote(msg)
            wa_link = f"https://wa.me/?text={encoded_msg}"
            
            st.markdown(f"""
                <a href="{wa_link}" target="_blank" style="text-decoration: none;">
                    <div style="background-color: #25D366; color: white; padding: 15px; border-radius: 10px; text-align: center; font-weight: bold; cursor: pointer; font-size: 18px;">
                        📱 إرسال التقرير عبر الواتساب (عادي / أعمال)
                    </div>
                </a>
            """, unsafe_allow_html=True)
            
            st.write("<br>", unsafe_allow_html=True)
            
            if st.button("📄 إصدار تقرير PDF للتحميل", use_container_width=True):
                try:
                    pdf_output = create_pdf(display_df, rep_date)
                    st.download_button(
                        label="⬇️ تحميل ملف PDF",
                        data=bytes(pdf_output),
                        file_name=f"تقرير_غياب_{rep_date}.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"حدث خطأ في الـ PDF: {e}")
        else:
            st.warning("لا توجد سجلات غياب لهذا التاريخ.")
