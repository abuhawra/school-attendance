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
    .wa-absent { background-color: #dc3545; }
    .wa-late { background-color: #fd7e14; }
    .thank-you-box { text-align: center; padding: 40px; background: #f8fdf9; border-radius: 20px; border: 2px solid #22c55e; margin-top: 20px; }
    </style>
''', unsafe_allow_html=True)

if 'page' not in st.session_state: st.session_state.page = "home"

# --- 1. الصفحة الرئيسية ---
if st.session_state.page == "home":
    st.markdown('''
        <div class="main-header">
            <h2 style="color:#ffd700; font-size: 65px; font-weight: 800;">بصمة تميز</h2>
            <h2 style="color:#ffd700; font-size: 22px; font-weight: 500;">أولى خطوات النجاح التحضير اليومي</h2>
            <h2 style="margin:10px 0; font-size: 40px;">مدرسة القطيف الثانوية</h2>
            <h2 style="color:#ffd700; font-size: 24px; font-weight: 500;">مدير المدرسة: أ. فراس آل عبدالمحسن</h2>
            <h2 style="color:#ffffff; font-size: 24px; font-weight: 500;">فكرة و برمجة: أ. عارف أحمد الحداد</h2>
        </div>
    ''', unsafe_allow_html=True)
    
    col_b = st.columns([1, 2, 1])[1]
    with col_b:
        if st.button("📝 رصد غياب الطلاب اليومي", use_container_width=True, type="primary"):
            st.session_state.page = "t_log"; st.rerun()
        st.write("")
        if st.button("⚙️ لوحة الإدارة والتقارير الموحدة", use_container_width=True):
            st.session_state.page = "a_log"; st.rerun()

# --- 2. تسجيل دخول المعلم ---
elif st.session_state.page == "t_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    tid = st.text_input("أدخل السجل المدني للمعلم:", type="password")
    if st.button("دخول للنظام"):
        res = supabase.table("teachers").select("*").eq("national_id", tid.strip()).execute()
        if res.data:
            t_info = res.data[0]
            if t_info.get('status') == 'موقوف':
                st.error("عذراً، هذا الحساب موقوف حالياً.")
            else:
                st.session_state.teacher = t_info['name_tech']
                st.session_state.page = "mark"; st.rerun()
        else: st.error("السجل المدني غير مسجل.")

# --- 3. واجهة الرصد ---
elif st.session_state.page == "mark":
    today = str(datetime.now().date())
    st.info(f"المعلم: {st.session_state.teacher} | التاريخ: {today}")
    res_s = supabase.table('students').select("committee").execute()
    if res_s.data:
        coms = sorted(list(set([str(i['committee']) for i in res_s.data if i['committee']])), key=lambda x: int(x) if x.isdigit() else 0)
        sel_c = st.selectbox("اختر اللجنة:", ["---"] + coms)
        if sel_c != "---":
            students = supabase.table('students').select("*").eq("committee", sel_c).execute()
            old_att = supabase.table('attendance').select("*").eq("committee", sel_c).eq("date", today).execute()
            old_map = {i['student_name']: i['status'] for i in old_att.data}
            
            results = []
            for s in students.data:
                prev = old_map.get(s['student_name'], "حاضر")
                choice = st.radio(f"👤 {s['student_name']}", ["حاضر", "غائب", "متأخر"], index=["حاضر", "غائب", "متأخر"].index(prev), key=f"std_{s['id']}", horizontal=True)
                results.append({"student_name": s['student_name'], "committee": str(sel_c), "status": choice, "date": today, "teacher_name": st.session_state.teacher})
            
            if st.button("💾 حفظ الرصد النهائي", use_container_width=True):
                supabase.table('attendance').delete().eq("committee", sel_c).eq("date", today).execute()
                supabase.table('attendance').insert(results).execute()
                st.session_state.page = "thank_you"; st.rerun()

# --- 4. صفحة الشكر ---
elif st.session_state.page == "thank_you":
    st.snow()
    st.markdown(f'<div class="thank-you-box"><h1>✅ تم الرصد بنجاح</h1><h2>شكراً لك أ. {st.session_state.teacher}</h2></div>', unsafe_allow_html=True)
    if st.button("🏠 العودة للرئيسية", use_container_width=True):
        st.session_state.page = "home"; st.rerun()

# --- 5. لوحة الإدارة ---
elif st.session_state.page == "a_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    if st.text_input("كلمة مرور الإدارة:", type="password") == "1234": 
        st.session_state.page = "admin"; st.rerun()

elif st.session_state.page == "admin":
    if st.button("⬅️ تسجيل خروج"): st.session_state.page = "home"; st.rerun()
    tab1, tab2, tab3, tab4 = st.tabs(["📊 التقارير", "🏘️ حالة اللجان", "💾 البيانات", "👨‍🏫 المعلمين"])
    
    with tab1: # التقارير والواتساب
        d = st.date_input("اختر التاريخ:", datetime.now())
        res_att = supabase.table("attendance").select("*").eq("date", str(d)).execute()
        if res_att.data:
            df = pd.DataFrame(res_att.data)
            df_rep = df[df['status'].isin(['غائب', 'متأخر'])].copy()
            if not df_rep.empty:
                st.table(df_rep[['committee', 'student_name', 'status', 'teacher_name']])
                msg = f"📝 *تقرير مدرسة القطيف*%0A📅 *التاريخ:* {d}%0A"
                for _, r in df_rep.iterrows(): msg += f"-----------------%0A📦 اللجنة: {r['committee']}%0A👤 الطالب: {r['student_name']}%0A⚠️ الحالة: {r['status']}%0A"
                st.markdown(f'<a href="https://wa.me/?text={msg}" target="_blank" class="wa-button wa-all">📲 إرسال التقرير عبر واتساب</a>', unsafe_allow_html=True)
            else: st.success("لا يوجد غياب اليوم.")
        else: st.info("لا توجد بيانات لهذا اليوم.")

    with tab2: # حالة اللجان
        st.subheader("🏘️ حالة رصد اللجان")
        res_s = supabase.table('students').select("committee").execute()
        all_c = sorted(list(set([str(i['committee']) for i in res_s.data])), key=lambda x: int(x) if x.isdigit() else 0)
        done = [str(i['committee']) for i in supabase.table('attendance').select("committee").eq("date", str(datetime.now().date())).execute().data]
        c1, c2 = st.columns(2)
        with c1:
            st.success("✅ رُصدت")
            for c in all_c:
                if c in done: st.write(f"📍 لجنة {c}")
        with c2:
            st.error("❌ لم تُرصد")
            for c in all_c:
                if c not in done: st.write(f"⚠️ لجنة {c}")

    with tab3: # النسخ الاحتياطي وتحديث البيانات
        if st.text_input("رمز البيانات:", type="password") == "4321":
            st.subheader("💾 النسخة الاحتياطية")
            res_b = supabase.table('students').select("*").execute()
            if res_b.data:
                df_b = pd.DataFrame(res_b.data)
                csv = df_b.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 تحميل ملف الطلاب (CSV)", csv, "students.csv", "text/csv", use_container_width=True)
            
            st.divider()
            up = st.file_uploader("تحديث قاعدة بيانات الطلاب (CSV/Excel):")
            if up and st.button("🚀 رفع وتحديث"):
                df_new = pd.read_csv(up) if up.name.endswith('.csv') else pd.read_excel(up)
                supabase.table('students').delete().neq('committee', '0').execute()
                supabase.table('students').insert(df_new.to_dict('records')).execute()
                st.success("تم التحديث بنجاح!")

    with tab4: # إدارة المعلمين وتحديث الرقم السري
        st.subheader("👨‍🏫 إدارة بيانات المعلمين")
        with st.expander("➕ إضافة معلم"):
            with st.form("add_t"):
                n = st.text_input("الاسم:")
                i = st.text_input("السجل:")
                if st.form_submit_button("إضافة"):
                    supabase.table("teachers").insert({"name_tech": n, "national_id": i, "status": "نشط"}).execute()
                    st.rerun()

        st.divider()
        res_t = supabase.table("teachers").select("*").execute()
        if res_t.data:
            df_t = pd.DataFrame(res_t.data).sort_values('name_tech')
            for index, row in df_t.iterrows():
                with st.container():
                    c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
                    with c1: st.write(f"👤 **{row['name_tech']}**")
                    with c2: new_val = st.text_input("السجل:", value=row['national_id'], key=f"p_{row['id']}")
                    with c3: new_stat = st.selectbox("الحالة:", ["نشط", "موقوف"], index=0 if row.get('status')=='نشط' else 1, key=f"s_{row['id']}")
                    with c4:
                        if st.button("💾 تحديث", key=f"b_{row['id']}"):
                            try:
                                supabase.table("teachers").update({"national_id": new_val, "status": new_stat}).eq("id", row['id']).execute()
                                st.success("تم")
                                time.sleep(0.5); st.rerun()
                            except: st.error("خطأ")
                st.markdown("---")
