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

# --- 🎨 التنسيق والـ CSS ---
st.set_page_config(page_title="نظام مدرسة القطيف التقني", layout="wide")
st.markdown('''
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .main-header { 
        background-color: #1a237e; padding: 30px; text-align: center; color: white; 
        border-radius: 20px; margin-bottom: 25px; border-bottom: 8px solid #ffd700; 
    }
    .wa-button { color: white !important; padding: 12px; border-radius: 10px; text-align: center; display: block; text-decoration: none; font-weight: bold; margin-top: 10px; font-size: 16px; }
    .wa-all { background-color: #28a745; }
    .status-active { color: #28a745; font-weight: bold; }
    .status-stop { color: #dc3545; font-weight: bold; }
    </style>
''', unsafe_allow_html=True)

if 'page' not in st.session_state: st.session_state.page = "home"

# --- الصفحة الرئيسية و تسجيل الدخول (تبقي كما هي في الكود السابق) ---
if st.session_state.page == "home":
    st.markdown('''<div class="main-header">
            <h2 style="color:#ffd700; font-size: 65px; font-weight: 800;">بصمة تميز</h2>
            <h2 style="margin:10px 0; font-size: 40px;">مدرسة القطيف الثانوية</h2>
            <h2 style="color:#ffffff; font-size: 24px;">فكرة و برمجة: أ. عارف أحمد الحداد</h2>
        </div>''', unsafe_allow_html=True)
    col_b = st.columns([1, 2, 1])[1]
    with col_b:
        if st.button("📝 رصد غياب الطلاب اليومي", use_container_width=True, type="primary"):
            st.session_state.page = "t_log"; st.rerun()
        st.write("")
        if st.button("⚙️ لوحة الإدارة والتقارير الموحدة", use_container_width=True):
            st.session_state.page = "a_log"; st.rerun()

elif st.session_state.page == "t_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    tid = st.text_input("أدخل السجل المدني:", type="password")
    if st.button("دخول"):
        res = supabase.table("teachers").select("*").eq("national_id", tid.strip()).execute()
        if res.data:
            if res.data[0].get('status') == 'موقوف': st.error("الحساب موقوف")
            else: st.session_state.teacher = res.data[0]['name_tech']; st.session_state.page = "mark"; st.rerun()
        else: st.error("السجل غير مسجل")

# --- واجهة الرصد و التقارير (تبقي كما هي لتركيز الرد على طلبك الجديد) ---
# [ ... كود صفحة mark و admin tab1, tab2, tab3 ... ]

elif st.session_state.page == "a_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    if st.text_input("كلمة مرور الإدارة:", type="password") == "1234": 
        st.session_state.page = "admin"; st.rerun()

elif st.session_state.page == "admin":
    if st.button("⬅️ تسجيل خروج"): st.session_state.page = "home"; st.rerun()
    tab1, tab2, tab3, tab4 = st.tabs(["📊 التقارير", "🏘️ حالة اللجان", "💾 البيانات", "👨‍🏫 إدارة المعلمين"])

    with tab4:
        st.subheader("👨‍🏫 إدارة المعلمين")
        
        # 2. تغيير الكل (موقوف / نشط)
        st.write("🔧 إجراءات جماعية:")
        c_all1, c_all2 = st.columns(2)
        with c_all1:
            if st.button("✅ تنشيط جميع المعلمين", use_container_width=True):
                supabase.table("teachers").update({"status": "نشط"}).neq("id", 0).execute()
                st.success("تم تنشيط الجميع"); time.sleep(1); st.rerun()
        with c_all2:
            if st.button("🚫 إيقاف جميع المعلمين", use_container_width=True):
                supabase.table("teachers").update({"status": "موقوف"}).neq("id", 0).execute()
                st.warning("تم إيقاف الجميع"); time.sleep(1); st.rerun()

        st.divider()

        # 1. قائمة المعلمين مع التحديث
        res_t = supabase.table("teachers").select("*").execute()
        if res_t.data:
            df_t = pd.DataFrame(res_t.data).sort_values('name_tech')
            for index, row in df_t.iterrows():
                t_id = row['id']
                with st.expander(f"👤 {row['name_tech']} - ({row.get('status', 'نشط')})"):
                    # حقول التعديل
                    new_name = st.text_input("الاسم:", value=row['name_tech'], key=f"nm_{t_id}")
                    new_pwd = st.text_input("السجل المدني (الرقم السري):", value=row['national_id'], key=f"pwd_{t_id}")
                    
                    # اختيار الحالة (نشط / موقوف) راديو بدلاً من منسدلة
                    status_options = ["نشط", "موقوف"]
                    current_stat = row.get('status', 'نشط')
                    new_stat = st.radio("حالة المعلم:", status_options, 
                                        index=status_options.index(current_stat) if current_stat in status_options else 0,
                                        key=f"rad_{t_id}", horizontal=True)
                    
                    if st.button("💾 حفظ التعديلات", key=f"save_{t_id}"):
                        try:
                            # تنفيذ التحديث في Supabase
                            update_res = supabase.table("teachers").update({
                                "name_tech": new_name,
                                "national_id": str(new_pwd).strip(),
                                "status": new_stat
                            }).eq("id", t_id).execute()
                            
                            st.success(f"تم تحديث بيانات أ. {new_name}")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"فشل التحديث: {e}")

        # إضافة معلم جديد
        st.divider()
        with st.expander("➕ إضافة معلم جديد للنظام"):
            with st.form("add_teacher_new"):
                add_n = st.text_input("اسم المعلم الكامل:")
                add_i = st.text_input("السجل المدني:")
                if st.form_submit_button("إضافة المعلم"):
                    if add_n and add_i:
                        supabase.table("teachers").insert({"name_tech": add_n, "national_id": add_i, "status": "نشط"}).execute()
                        st.success("تمت الإضافة"); st.rerun()

# --- باقي الأقسام (mark) لضمان اكتمال الكود ---
elif st.session_state.page == "mark":
    # [أضف هنا كود الرصد mark الذي يعمل عندك ليكون الملف كاملاً]
    st.write("واجهة الرصد نشطة...")
    if st.button("العودة"): st.session_state.page = "home"; st.rerun()
