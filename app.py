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

# 2. هندسة الواجهة والتنسيق (توسيط كامل)
st.set_page_config(page_title="نظام غياب مدرسة القطيف الثانوية", layout="centered")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display: none !important;}
    .stApp { background-color: #f9fbff; }
    .center-text { text-align: center !important; direction: rtl; width: 100%; }
    .main-title { font-size: 35px !important; font-weight: 800; color: #2c3e50; }
    .label-style { font-size: 22px !important; color: #78909c; font-weight: bold; }
    .name-style { font-size: 32px !important; color: #1e88e5; font-weight: 900; }
    
    /* توسيط الأزرار */
    .stButton { display: flex; justify-content: center; }
    .stButton button { 
        width: 100% !important; 
        max-width: 350px !important; 
        height: 55px !important; 
        border-radius: 12px !important; 
        font-size: 20px !important; 
        font-weight: bold; 
        margin: 10px auto !important; 
        display: block; 
    }
    button[kind="primary"] { background-color: #3498db !important; color: white !important; }
    button[kind="secondary"] { background-color: #cfd8dc !important; color: #455a64 !important; }
    
    /* تنسيق الجداول لتكون من اليمين لليسار */
    div[data-testid="stDataFrame"] { direction: rtl !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. إدارة التنقل
if 'page' not in st.session_state: st.session_state.page = "home"
if 'admin_logged_in' not in st.session_state: st.session_state.admin_logged_in = False

# --- الصفحة الرئيسية ---
if st.session_state.page == "home":
    st.markdown('<div class="center-text">', unsafe_allow_html=True)
    st.markdown('<div class="main-title">برنامج التحضير الرقمي</div>', unsafe_allow_html=True)
    st.markdown('<div class="label-style">فكرة وتنفيذ</div>', unsafe_allow_html=True)
    st.markdown('<div class="name-style">أ. عارف أحمد الحداد</div>', unsafe_allow_html=True)
    st.markdown('<div class="label-style">مدير المدرسة</div>', unsafe_allow_html=True)
    st.markdown('<div class="name-style">أ. فراس عبدالله آل عبدالمحسن</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("📝 ابدأ تحضير الطلاب", type="primary"):
        st.session_state.page = "attendance"; st.rerun()
    if st.button("⚙️ دخول لوحة التحكم", type="secondary"):
        st.session_state.page = "admin_login"; st.rerun()

# --- صفحة تسجيل دخول الإدارة ---
elif st.session_state.page == "admin_login":
    if st.button("⬅️ عودة"):
        st.session_state.page = "home"; st.rerun()
    st.markdown('<div class="center-text label-style">كلمة مرور الإدارة</div>', unsafe_allow_html=True)
    pw = st.text_input("أدخل الرمز:", type="password")
    if pw == "1234":
        st.session_state.admin_logged_in = True
        st.session_state.page = "admin_panel"; st.rerun()

# --- لوحة التحكم وعرض الغياب المفلتر ---
elif st.session_state.page == "admin_panel":
    if st.button("⬅️ خروج"):
        st.session_state.admin_logged_in = False; st.session_state.page = "home"; st.rerun()
    
    st.markdown('<div class="center-text main-title">لوحة التحكم</div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📊 تقارير الغياب والتأخر", "🗂️ إدارة البيانات"])
    
    with tab1:
        st.markdown('<div class="center-text label-style">استعراض كشوف (غائب / متأخر)</div>', unsafe_allow_html=True)
        search_date = st.date_input("اختر التاريخ:", datetime.now())
        
        if st.button("🔍 عرض التقرير"):
            # جلب البيانات
            response = supabase.table("attendance").select("*").eq("date", str(search_date)).execute()
            
            if response.data:
                df = pd.DataFrame(response.data)
                
                # --- الفلترة المطلوبة: استبعاد "حاضر" ---
                # سيعرض فقط الطلاب الذين حالتهم "غائب" أو "متأخر"
                df_filtered = df[df['status'].isin(['غائب', 'متأخر'])]
                
                if not df_filtered.empty:
                    # ترتيب وتنسيق الأعمدة
                    df_display = df_filtered[['student_name', 'status', 'committee', 'teacher_name']]
                    df_display.columns = ['اسم الطالب', 'الحالة', 'اللجنة', 'المعلم المحضر']
                    
                    st.success(f"تم العثور على {len(df_filtered)} حالات (غياب/تأخر)")
                    st.dataframe(df_display, use_container_width=True, hide_index=True)
                    
                    # خيار التحميل
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df_display.to_excel(writer, index=False, sheet_name='الغياب')
                    st.download_button(
                        label="📥 تحميل تقرير الغياب (Excel)",
                        data=output.getvalue(),
                        file_name=f"تقرير_غياب_{search_date}.xlsx",
                        mime="application/vnd.ms-excel"
                    )
                else:
                    st.balloons()
                    st.success("ما شاء الله! لا يوجد غياب أو تأخر في هذا اليوم (الجميع حاضر).")
            else:
                st.warning("لا توجد بيانات غياب مسجلة لهذا التاريخ.")

    with tab2:
        st.info("قسم إدارة البيانات والرفع.")
