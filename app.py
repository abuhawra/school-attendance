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

# 2. تحسين مظهر الصفحة بالكامل وتكبير الخطوط
st.set_page_config(page_title="نظام غياب مدرسة القطيف الثانوية", layout="centered")

st.markdown("""
    <style>
    /* إخفاء القوائم والترويسات */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* جعل جميع النصوص في المنتصف وخط واضح */
    .stMarkdown, div[data-testid="stText"], h1, h2, h3, p, span {
        text-align: center !important;
        direction: rtl;
    }
    
    /* تنسيق الحاوية الرئيسية */
    .stApp {
        background-color: #f0f2f6;
    }

    /* تكبير حجم الخط للعناوين الفرعية (فكرة وتنفيذ / مدير المدرسة) */
    .stCaption {
        font-size: 20px !important;
        color: #555 !important;
        font-weight: bold !important;
    }

    /* تكبير حجم الخط للأسماء */
    h3 {
        font-size: 28px !important;
        color: #1f77b4 !important;
        margin-top: 5px !important;
        margin-bottom: 20px !important;
    }
    
    /* تنسيق الأزرار وتوسيطها */
    div.stButton {
        display: flex;
        justify-content: center;
    }

    div.stButton > button {
        width: 100%;
        max-width: 380px; /* تحديد عرض أقصى للزر ليكون متناسقاً */
        height: 65px;
        border-radius: 15px;
        font-size: 22px !important;
        font-weight: bold;
        margin: 10px auto;
    }
    
    /* لون زر التحضير */
    button[kind="primary"] {
        background-color: #4A90E2 !important;
        color: white !important;
        border: none;
    }
    
    /* لون زر الإدارة */
    button[kind="secondary"] {
        background-color: #7B8D9E !important;
        color: white !important;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. إدارة الصفحات
if 'page' not in st.session_state: st.session_state.page = "home"
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- الصفحة الرئيسية (توسيط وتكبير الخطوط) ---
if st.session_state.page == "home":
    st.write("<br>", unsafe_allow_html=True)
    st.title("برنامج التحضير الرقمي")
    st.header("مدرسة القطيف الثانوية")
    
    st.divider() 
    
    # عرض الأسماء بخط عريض وواضح
    st.caption("فكرة وتنفيذ")
    st.subheader("أ. عارف أحمد الحداد")
    
    st.caption("مدير المدرسة")
    st.subheader("أ. فراس عبدالله آل عبدالمحسن")
    
    st.divider()
    st.write("<br>", unsafe_allow_html=True)
    
    # الأزرار الرئيسية موسطة تلقائياً عبر CSS
    if st.button("📝 ابدأ تحضير الطلاب", type="primary"):
        st.session_state.page = "attendance"; st.rerun()
    
    if st.button("⚙️ دخول لوحة التحكم", type="secondary"):
        st.session_state.page = "admin"; st.rerun()

# --- صفحة التحضير ---
elif st.session_state.page == "attendance":
    if st.button("⬅️ عودة"):
        st.session_state.page = "home"; st.rerun()
        
    if not st.session_state.logged_in:
        st.info("الرجاء تسجيل الدخول للمتابعة")
        nid = st.text_input("أدخل السجل المدني للمعلم:", type="password")
        if st.button("دخول"):
            res = supabase.table("teachers").select("*").eq("national_id", nid.strip()).execute()
            if res.data:
                st.session_state.logged_in = True
                st.session_state.teacher_name = res.data[0].get('name_tech', 'المعلم')
                st.rerun()
            else:
                st.error("السجل المدني غير مسجل في النظام")
    else:
        st.write(f"المعلم المسؤول: **{st.session_state.teacher_name}**")
        t_date = st.date_input("تاريخ اليوم", datetime.now())
        
        s_data = supabase.table('students').select("committee").execute()
        coms = sorted(list(set([str(i['committee']) for i in s_data.data if i['committee']])), key=lambda x: int(x) if x.isdigit() else x)
        sel_c = st.selectbox("اختر اللجنة المراد تحضيرها:", ["---"] + coms)
        
        if sel_c != "---":
            students = supabase.table('students').select("*").eq('committee', sel_c).execute()
            results = []
            
            for s in students.data:
                st.markdown(f"**{s['student_name']}**")
                stat = st.radio("الحالة", ["حاضر", "غائب", "متأخر"], key=f"st_{s['id']}", horizontal=True)
                results.append({
                    "student_name": s['student_name'], 
                    "committee": sel_c, 
                    "status": stat, 
                    "date": str(t_date), 
                    "teacher_name": st.session_state.teacher_name
                })
            
            if st.button("💾 حفظ وإرسال البيانات"):
                supabase.table('attendance').delete().eq('committee', sel_c).eq('date', str(t_date)).execute()
                supabase.table('attendance').insert(results).execute()
                st.success("تم حفظ كشف الغياب بنجاح!")
                time.sleep(2)
                st.session_state.page = "home"; st.session_state.logged_in = False; st.rerun()

# --- صفحة الإدارة ---
elif st.session_state.page == "admin":
    if st.button("⬅️ عودة"):
        st.session_state.page = "home"; st.rerun()
        
    pw = st.text_input("كلمة مرور الإدارة:", type="password")
    if pw == "1234":
        tab1, tab2 = st.tabs(["📊 التقارير", "🗂️ إدارة البيانات"])
        
        with tab1:
            rep_date = st.date_input("عرض تقرير يوم:", datetime.now())
            att_data = supabase.table('attendance').select("*").eq('date', str(rep_date)).execute()
            if att_data.data:
                df = pd.DataFrame(att_data.data)
                st.dataframe(df[['student_name', 'status', 'committee']], use_container_width=True)
            else:
                st.warning("لا توجد بيانات غياب لهذا اليوم.")

        with tab2:
            st.write("إدارة قاعدة بيانات المعلمين والطلاب")
