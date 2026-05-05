import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
import io

# 1. إعدادات الاتصال بقاعدة البيانات (Supabase)
url = "https://lsmevvsogsqqqjyuqzbx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzbWV2dnNvZ3NxcXFqeXVxemJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MDMyOTgsImV4cCI6MjA5Mjk3OTI5OH0.ecqJS75fPbKqwSAiBzP6Qonn4cuymgwjB96tIGek8j0"

if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(url, key)
supabase = st.session_state.supabase

# --- 🎨 التنسيق المرئي والـ CSS ---
st.set_page_config(page_title="نظام مدرسة القطيف التقني", layout="wide")
st.markdown('''
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .main-header { 
        background-color: #1a237e; padding: 30px; text-align: center; color: white; 
        border-radius: 20px; margin-bottom: 25px; border-bottom: 8px solid #ffd700; 
    }
    .teacher-card {
        background-color: #ffffff; padding: 15px; border-radius: 12px;
        border: 1px solid #e0e0e0; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .wa-link { text-decoration: none; color: white !important; display: block; text-align: center; padding: 12px; border-radius: 10px; font-weight: bold; margin-bottom: 10px; }
    .wa-absent { background-color: #dc3545; }
    .wa-late { background-color: #fd7e14; }
    </style>
''', unsafe_allow_html=True)

if 'page' not in st.session_state:
    st.session_state.page = "home"

# --- 1. الصفحة الرئيسية ---
if st.session_state.page == "home":
    st.markdown('''
        <div class="main-header">
            <h1 style="color:#ffd700; font-size: 50px; font-weight: 800;">نظام مدرسة القطيف التقني</h1>
            <h2 style="color:#ffffff; font-size: 24px;">إشراف مدير المدرسة: أ. فراس آل عبدالمحسن</h2>
            <h3 style="color:#cfd8dc;">فكرة وبرمجة: أ. عارف أحمد الحداد (أبو محمد)</h3>
        </div>
    ''', unsafe_allow_html=True)
    
    col_b = st.columns([1, 2, 1])[1]
    with col_b:
        if st.button("📝 رصد غياب الطلاب اليومي", use_container_width=True, type="primary"):
            st.session_state.page = "t_log"; st.rerun()
        st.write("")
        if st.button("⚙️ لوحة الإدارة والتحكم الكامل", use_container_width=True):
            st.session_state.page = "a_log"; st.rerun()

# --- 2. تسجيل دخول المعلم ---
elif st.session_state.page == "t_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    tid = st.text_input("أدخل السجل المدني (كلمة المرور):", type="password")
    if st.button("دخول للنظام"):
        res = supabase.table("teachers").select("*").eq("national_id", tid.strip()).execute()
        if res.data:
            if res.data[0].get('status') == 'موقوف':
                st.error("⚠️ عذراً، هذا الحساب موقوف حالياً. راجع الإدارة.")
            else:
                st.session_state.teacher = res.data[0]['name_tech']
                st.session_state.page = "mark"; st.rerun()
        else: st.error("❌ السجل المدني غير مسجل.")

# --- 3. واجهة الرصد (Marking) ---
elif st.session_state.page == "mark":
    today = str(datetime.now().date())
    st.info(f"المعلم: {st.session_state.teacher} | التاريخ: {today}")
    res_s = supabase.table('students').select("committee").execute()
    if res_s.data:
        coms = sorted(list(set([str(i['committee']) for i in res_s.data if i['committee']])), key=lambda x: int(x) if x.isdigit() else 0)
        sel_c = st.selectbox("اختر اللجنة المراد رصدها:", ["---"] + coms)
        if sel_c != "---":
            students = supabase.table('students').select("*").eq("committee", sel_c).execute()
            old_att = supabase.table('attendance').select("*").eq("committee", sel_c).eq("date", today).execute()
            old_map = {i['student_name']: i['status'] for i in old_att.data}
            
            results = []
            for s in students.data:
                prev = old_map.get(s['student_name'], "حاضر")
                choice = st.radio(f"👤 {s['student_name']}", ["حاضر", "غائب", "متأخر"], 
                                  index=["حاضر", "غائب", "متأخر"].index(prev), 
                                  key=f"att_{s['student_name']}", horizontal=True)
                results.append({"student_name": s['student_name'], "committee": str(sel_c), "status": choice, "date": today, "teacher_name": st.session_state.teacher})
            
            if st.button("💾 حفظ الرصد النهائي", use_container_width=True):
                supabase.table('attendance').delete().eq("committee", sel_c).eq("date", today).execute()
                supabase.table('attendance').insert(results).execute()
                st.success("✅ تم حفظ الرصد بنجاح!"); time.sleep(1); st.session_state.page = "home"; st.rerun()

