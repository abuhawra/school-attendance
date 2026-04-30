import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
import urllib.parse

# 1. إعدادات الاتصال بقاعدة البيانات
url = "https://lsmevvsogsqqqjyuqzbx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzbWV2dnNvZ3NxcXFqeXVxemJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MDMyOTgsImV4cCI6MjA5Mjk3OTI5OH0.ecqJS75fPbKqwSAiBzP6Qonn4cuymgwjB96tIGek8j0"

if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(url, key)
supabase = st.session_state.supabase

# 2. إخفاء عناصر Streamlit وإضافة تنسيق الأزرار المخصص
st.set_page_config(page_title="نظام غياب مدرسة القطيف الثانوية", layout="wide")
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            .stAppDeployButton {display:none;}
            
            /* تنسيق زر تحضير الطلاب - أزرق فاتح */
            div.stButton > button:first-child[data-testid="baseButton-primary"] {
                background-color: #add8e6;
                color: #000000;
                border: none;
            }
            
            /* تنسيق زر إدارة التطبيق - برتقالي */
            div.stButton > button:first-child[data-testid="baseButton-secondary"] {
                background-color: #ffa500;
                color: #ffffff;
                border: none;
            }
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# 3. الدوال الأساسية
def smart_sort(x):
    try: return int(x)
    except: return str(x)

def get_system_status():
    try:
        res = supabase.table("settings").select("is_open").eq("setting_name", "attendance_status").execute()
        return res.data[0]['is_open'] if res.data else True
    except: return True

# تهيئة متغيرات الجلسة
if 'page' not in st.session_state: st.session_state.page = "home"
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'confirm_delete' not in st.session_state: st.session_state.confirm_delete = False

