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
    .wa-button { color: white !important; padding: 12px; border-radius: 10px; text-align: center; display: block; text-decoration: none; font-weight: bold; margin-top: 10px; }
    .wa-all { background-color: #28a745; }
    .status-active { color: #28a745; font-weight: bold; }
    .status-stop { color: #dc3545; font-weight: bold; }
    </style>
''', unsafe_allow_html=True)

if 'page' not in st.session_state: st.session_state.page = "home"

# --- 1. الصفحة الرئيسية ---
if st.session_state.page == "home":
    st.markdown('''
        <div class="main-header">
            <h2 style="color:#ffd700; font-size: 60px; font-weight: 800;">بصمة تميز</h2>
            <h2 style="margin:10px 0; font-size: 40px;">مدرسة القطيف الثانوية</h2>
            <h2 style="color:#ffffff; font-size: 24px;">فكرة و برمجة: أ. عارف أحمد الحداد</h2>
        </div>
    ''', unsafe_allow_html=True)
    
    col_b = st.columns([1, 2, 1])[1]
    with col_b:
        if st.button("📝 رصد غياب الطلاب اليومي", use_container_width=True, type="primary"):
            st.session_state.page = "t_log"; st.rerun()
        st.write("")
        if st.button("⚙️ لوحة الإدارة والتقارير الموحدة", use_container_width=True):
            st.session_state.page = "a_log"; st.rerun()

# --- 2. دخول المعلم ---
elif st.session_state.page == "t_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    tid = st.text_input("أدخل السجل المدني (كلمة المرور):", type="password")
    if st.button("دخول للنظام"):
        res = supabase.table("teachers").select("*").eq("national_id", tid.strip()).execute()
        if res.data:
            if res.data[0].get('status') == 'موقوف':
                st.error("عذراً، هذا الحساب موقوف حالياً.")
            else:
                st.session_state.teacher = res.data[0]['name_tech']
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
                choice = st.radio(f"👤 {s['student_name']}", ["حاضر", "غائب", "متأخر"], 
                                 index=["حاضر", "غائب", "متأخر"].index(prev), key=f"std_{s['id']}", horizontal=True)
                results.append({"student_name": s['student_name'], "committee": str(sel_c), "status": choice, "date": today, "teacher_name": st.session_state.teacher})
            
            if st.button("💾 حفظ الرصد النهائي", use_container_width=True):
                supabase.table('attendance').delete().eq("committee", sel_c).eq("date", today).execute()
                supabase.table('attendance').insert(results).execute()
                st.success("تم الحفظ بنجاح!"); time.sleep(1); st.session_state.page = "home"; st.rerun()

# --- 4. لوحة الإدارة ---
elif st.session_state.page == "a_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    if st.text_input("كلمة مرور الإدارة:", type="password") == "1234": 
        st.session_state.page = "admin"; st.rerun()

elif st.session_state.page == "admin":
    if st.button("⬅️ تسجيل خروج"): st.session_state.page = "home"; st.rerun()
    tab1, tab2, tab3, tab4 = st.tabs(["📊 التقارير", "🏘️ حالة اللجان", "💾 البيانات", "👨‍🏫 إدارة المعلمين"])
    
    with tab4: # تبويب إدارة المعلمين الجديد
        st.subheader("👨‍🏫 التحكم في حسابات المعلمين")
        
        # أزرار التغيير الجماعي
        st.write("🔧 إجراءات سريعة لجميع المعلمين:")
        c_all1, c_all2 = st.columns(2)
        with c_all1:
            if st.button("✅ تنشيط جميع الحسابات", use_container_width=True):
                supabase.table("teachers").update({"status": "نشط"}).neq("id", 0).execute()
                st.success("تم تنشيط جميع المعلمين"); time.sleep(1); st.rerun()
        with c_all2:
            if st.button("🚫 إيقاف جميع الحسابات", use_container_width=True):
                supabase.table("teachers").update({"status": "موقوف"}).neq("id", 0).execute()
                st.warning("تم إيقاف جميع المعلمين"); time.sleep(1); st.rerun()

        st.divider()

        # قائمة المعلمين مع تحديث السجل والحالة
        res_t = supabase.table("teachers").select("*").execute()
        if res_t.data:
            df_t = pd.DataFrame(res_t.data).sort_values('name_tech')
            for index, row in df_t.iterrows():
                t_id = row['id']
                with st.expander(f"👤 {row['name_tech']} - الحالة الحالية: ({row.get('status', 'نشط')})"):
                    # تعديل البيانات الفردية
                    new_name = st.text_input("اسم المعلم:", value=row['name_tech'], key=f"nm_{t_id}")
                    new_pwd = st.text_input("السجل المدني (الرقم السري):", value=row['national_id'], key=f"pwd_{t_id}")
                    
                    # اختيار الحالة (راديو)
                    status_list = ["نشط", "موقوف"]
                    curr_idx = status_list.index(row.get('status', 'نشط')) if row.get('status') in status_list else 0
                    new_stat = st.radio("تغيير الحالة:", status_list, index=curr_idx, key=f"rad_{t_id}", horizontal=True)
                    
                    if st.button(f"💾 تحديث بيانات {row['name_tech']}", key=f"btn_{t_id}"):
                        try:
                            supabase.table("teachers").update({
                                "name_tech": new_name,
                                "national_id": str(new_pwd).strip(),
                                "status": new_stat
                            }).eq("id", t_id).execute()
                            st.success(f"تم تحديث بيانات المعلم بنجاح")
                            time.sleep(0.5); st.rerun()
                        except Exception as e:
                            st.error(f"حدث خطأ أثناء التحديث: {e}")

        # إضافة معلم جديد
        st.divider()
        with st.expander("➕ إضافة معلم جديد للنظام"):
            with st.form("add_new"):
                an = st.text_input("اسم المعلم:")
                ai = st.text_input("السجل المدني:")
                if st.form_submit_button("إضافة"):
                    if an and ai:
                        supabase.table("teachers").insert({"name_tech": an, "national_id": ai, "status": "نشط"}).execute()
                        st.success("تمت الإضافة"); st.rerun()

    # بقية التبويبات (التقارير وحالة اللجان والبيانات) كما هي في النسخة المستقرة السابقة
    with tab1:
        d = st.date_input("تاريخ التقرير:", datetime.now())
        res_att = supabase.table("attendance").select("*").eq("date", str(d)).execute()
        if res_att.data:
            df_rep = pd.DataFrame(res_att.data)
            df_rep = df_rep[df_rep['status'].isin(['غائب', 'متأخر'])]
            st.table(df_rep[['committee', 'student_name', 'status', 'teacher_name']])
            msg = f"📝 *تقرير الغياب*%0A📅 *التاريخ:* {d}%0A"
            for _, r in df_rep.iterrows(): msg += f"-----------------%0A📦 اللجنة: {r['committee']}%0A👤 الطالب: {r['student_name']}%0A⚠️ الحالة: {r['status']}%0A"
            st.markdown(f'<a href="https://wa.me/?text={msg}" target="_blank" class="wa-button wa-all">📲 إرسال عبر واتساب</a>', unsafe_allow_html=True)

    with tab3: # تبويب البيانات والنسخ الاحتياطي
        if st.text_input("رمز البيانات:", type="password") == "4321":
            st.subheader("💾 النسخة الاحتياطية")
            res_b = supabase.table('students').select("*").execute()
            if res_b.data:
                df_b = pd.DataFrame(res_b.data)
                csv = df_b.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 تحميل ملف الطلاب (CSV)", csv, "backup.csv", "text/csv")
            
            st.divider()
            up = st.file_uploader("تحديث الطلاب (CSV):")
            if up and st.button("🚀 رفع"):
                df_new = pd.read_csv(up)
                supabase.table('students').delete().neq('committee', '0').execute()
                supabase.table('students').insert(df_new.to_dict('records')).execute()
                st.success("تم!")
