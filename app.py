import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
import urllib.parse
import io

# 1. إعدادات الاتصال بقاعدة البيانات
url = "https://lsmevvsogsqqqjyuqzbx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzbWV2dnNvZ3NxcXFqeXVxemJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MDMyOTgsImV4cCI6MjA5Mjk3OTI5OH0.ecqJS75fPbKqwSAiBzP6Qonn4cuymgwjB96tIGek8j0"

if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(url, key)
supabase = st.session_state.supabase

# 2. هندسة الواجهة والألوان الهادئة
st.set_page_config(page_title="نظام غياب مدرسة القطيف الثانوية", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;700&display=swap');

    /* تطبيق الخط وتنسيق الخلفية */
    html, body, [class*="st-"] {
        font-family: 'Tajawal', sans-serif;
        text-align: center;
    }
    
    .stApp {
        background-color: #F0F4F8; /* رمادي مائل للأزرق هادئ جداً */
    }

    /* إخفاء القوائم غير الضرورية */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* حاوية الغلاف الرئيسي */
    .hero-container {
        background: white;
        padding: 40px 20px;
        border-radius: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 30px;
        border-top: 8px solid #3498db;
    }

    .main-title {
        color: #2c3e50;
        font-size: 30px;
        font-weight: 700;
        margin-bottom: 5px;
    }
    
    .school-name {
        color: #5a67d8;
        font-size: 20px;
        font-weight: 400;
        margin-bottom: 25px;
    }

    .info-box {
        background-color: #f8fafc;
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
    }

    .label-text {
        color: #7f8c8d;
        font-size: 14px;
        margin-bottom: 5px;
    }
    
    .name-text {
        color: #2c3e50;
        font-size: 19px;
        font-weight: 700;
    }

    /* تنسيق الأزرار بشكل عصري */
    div.stButton > button {
        width: 100%;
        max-width: 350px;
        height: 58px;
        font-size: 18px !important;
        font-weight: 700 !important;
        border-radius: 15px !important;
        transition: all 0.3s ease;
        border: none !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 12px auto;
        display: block;
    }

    /* زر التحضير - أزرق هادئ */
    button[kind="primary"] {
        background-color: #3498db !important;
        color: white !important;
    }
    button[kind="primary"]:hover {
        background-color: #2980b9 !important;
        transform: translateY(-2px);
    }

    /* زر الإدارة - ذهبي هادئ */
    button[kind="secondary"] {
        background-color: #f1c40f !important;
        color: #2c3e50 !important;
    }
    button[kind="secondary"]:hover {
        background-color: #f39c12 !important;
        transform: translateY(-2px);
    }
    </style>
    """, unsafe_allow_html=True)

# 3. إدارة الجلسة والتنقل
if 'page' not in st.session_state: st.session_state.page = "home"
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- الصفحة الرئيسية (التصميم الجديد الجذاب) ---
if st.session_state.page == "home":
    st.write("<br>", unsafe_allow_html=True)
    
    # حاوية الغلاف
    st.markdown("""
        <div class="hero-container">
            <div class="main-title">برنامج التحضير الرقمي</div>
            <div class="school-name">مدرسة القطيف الثانوية</div>
            
            <div class="info-box">
                <div class="label-text">فكرة وتنفيذ</div>
                <div class="name-text">أ. عارف أحمد الحداد</div>
            </div>
            
            <div class="info-box">
                <div class="label-text">مدير المدرسة</div>
                <div class="name-text">أ. فراس عبدالله آل عبدالمحسن</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # الأزرار في المنتصف
    if st.button("📝 ابدأ تحضير الطلاب", type="primary"):
        st.session_state.page = "attendance"; st.rerun()
    
    if st.button("⚙️ دخول لوحة التحكم", type="secondary"):
        st.session_state.page = "admin"; st.rerun()

# --- صفحة التحضير ---
elif st.session_state.page == "attendance":
    if st.button("⬅️ عودة للرئيسية"): st.session_state.page = "home"; st.rerun()
    if not st.session_state.logged_in:
        st.markdown("### تسجيل دخول المعلم")
        nid = st.text_input("أدخل السجل المدني:", type="password")
        if st.button("دخول"):
            res = supabase.table("teachers").select("*").eq("national_id", nid.strip()).execute()
            if res.data:
                st.session_state.logged_in = True
                st.session_state.teacher_name = res.data[0].get('name_tech', 'المعلم')
                st.rerun()
            else: st.error("عذراً، البيانات غير صحيحة.")
    else:
        st.success(f"مرحباً أ. {st.session_state.teacher_name}")
        t_date = st.date_input("تاريخ اليوم", datetime.now())
        s_data = supabase.table('students').select("committee").execute()
        coms = sorted(list(set([str(i['committee']) for i in s_data.data if i['committee']])), key=lambda x: int(x) if x.isdigit() else x)
        sel_c = st.selectbox("اختر اللجنة:", ["---"] + coms)
        
        if sel_c != "---":
            students = supabase.table('students').select("*").eq('committee', sel_c).execute()
            results = []
            for s in students.data:
                st.markdown(f"**👤 {s['student_name']}**")
                stat = st.radio("الحالة:", ["حاضر", "غائب", "متأخر"], key=f"st_{s['id']}", horizontal=True)
                results.append({"student_name": s['student_name'], "committee": sel_c, "status": stat, "date": str(t_date), "teacher_name": st.session_state.teacher_name})
            
            if st.button("💾 حفظ الكشف نهائياً"):
                supabase.table('attendance').delete().eq('committee', sel_c).eq('date', str(t_date)).execute()
                supabase.table('attendance').insert(results).execute()
                st.balloons()
                st.success("تم حفظ البيانات بنجاح!")
                time.sleep(2)
                st.session_state.page = "home"; st.session_state.logged_in = False; st.rerun()

# --- صفحة الإدارة ---
elif st.session_state.page == "admin":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    pw = st.text_input("كلمة مرور المدير:", type="password")
    if pw == "1234":
        tab1, tab2, tab3 = st.tabs(["📊 تقارير الغياب", "🗂️ قاعدة البيانات", "⚙️ الإعدادات"])
        
        with tab1:
            rep_date = st.date_input("اختر التاريخ", datetime.now())
            att = supabase.table('attendance').select("*").eq('date', str(rep_date)).execute()
            if att.data:
                df = pd.DataFrame(att.data)
                st.dataframe(df[['student_name', 'status', 'committee']], use_container_width=True)
                if st.button("📱 إرسال ملخص عبر واتساب"):
                    msg = f"تقرير غياب يوم {rep_date}"
                    st.markdown(f'[اضغط هنا للإرسال](https://wa.me/?text={urllib.parse.quote(msg)})')

        with tab2:
            st.write("إدارة أسماء الطلاب واللجان")
            # أزرار النسخ الاحتياطي مبسطة هنا كما في الإصدار السابق
            
        with tab3:
            if st.button("❌ تفريغ سجلات اليوم"):
                supabase.table('attendance').delete().eq('date', str(datetime.now().date())).execute()
                st.success("تم تنظيف السجلات.")
