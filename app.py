import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
import io

# 1. إعدادات الاتصال
url = "https://lsmevvsogsqqqjyuqzbx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzbWV2dnNvZ3NxcXFqeXVxemJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MDMyOTgsImV4cCI6MjA5Mjk3OTI5OH0.ecqJS75fPbKqwSAiBzP6Qonn4cuymgwjB96tIGek8j0"

if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(url, key)
supabase = st.session_state.supabase

# 2. الواجهة الكلاسيكية
st.set_page_config(page_title="نظام مدرسة القطيف التقني", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; }
    .main-header { background-color: #1a237e; color: white; padding: 40px; border-radius: 15px; text-align: center; border-bottom: 6px solid #ffd700; }
    .hr-style { border: 0; height: 1px; background: rgba(255,255,255,0.3); width: 40%; margin: 20px auto; }
    .wa-all { background-color: #25D366; color: white !important; padding: 12px; border-radius: 10px; text-align: center; display: block; text-decoration: none; font-weight: bold; margin-bottom: 10px; }
    .wa-absent { background-color: #d32f2f; color: white !important; padding: 12px; border-radius: 10px; text-align: center; display: block; text-decoration: none; font-weight: bold; }
    th { background-color: #1a237e !important; color: white !important; text-align: center !important; }
    td { text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

if 'page' not in st.session_state: st.session_state.page = "home"

# --- الصفحة الرئيسية ---
if st.session_state.page == "home":
    st.markdown("""
        <div class="main-header">
            <div style="font-size:36px; font-weight:800;">التحضير التقني</div>
            <div style="font-size:26px; font-weight:700;">مدرسة القطيف الثانوية</div>
            <div class="hr-style"></div>
            <div style="font-size:18px; color:#ffd700;">فكرة وبرمجة</div>
            <div style="font-size:24px; font-weight:bold;">أ. عارف أحمد الحداد</div>
            <div style="font-size:18px; color:#cfd8dc; margin-top:15px;">إشراف مدير المدرسة</div>
            <div style="font-size:22px; font-weight:bold;">أ. فراس عبدالله آل عبد المحسن</div>
        </div>
    """, unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns([1, 1.2, 1])
    with col_b:
        st.write(" ")
        if st.button("📝 رصد غياب الطلاب", type="primary"): st.session_state.page = "t_log"; st.rerun()
        st.write(" ")
        if st.button("⚙️ لوحة الإدارة والتقارير"): st.session_state.page = "a_log"; st.rerun()

# --- قسم الإدارة والتقارير ---
elif st.session_state.page == "a_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    if st.text_input("رمز الإدارة:", type="password") == "1234": st.session_state.page = "admin"; st.rerun()

elif st.session_state.page == "admin":
    if st.button("⬅️ تسجيل خروج"): st.session_state.page = "home"; st.rerun()
    tab1, tab2, tab3 = st.tabs(["📊 التقارير الموحدة", "🏘️ متابعة حالة اللجان", "💾 إدارة البيانات"])
    
    with tab1:
        d = st.date_input("اختر التاريخ:", datetime.now())
        res_att = supabase.table("attendance").select("*").eq("date", str(d)).execute()
        
        if res_att.data:
            df_report = pd.DataFrame(res_att.data)
            
            # جلب بيانات الطلاب لربط الشعبة آلياً
            res_std = supabase.table("students").select("*").execute()
            if res_std.data:
                df_std = pd.DataFrame(res_std.data)
                # كشف الأعمدة آلياً لتجنب KeyError
                c_name = 'student_name' if 'student_name' in df_std.columns else df_std.columns[1]
                c_class = 'class_name' if 'class_name' in df_std.columns else ('الشعبة' if 'الشعبة' in df_std.columns else df_std.columns[2])
                s_map = dict(zip(df_std[c_name], df_std[c_class]))
                df_report['الشعبة'] = df_report['student_name'].map(s_map).fillna("---")
            
            # ترتيب وعرض الجدول
            st.table(df_report[['committee', 'student_name', 'الشعبة', 'status', 'teacher_name']].rename(columns={'committee':'اللجنة','student_name':'الطالب'}))
            
            # --- أزرار الواتساب ---
            # 1. زر الكل
            wa_all = f"🗓️ *تقرير مدرسة القطيف التقني - {d}*%0A-----------------------%0A"
            for _, r in df_report.iterrows():
                wa_all += f"📦 *اللجنة:* {r['committee']}%0A👤 *الاسم:* {r['student_name']}%0A🏫 *الشعبة:* {r['الشعبة']}%0A⚠️ *الحالة:* {r['status']}%0A-----------------------%0A"
            st.markdown(f'<a href="https://wa.me/?text={wa_all}" target="_blank" class="wa-all">📲 إرسال تقرير (الكل) عبر واتساب</a>', unsafe_allow_html=True)

            # 2. زر الغائبين فقط
            df_abs = df_report[df_report['status'] == 'غائب']
            if not df_abs.empty:
                wa_abs = f"🗓️ *تقرير الغائبين فقط - {d}*%0A-----------------------%0A"
                for _, r in df_abs.iterrows():
                    wa_abs += f"📦 *اللجنة:* {r['committee']}%0A👤 *الاسم:* {r['student_name']}%0A🏫 *الشعبة:* {r['الشعبة']}%0A🔴 *الحالة:* غائب%0A-----------------------%0A"
                st.markdown(f'<a href="https://wa.me/?text={wa_abs}" target="_blank" class="wa-absent">🚫 إرسال تقرير (الغائبين فقط) عبر واتساب</a>', unsafe_allow_html=True)
        else: st.info("لا توجد بيانات لهذا التاريخ")

    with tab2:
        st.subheader("🏘️ حالة رصد اللجان")
        res_s = supabase.table('students').select("committee").execute()
        if res_s.data:
            all_coms = sorted(list(set([str(i['committee']) for i in res_s.data])), key=lambda x: int(x) if x.isdigit() else 0)
            done_res = supabase.table('attendance').select("committee", "teacher_name").eq("date", str(datetime.now().date())).execute()
            done_map = {str(i['committee']): i['teacher_name'] for i in done_res.data}
            
            c1, c2 = st.columns(2)
            with c1:
                st.success("✅ رُصدت")
                for c in all_coms:
                    if c in done_map: st.write(f"📍 لجنة {c} ({done_map[c]})")
            with c2:
                st.error("❌ متبقية")
                for c in all_coms:
                    if c not in done_map: st.write(f"⚠️ لجنة {c}")

    with tab3:
        if st.text_input("كلمة مرور البيانات:", type="password") == "4321":
            up = st.file_uploader("رفع بيانات الطلاب (Excel/CSV):")
            if up and st.button("🚀 تحديث قاعدة البيانات"):
                df_new = pd.read_csv(up) if up.name.endswith('.csv') else pd.read_excel(up)
                supabase.table('students').delete().neq('committee', '0').execute()
                supabase.table('students').insert(df_new.to_dict('records')).execute()
                st.success("تم التحديث بنجاح")

# --- قسم المعلمين ---
elif st.session_state.page == "t_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    tid = st.text_input("أدخل السجل المدني:", type="password")
    if st.button("دخول"):
        res = supabase.table("teachers").select("*").eq("national_id", tid.strip()).execute()
        if res.data:
            st.session_state.teacher = res.data[0]['name_tech']
            st.session_state.page = "mark"; st.rerun()
        else: st.error("السجل غير مسجل")

elif st.session_state.page == "mark":
    today = str(datetime.now().date())
    st.info(f"المعلم: {st.session_state.teacher} | التاريخ: {today}")
    res_coms = supabase.table('students').select("committee").execute()
    if res_coms.data:
        coms = sorted(list(set([str(i['committee']) for i in res_coms.data])), key=lambda x: int(x) if x.isdigit() else 0)
        sel_c = st.selectbox("اختر اللجنة:", ["---"] + coms)
        if sel_c != "---":
            st_list = supabase.table('students').select("*").eq("committee", sel_c).execute()
            old_att = supabase.table('attendance').select("*").eq("committee", sel_c).eq("date", today).execute()
            old_map = {i['student_name']: i['status'] for i in old_att.data}
            
            results = []
            for s in st_list.data:
                prev = old_map.get(s['student_name'], "حاضر")
                choice = st.radio(f"👤 {s['student_name']}", ["حاضر", "غائب", "متأخر"], index=["حاضر", "غائب", "متأخر"].index(prev), key=s['student_name'], horizontal=True)
                results.append({"student_name": s['student_name'], "committee": str(sel_c), "status": choice, "date": today, "teacher_name": st.session_state.teacher})
            
            if st.button("💾 حفظ"):
                supabase.table('attendance').delete().eq("committee", sel_c).eq("date", today).execute()
                supabase.table('attendance').insert(results).execute()
                st.success("تم الحفظ"); time.sleep(1); st.session_state.page = "home"; st.rerun()
