import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
import urllib.parse

# 1. إعدادات الاتصال
url = "https://lsmevvsogsqqqjyuqzbx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzbWV2dnNvZ3NxcXFqeXVxemJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MDMyOTgsImV4cCI6MjA5Mjk3OTI5OH0.ecqJS75fPbKqwSAiBzP6Qonn4cuymgwjB96tIGek8j0"

if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(url, key)
supabase = st.session_state.supabase

# 2. تعريف الدوال الأساسية
def smart_sort(x):
    try: return int(x)
    except: return str(x)

def get_system_status():
    try:
        res = supabase.table("settings").select("is_open").eq("setting_name", "attendance_status").execute()
        return res.data[0]['is_open'] if res.data else True
    except: return True

# تهيئة الجلسة
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'confirm_delete' not in st.session_state: st.session_state.confirm_delete = False

st.set_page_config(page_title="نظام غياب الطلاب - أ. عارف الحداد", layout="wide")

# 3. القائمة الجانبية
st.sidebar.title("🏫 القائمة الرئيسية")
page = st.sidebar.radio("انتقل إلى:", ["🔑 دخول المعلم", "📊 لوحة الإدارة"])

# --- واجهة المعلم ---
if page == "🔑 دخول المعلم":
    if not get_system_status():
        st.error("🚫 النظام مغلق حالياً.")
    else:
        if not st.session_state.logged_in:
            st.header("🔑 تسجيل دخول المعلم")
            # إضافة عبارة البرمجة المطلوبة
            st.caption("💠 برمجة (أ.عارف أحمد الحداد)") 
            
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
            st.divider()
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
                
                # تعديل الزر ليصبح (حفظ وخروج)
                if st.button("💾 حفظ الكشف وخروج"):
                    supabase.table('attendance').delete().eq('committee', sel_c).eq('date', str(t_date)).execute()
                    supabase.table('attendance').insert(results).execute()
                    st.success("✅ تم الحفظ بنجاح!")
                    time.sleep(1)
                    st.session_state.logged_in = False # تسجيل الخروج تلقائياً بعد الحفظ
                    st.rerun()

# --- واجهة الإدارة ---
elif page == "📊 لوحة الإدارة":
    st.header("📊 لوحة الإدارة والتقارير")
    pw = st.sidebar.text_input("كلمة المرور", type="password")
    if pw == "1234":
        # إعدادات النظام والحذف
        c_status, c_del = st.columns(2)
        with c_status:
            is_open = get_system_status()
            if is_open:
                st.success("🟢 النظام: مفتوح")
                if st.button("🔴 إيقاف الرصد"):
                    supabase.table("settings").update({"is_open": False}).eq("setting_name", "attendance_status").execute()
                    st.rerun()
            else:
                st.error("🔴 النظام: مغلق")
                if st.button("🟢 تفعيل الرصد"):
                    supabase.table("settings").update({"is_open": True}).eq("setting_name", "attendance_status").execute()
                    st.rerun()
        
        with c_del:
            st.warning("🗑️ حذف بيانات يوم")
            d_date = st.date_input("اختر التاريخ", datetime.now(), key="del_date")
            if st.button(f"⚠️ مسح غياب يوم {d_date}"): st.session_state.confirm_delete = True
            if st.session_state.confirm_delete:
                st.error("تأكيد الحذف النهائي؟")
                cy, cn = st.columns(2)
                if cy.button("✅ نعم"):
                    supabase.table('attendance').delete().eq('date', str(d_date)).execute()
                    st.session_state.confirm_delete = False
                    st.success("تم الحذف"); time.sleep(0.5); st.rerun()
                if cn.button("❌ تراجع"):
                    st.session_state.confirm_delete = False
                    st.rerun()

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
                
                # الواتساب التفصيلي
                msg = f"*تقرير الغياب - {rep_date}*\n\n"
                for _, r in final.iterrows():
                    msg += f"👤 {r['الاسم']}\n🏢 الشعبة: {r['الشعبة']} | 🎯 اللجنة: {r['اللجنة']}\n🚩 الحالة: *{r['الحالة']}*\n---\n"
                st.link_button("📱 إرسال الكشف التفصيلي عبر واتساب", f"https://wa.me/?text={urllib.parse.quote(msg)}")
                st.table(final)
            else: st.info("لا توجد سجلات.")

        with t2:
            # تقرير حالة اللجان (تم إصلاح NameError)
            all_comms = set([str(s['committee']) for s in std.data if s['committee']])
            done_comms = set([str(a['committee']) for a in att.data])
            not_done = sorted(list(all_comms - done_comms), key=smart_sort)
            
            c_done, c_not = st.columns(2)
            c_done.success(f"✅ لجان رصدت ({len(done_comms)}):\n\n" + ", ".join(sorted(list(done_comms), key=smart_sort)))
            c_not.error(f"❌ لجان لم ترصد ({len(not_done)}):\n\n" + ", ".join(not_done))
    else: st.sidebar.info("أدخل كلمة المرور (1234)")
