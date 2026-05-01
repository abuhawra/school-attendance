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

# 2. إعدادات الواجهة والتنسيق
st.set_page_config(page_title="نظام مدرسة القطيف التقني", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .main-header { background-color: #1a237e; color: white; padding: 30px; border-radius: 15px; text-align: center; border-bottom: 5px solid #ffd700; margin-bottom: 20px; }
    .wa-button { color: white !important; padding: 15px; border-radius: 10px; text-align: center; display: block; text-decoration: none; font-weight: bold; margin-top: 10px; font-size: 18px; transition: 0.3s; }
    .wa-all { background-color: #28a745; } .wa-all:hover { background-color: #218838; }
    .wa-absent { background-color: #dc3545; } .wa-absent:hover { background-color: #c82333; }
    th { background-color: #1a237e !important; color: white !important; text-align: center !important; }
    td { text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

if 'page' not in st.session_state: st.session_state.page = "home"

# --- الصفحة الرئيسية ---
if st.session_state.page == "home":
    st.markdown("""
        <div class="main-header">
            <div style="font-size:32px; font-weight:800;">التحضير التقني لـ مدرسة القطيف الثانوية</div>
            <div style="font-size:20px; color:#ffd700; margin-top:10px;">فكرة وبرمجة: أ. عارف أحمد الحداد</div>
            <div style="font-size:18px; color:#cfd8dc;">بإشراف مدير المدرسة: أ. فراس عبدالله آل عبد المحسن</div>
        </div>
    """, unsafe_allow_html=True)
    
    col_a, col_b, col_c = st.columns([1, 1.5, 1])
    with col_b:
        if st.button("📝 رصد غياب الطلاب", type="primary", use_container_width=True): 
            st.session_state.page = "t_log"; st.rerun()
        st.write("")
        if st.button("⚙️ لوحة الإدارة والتقارير", use_container_width=True): 
            st.session_state.page = "a_log"; st.rerun()

# --- قسم التحقق (المعلم) ---
elif st.session_state.page == "t_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    tid = st.text_input("أدخل رقم السجل المدني الخاص بك:", type="password")
    if st.button("دخول للنظام"):
        res = supabase.table("teachers").select("*").eq("national_id", tid.strip()).execute()
        if res.data:
            st.session_state.teacher = res.data[0]['name_tech']
            st.session_state.page = "mark"; st.rerun()
        else: st.error("عذراً، السجل المدني غير مسجل في قاعدة البيانات.")

# --- قسم رصد الحضور ---
elif st.session_state.page == "mark":
    today = str(datetime.now().date())
    st.info(f"المعلم المسجل: {st.session_state.teacher} | التاريخ: {today}")
    
    res_s = supabase.table('students').select("committee").execute()
    if res_s.data:
        coms = sorted(list(set([str(i['committee']) for i in res_s.data if i['committee']])), key=lambda x: int(x) if x.isdigit() else 0)
        sel_c = st.selectbox("اختر رقم اللجنة:", ["---"] + coms)
        
        if sel_c != "---":
            students = supabase.table('students').select("*").eq("committee", sel_c).execute()
            old_att = supabase.table('attendance').select("*").eq("committee", sel_c).eq("date", today).execute()
            old_map = {i['student_name']: i['status'] for i in old_att.data}
            
            results = []
            for s in students.data:
                prev_status = old_map.get(s['student_name'], "حاضر")
                choice = st.radio(f"👤 {s['student_name']}", ["حاضر", "غائب", "متأخر"], 
                                  index=["حاضر", "غائب", "متأخر"].index(prev_status), key=s['student_name'], horizontal=True)
                results.append({"student_name": s['student_name'], "committee": str(sel_c), "status": choice, "date": today, "teacher_name": st.session_state.teacher})
            
            if st.button("💾 حفظ بيانات اللجنة", use_container_width=True):
                supabase.table('attendance').delete().eq("committee", sel_c).eq("date", today).execute()
                supabase.table('attendance').insert(results).execute()
                st.success("تم حفظ البيانات بنجاح!"); time.sleep(1); st.session_state.page = "home"; st.rerun()

# --- قسم الإدارة والتقارير ---
elif st.session_state.page == "a_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    if st.text_input("كلمة مرور الإدارة:", type="password") == "1234": 
        st.session_state.page = "admin"; st.rerun()

elif st.session_state.page == "admin":
    if st.button("⬅️ تسجيل الخروج"): st.session_state.page = "home"; st.rerun()
    
    tab1, tab2, tab3 = st.tabs(["📊 التقارير الموحدة", "🏘️ حالة اللجان", "💾 إدارة البيانات"])
    
    with tab1:
        d = st.date_input("اختر تاريخ التقرير المُراد عرضه:", datetime.now())
        res_att = supabase.table("attendance").select("*").eq("date", str(d)).execute()
        
        if res_att.data:
            df_full = pd.DataFrame(res_att.data)
            # التعديل المطلوب: إظهار الغائب والمتأخر فقط في التقرير
            df_report = df_full[df_full['status'].isin(['غائب', 'متأخر'])].copy()
            
            if not df_report.empty:
                # ربط الشعبة بشكل آلي لتفادي KeyError
                res_std = supabase.table("students").select("*").execute()
                df_std_map = pd.DataFrame(res_std.data)
                
                # البحث عن اسم عمود الشعبة واسم الطالب آلياً
                name_col = 'student_name' if 'student_name' in df_std_map.columns else df_std_map.columns[1]
                class_col = 'class_name' if 'class_name' in df_std_map.columns else ('الشعبة' if 'الشعبة' in df_std_map.columns else df_std_map.columns[2])
                
                s_map = dict(zip(df_std_map[name_col], df_std_map[class_col]))
                df_report['الشعبة'] = df_report['student_name'].map(s_map).fillna("---")
                
                st.table(df_report[['committee', 'student_name', 'الشعبة', 'status', 'teacher_name']].rename(columns={'committee':'اللجنة','student_name':'اسم الطالب'}))
                
                # --- أزرار الواتساب المعدلة ---
                # 1. زر إرسال (الكل الموجود في التقرير: غائب + متأخر)
                wa_all_msg = f"🗓️ *تقرير الغياب والتأخر - مدرسة القطيف*%0A📅 *التاريخ:* {d}%0A-----------------------%0A"
                for _, r in df_report.iterrows():
                    wa_all_msg += f"📦 *اللجنة:* {r['committee']}%0A👤 *الاسم:* {r['student_name']}%0A🏫 *الشعبة:* {r['الشعبة']}%0A⚠️ *الحالة:* {r['status']}%0A-----------------------%0A"
                
                st.markdown(f'<a href="https://wa.me/?text={wa_all_msg}" target="_blank" class="wa-button wa-all">📲 إرسال تقرير (الغائبين والمتأخرين) عبر واتساب</a>', unsafe_allow_html=True)

                # 2. زر إرسال (الغائبين فقط)
                df_only_absent = df_report[df_report['status'] == 'غائب']
                if not df_only_absent.empty:
                    wa_abs_msg = f"🗓️ *تقرير الغائبين فقط - مدرسة القطيف*%0A📅 *التاريخ:* {d}%0A-----------------------%0A"
                    for _, r in df_only_absent.iterrows():
                        wa_abs_msg += f"📦 *اللجنة:* {r['committee']}%0A👤 *الاسم:* {r['student_name']}%0A🏫 *الشعبة:* {r['الشعبة']}%0A🔴 *الحالة:* غائب%0A-----------------------%0A"
                    st.markdown(f'<a href="https://wa.me/?text={wa_abs_msg}" target="_blank" class="wa-button wa-absent">🚫 إرسال تقرير (الغائبين فقط) عبر واتساب</a>', unsafe_allow_html=True)
            else:
                st.success("الحمد لله، لا يوجد غياب أو تأخر في هذا التاريخ.")
        else: st.info("لا توجد سجلات حضور لهذا اليوم.")

    with tab2:
        st.subheader("🏘️ متابعة رصد لجان اليوم")
        res_all_s = supabase.table('students').select("committee").execute()
        if res_all_s.data:
            all_coms = sorted(list(set([str(i['committee']) for i in res_all_s.data])), key=lambda x: int(x) if x.isdigit() else 0)
            done_res = supabase.table('attendance').select("committee", "teacher_name").eq("date", str(datetime.now().date())).execute()
            done_map = {str(i['committee']): i['teacher_name'] for i in done_res.data}
            
            c1, c2 = st.columns(2)
            with c1:
                st.success("✅ لجان تم رصدها")
                for c in all_coms:
                    if c in done_map: st.write(f"📍 لجنة {c} (بواسطة: {done_map[c]})")
            with c2:
                st.error("❌ لجان لم تُرصد")
                for c in all_coms:
                    if c not in done_map: st.write(f"⚠️ لجنة {c}")

    with tab3:
        if st.text_input("رمز إدارة البيانات:", type="password") == "4321":
            up = st.file_uploader("تحديث قاعدة بيانات الطلاب (CSV/Excel):")
            if up and st.button("🚀 بدء التحديث"):
                df_new = pd.read_csv(up) if up.name.endswith('.csv') else pd.read_excel(up)
                supabase.table('students').delete().neq('committee', '0').execute()
                supabase.table('students').insert(df_new.to_dict('records')).execute()
                st.success("تم تحديث البيانات بنجاح!")
