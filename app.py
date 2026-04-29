import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
import urllib.parse

# إعدادات الاتصال بقاعدة البيانات
url = "https://lsmevvsogsqqqjyuqzbx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzbWV2dnNvZ3NxcXFqeXVxemJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MDMyOTgsImV4cCI6MjA5Mjk3OTI5OH0.ecqJS75fPbKqwSAiBzP6Qonn4cuymgwjB96tIGek8j0"

if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(url, key)
supabase = st.session_state.supabase

st.set_page_config(page_title="نظام غياب الطلاب - أ. عارف الحداد", layout="wide")

# --- لوحة الإدارة ---
st.header("📊 لوحة الإدارة والتقارير")
if st.sidebar.text_input("كلمة المرور", type="password") == "1234":
    report_date = st.date_input("📅 اختر تاريخ التقرير", datetime.now())

    # جلب البيانات من الجداول
    att_res = supabase.table('attendance').select("student_name, status, committee").eq('date', str(report_date)).execute()
    std_res = supabase.table('students').select("student_name, section").execute()

    if att_res.data:
        att_df = pd.DataFrame(att_res.data)
        std_df = pd.DataFrame(std_res.data)
        
        # دمج البيانات للحصول على الشعبة
        merged_df = pd.merge(att_df, std_df, on='student_name', how='left')
        
        # تصفية الغائبين والمتأخرين
        detailed_df = merged_df[merged_df['status'].isin(['غائب', 'متأخر'])]
        
        if not detailed_df.empty:
            st.table(detailed_df[['student_name', 'section', 'committee', 'status']].rename(columns={
                'student_name': 'اسم الطالب', 'section': 'الشعبة', 'committee': 'اللجنة', 'status': 'الحالة'
            }))

            # --- أزرار الإرسال ---
            col1, col2 = st.columns(2)
            
            with col1:
                # ميزة الواتساب التفصيلي الجديدة
                wa_header = f"*تقرير الغياب التفصيلي ليوم {report_date}*\n\n"
                wa_body = ""
                for _, row in detailed_df.iterrows():
                    wa_body += f"👤 *الطالب:* {row['student_name']}\n"
                    wa_body += f"🏢 *الشعبة:* {row['section']}\n"
                    wa_body += f"🎯 *اللجنة:* {row['committee']}\n"
                    wa_body += f"🚩 *الحالة:* {row['status']}\n"
                    wa_body += "--------------------------\n"
                
                full_msg = wa_header + wa_body
                wa_url = f"https://wa.me/?text={urllib.parse.quote(full_msg)}"
                st.link_button("📱 إرسال الكشف التفصيلي عبر واتساب", wa_url, use_container_width=True)

            with col2:
                # زر التقرير الصوري/PDF كما في الصور السابقة
                if st.button("📄 تصدير الكشف (PDF/طباعة)", use_container_width=True):
                    st.info("قم بالضغط على Ctrl+P لحفظ الكشف كملف PDF.")
        else:
            st.success("الكل حاضر لهذا اليوم.")
    else:
        st.info("لا توجد بيانات لهذا التاريخ.")