# --- 4. لوحة الإدارة ---
elif st.session_state.page == "a_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    if st.text_input("كلمة مرور الإدارة:", type="password") == "1234": 
        st.session_state.page = "admin"; st.rerun()

elif st.session_state.page == "admin":
    if st.button("⬅️ تسجيل خروج"): st.session_state.page = "home"; st.rerun()
    tab1, tab2, tab3, tab4 = st.tabs(["📊 التقارير", "🏘️ حالة اللجان", "💾 البيانات", "👨‍🏫 إدارة المعلمين"])
    
    # --- التبويب الرابع: إدارة المعلمين (الإضافة الجديدة) ---
    with tab4:
        st.subheader("👨‍🏫 لوحة التحكم في حسابات المعلمين")
        
        # أزرار الإجراءات السريعة
        col_act1, col_act2 = st.columns(2)
        with col_act1:
            if st.button("✅ تفعيل جميع المعلمين", use_container_width=True):
                supabase.table("teachers").update({"status": "نشط"}).neq("id", 0).execute()
                st.success("تم تفعيل جميع الحسابات"); st.rerun()
        with col_act2:
            if st.button("🚫 إيقاف جميع المعلمين", use_container_width=True):
                supabase.table("teachers").update({"status": "موقوف"}).neq("id", 0).execute()
                st.warning("تم إيقاف جميع الحسابات"); st.rerun()

        st.divider()
        
        # إضافة معلم جديد
        with st.expander("➕ إضافة معلم جديد للنظام"):
            with st.form("add_teacher"):
                new_n = st.text_input("اسم المعلم الكامل:")
                new_p = st.text_input("السجل المدني (كلمة المرور):")
                if st.form_submit_button("إضافة الآن"):
                    if new_n and new_p:
                        supabase.table("teachers").insert({"name_tech": new_n, "national_id": new_p, "status": "نشط"}).execute()
                        st.success(f"تمت إضافة أ. {new_n} بنجاح"); st.rerun()
                    else: st.error("يرجى تعبئة جميع الحقول")

        st.divider()
        
        # عرض وتعديل المعلمين الحاليين
        st.write("🔍 **المعلمون المسجلون حالياً:**")
        res_t = supabase.table("teachers").select("*").execute()
        if res_t.data:
            df_t = pd.DataFrame(res_t.data).sort_values('name_tech')
            for index, row in df_t.iterrows():
                with st.container():
                    st.markdown(f'<div class="teacher-card">', unsafe_allow_html=True)
                    c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
                    
                    # تعديل الاسم والسجل
                    u_name = c1.text_input("الاسم", value=row['name_tech'], key=f"nm_{row['id']}")
                    u_pass = c2.text_input("السجل", value=row['national_id'], key=f"ps_{row['id']}")
                    
                    # تعديل الحالة
                    current_status = row.get('status', 'نشط')
                    u_stat = c3.selectbox("الحالة", ["نشط", "موقوف"], 
                                         index=0 if current_status == "نشط" else 1, 
                                         key=f"st_{row['id']}")
                    
                    # زر الحفظ لكل معلم
                    if c4.button("💾 حفظ", key=f"sv_{row['id']}"):
                        supabase.table("teachers").update({
                            "name_tech": u_name,
                            "national_id": u_pass,
                            "status": u_stat
                        }).eq("id", row['id']).execute()
                        st.toast(f"تم تحديث بيانات {u_name}")
                        time.sleep(0.5); st.rerun()
                    
                    st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("لا يوجد معلمون مسجلون حالياً.")

    # (بقية التبويبات تظل كما هي في كودك الأصلي...)
    with tab1:
        st.write("📊 تقارير الغياب...")
        # كود التقارير الخاص بك...
    
    with tab2:
        st.write("🏘️ متابعة اللجان...")
        # كود اللجان الخاص بك...

    with tab3:
        st.write("💾 إدارة بيانات الطلاب...")
        # كود رفع الملفات الخاص بك...