# --- 4. صفحة البداية (Home Page) ---
if st.session_state.page == "home":
    st.write("<br><br>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style="text-align: center; border: 2px solid #1f77b4; padding: 40px; border-radius: 20px; background-color: #f8f9fa; box-shadow: 2px 2px 15px rgba(0,0,0,0.1);">
            <h1 style="color: #1f77b4; margin-bottom: 10px;">برنامج تحضير الغياب</h1>
            <h2 style="color: #333; margin-bottom: 30px;">مدرسة القطيف الثانوية</h2>
            <div style="margin-bottom: 25px;">
                <h4 style="color: #555; margin-bottom: 5px;">فكرة وبرمجة</h4>
                <h3 style="color: #2c3e50; margin-top: 0;">أ. عارف أحمد الحداد</h3>
            </div>
            <div style="margin-bottom: 35px;">
                <h4 style="color: #555; margin-bottom: 5px;">مدير المدرسة</h4>
                <h3 style="color: #2c3e50; margin-top: 0;">أ. فراس آل عبدالمحسن</h3>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.write("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        # زر تحضير الطلاب باللون الأزرق الفاتح (Primary)
        if st.button("📝 تحضير الطلاب", use_container_width=True, type="primary"):
            st.session_state.page = "attendance"; st.rerun()
    with col2:
        # زر إدارة التطبيق باللون البرتقالي (Secondary)
        if st.button("⚙️ إدارة التطبيق", use_container_width=True, type="secondary"):
            st.session_state.page = "admin"; st.rerun()

# --- 5. صفحة تحضير الطلاب ---
elif st.session_state.page == "attendance":
    if st.button("⬅️ العودة للرئيسية"): st.session_state.page = "home"; st.rerun()
    if not get_system_status():
        st.error("🚫 النظام مغلق حالياً من قبل الإدارة.")
    else:
        if not st.session_state.logged_in:
            st.header("🔑 دخول المعلم")
            nid = st.text_input("أدخل رقم السجل المدني:", key="nid_input")
            if st.button("دخول"):
                res = supabase.table("teachers").select("*").eq("national_id", nid.strip()).execute()
                if res.data:
                    st.session_state.logged_in = True
                    st.session_state.teacher_name = res.data[0].get('name_tech', 'المعلم')
                    st.rerun()
                else: st.error("❌ السجل غير صحيح.")
        else:
            st.success(f"✅ مرحباً أستاذ: {st.session_state.teacher_name}")
            t_date = st.date_input("📅 تاريخ الرصد", datetime.now())
            s_data = supabase.table('students').select("committee").execute()
            all_c = sorted(list(set([str(i['committee']) for i in s_data.data if i['committee']])), key=smart_sort)
            sel_c = st.selectbox("🎯 اختر اللجنة:", ["---"] + all_c)
            if sel_c != "---":
                students = supabase.table('students').select("*").eq('committee', sel_c).execute()
                old = supabase.table('attendance').select("*").eq('committee', sel_c).eq('date', str(t_date)).execute()
                history = {r['student_name']: r['status'] for r in old.data}
                results = []
                for s in students.data:
                    prev = history.get(s['student_name'], "حاضر")
                    c1, c2 = st.columns([2, 1])
                    c1.write(s['student_name'])
                    stat = c2.radio("الحالة", ["حاضر", "غائب", "متأخر"], index=["حاضر", "غائب", "متأخر"].index(prev), key=s['id'], horizontal=True)
                    results.append({"student_name": s['student_name'], "committee": sel_c, "status": stat, "date": str(t_date), "teacher_name": st.session_state.teacher_name})
                if st.button("💾 حفظ الكشف وخروج"):
                    supabase.table('attendance').delete().eq('committee', sel_c).eq('date', str(t_date)).execute()
                    supabase.table('attendance').insert(results).execute()
                    st.success("✅ تم الحفظ بنجاح!"); time.sleep(1)
                    st.session_state.logged_in = False; st.session_state.page = "home"; st.rerun()

# --- 6. صفحة الإدارة ---
elif st.session_state.page == "admin":
    if st.button("⬅️ العودة للرئيسية"): st.session_state.page = "home"; st.rerun()
    st.header("📊 لوحة الإدارة والتقارير")
    pw = st.text_input("كلمة المرور", type="password")
    if pw == "1234":
        if st.button("🗂️ إدارة بيانات الطلاب (Excel)", use_container_width=True):
            st.session_state.page = "data_management"; st.rerun()
        st.divider()
        c_status, c_del = st.columns(2)
        with c_status:
            is_open = get_system_status()
            if is_open:
                st.success("🟢 النظام: مفتوح")
                if st.button("🔴 إيقاف الرصد"):
                    supabase.table("settings").update({"is_open": False}).eq("setting_name", "attendance_status").execute(); st.rerun()
            else:
                st.error("🔴 النظام: مغلق")
                if st.button("🟢 تفعيل الرصد"):
                    supabase.table("settings").update({"is_open": True}).eq("setting_name", "attendance_status").execute(); st.rerun()
        with c_del:
            st.warning("🗑️ حذف بيانات يوم")
            d_date = st.date_input("اختر التاريخ", datetime.now(), key="del_date")
            if st.button(f"⚠️ مسح غياب يوم {d_date}"): st.session_state.confirm_delete = True
            if st.session_state.confirm_delete:
                st.error("تأكيد الحذف؟")
                if st.button("✅ نعم"):
                    supabase.table('attendance').delete().eq('date', str(d_date)).execute()
                    st.session_state.confirm_delete = False; st.success("تم الحذف"); time.sleep(0.5); st.rerun()
        st.divider()
        rep_date = st.date_input("📅 تاريخ المتابعة", datetime.now(), key="rep_date")
        att = supabase.table('attendance').select("*").eq('date', str(rep_date)).execute()
        std = supabase.table('students').select("student_name, section, committee").execute()
        t1, t2 = st.tabs(["⚠️ كشف الغياب التفصيلي", "🚩 حالة اللجان"])
        with t1:
            if att.data:
                df_a, df_s = pd.DataFrame(att.data), pd.DataFrame(std.data)
                m = pd.merge(df_a, df_s, on='student_name', how='left')
                final = m[m['status'].isin(['غائب', 'متأخر'])][['student_name', 'section', 'committee_x', 'status']]
                final.columns = ['الاسم', 'الشعبة', 'اللجنة', 'الحالة']
                msg = f"*تقرير الغياب - {rep_date}*\n\n"
                for _, r in final.iterrows(): msg += f"👤 {r['الاسم']}\n🏢 الشعبة: {r['الشعبة']} | 🎯 اللجنة: {r['اللجنة']}\n🚩 الحالة: *{r['الحالة']}*\n---\n"
                st.link_button("📱 إرسال الكشف عبر واتساب", f"https://wa.me/?text={urllib.parse.quote(msg)}"); st.table(final)
            else: st.info("لا توجد سجلات.")
        with t2:
            all_c = set([str(s['committee']) for s in std.data if s['committee']])
            done_c = set([str(a['committee']) for a in att.data])
            not_done = sorted(list(all_c - done_c), key=smart_sort)
            c_done, c_not = st.columns(2)
            c_done.success(f"✅ رصدت ({len(done_c)}):\n\n" + ", ".join(sorted(list(done_c), key=smart_sort)))
            c_not.error(f"❌ لم ترصد ({len(not_done)}):\n\n" + ", ".join(not_done))
    else: st.info("🔓 أدخل كلمة المرور")

# --- 7. صفحة إدارة البيانات ---
elif st.session_state.page == "data_management":
    if st.button("⬅️ العودة للإدارة"): st.session_state.page = "admin"; st.rerun()
    st.header("🗂️ إدارة بيانات الطلاب")
    tab_upload, tab_edit = st.tabs(["📤 رفع وحذف البيانات", "✏️ تعديل بيانات طالب"])
    with tab_upload:
        st.warning("⚠️ حذف جميع الأسماء")
        if st.button("❌ مسح قاعدة البيانات"):
            supabase.table('students').delete().neq('id', 0).execute()
            st.success("تم الحذف.")
        st.divider()
        uploaded_file = st.file_uploader("رفع ملف Excel جديد", type=['xlsx'])
        if uploaded_file:
            df = pd.read_excel(uploaded_file)
            if st.button("🚀 بدء الرفع"):
                supabase.table('students').insert(df.to_dict(orient='records')).execute()
                st.success("تم الرفع بنجاح!")
    with tab_edit:
        search_name = st.text_input("ابحث عن اسم الطالب للتعديل:")
        if search_name:
            res = supabase.table('students').select("*").ilike('student_name', f'%{search_name}%').execute()
            if res.data:
                for student in res.data:
                    with st.expander(f"تعديل: {student['student_name']}"):
                        new_name = st.text_input("الاسم", student['student_name'], key=f"n_{student['id']}")
                        new_sec = st.text_input("الشعبة", student['section'], key=f"s_{student['id']}")
                        new_comm = st.text_input("اللجنة", student['committee'], key=f"c_{student['id']}")
                        if st.button("💾 حفظ التعديل", key=f"b_{student['id']}"):
                            supabase.table('students').update({"student_name": new_name, "section": new_sec, "committee": new_comm}).eq('id', student['id']).execute()
                            st.success("تم التحديث!"); time.sleep(0.5); st.rerun()
