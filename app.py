import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
import urllib.parse  # لتنسيق نصوص الروابط بشكل صحيح

# 1. إعدادات الاتصال وقاعدة البيانات
url = "https://lsmevvsogsqqqjyuqzbx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzbWV2dnNvZ3NxcXFqeXVxemJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MDMyOTgsImV4cCI6MjA5Mjk3OTI5OH0.ecqJS75fPbKqwSAiBzP6Qonn4cuymgwjB96tIGek8j0"

if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(url, key)
supabase = st.session_state.supabase

# --- 🎨 منطقة التنسيق المخفية (إضافة تنسيقات الأزرار) ---
STYLE_CSS = '''
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .stButton>button { border-radius: 10px; font-weight: bold; height: 50px; width: 100%; font-size: 18px; }
    
    /* تنسيق أزرار الواتساب */
    .wa-link { 
        text-decoration: none; 
        color: white !important; 
        display: block; 
        text-align: center; 
        padding: 15px; 
        border-radius: 10px; 
        font-weight: bold; 
        margin-bottom: 10px;
        transition: 0.3s;
    }
    .wa-absent { background-color: #dc3545; } /* أحمر للغائبين */
    .wa-late { background-color: #fd7e14; }   /* برتقالي للمتأخرين */
    .wa-link:hover { opacity: 0.8; transform: scale(0.98); }
    
    th { background-color: #1a237e !important; color: white !important; text-align: center !important; }
    td { text-align: center !important; }
    </style>
'''

st.set_page_config(page_title="نظام مدرسة القطيف التقني", layout="wide")
st.markdown(STYLE_CSS, unsafe_allow_html=True)

# --- 🛠️ دالة بناء روابط الواتساب ---
def create_whatsapp_link(df, status_type, report_date):
    if df.empty:
        return None
    
    # رأس الرسالة
    emoji = "🔴" if status_type == "غائب" else "⏳"
    title = "قائمة الغياب" if status_type == "غائب" else "قائمة التأخر الصباحي"
    
    message = f"*{emoji} {title}*\n"
    message += f"📅 *التاريخ:* {report_date}\n"
    message += "---------------------------\n"
    
    # تفاصيل الطلاب
    for _, row in df.iterrows():
        message += f"📦 *لجنة:* {row['committee']}\n"
        message += f"👤 *الطالب:* {row['student_name']}\n"
        message += f"🏫 *الشعبة:* {row.get('الشعبة', 'غير محدد')}\n"
        message += "---------------------------\n"
    
    message += "✅ *تم الرصد عبر نظام مدرسة القطيف التقني*"
    
    # تحويل النص لرابط متوافق مع المتصفحات
    encoded_message = urllib.parse.quote(message)
    return f"https://wa.me/?text={encoded_message}"

# --- لوحة الإدارة والتقارير ---
if 'page' not in st.session_state: st.session_state.page = "home"

# (بقية كود التنقل تظل كما هي، سنركز على قسم التقارير في Admin)
if st.session_state.page == "admin":
    st.title("⚙️ لوحة الإدارة")
    tab1, tab2, tab3 = st.tabs(["📊 التقارير الموحدة", "🏘️ حالة اللجان", "💾 إدارة البيانات"])

    with tab1:
        d = st.date_input("اختر تاريخ التقرير:", datetime.now())
        res_att = supabase.table("attendance").select("*").eq("date", str(d)).execute()
        
        if res_att.data:
            df_all = pd.DataFrame(res_att.data)
            
            # جلب بيانات الشعب لكل طالب من جدول الطلاب
            res_std = supabase.table("students").select("student_name, class_name").execute()
            if res_std.data:
                df_std_info = pd.DataFrame(res_std.data)
                s_map = dict(zip(df_std_info['student_name'], df_std_info['class_name']))
                df_all['الشعبة'] = df_all['student_name'].map(s_map).fillna("---")

            # تقسيم البيانات حسب الحالة
            df_absent = df_all[df_all['status'] == "غائب"]
            df_late = df_all[df_all['status'] == "متأخر"]

            st.write("### 📄 عرض الحالات")
            st.dataframe(df_all[df_all['status'].isin(['غائب', 'متأخر'])][['committee', 'student_name', 'الشعبة', 'status']], use_container_width=True)

            st.divider()
            st.write("### 📲 إرسال التقارير عبر WhatsApp")
            
            col1, col2 = st.columns(2)
            
            with col1:
                link_absent = create_whatsapp_link(df_absent, "غائب", d)
                if link_absent:
                    st.markdown(f'<a href="{link_absent}" target="_blank" class="wa-link wa-absent">🚫 إرسال قائمة الغائبين ({len(df_absent)})</a>', unsafe_allow_html=True)
                else:
                    st.info("لا يوجد غائبين اليوم")

            with col2:
                link_late = create_whatsapp_link(df_late, "متأخر", d)
                if link_late:
                    st.markdown(f'<a href="{link_late}" target="_blank" class="wa-link wa-late">⏳ إرسال قائمة المتأخرين ({len(df_late)})</a>', unsafe_allow_html=True)
                else:
                    st.info("لا يوجد متأخرين اليوم")
        else:
            st.warning("لا توجد سجلات رصد لهذا التاريخ.")
