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
    
    /* ضبط عرض الجداول والبيانات للجوال */
    .stDataFrame { width: 100% !important; }
    
    .wa-link { text-decoration: none; color: white !important; display: block; text-align: center; padding: 12px; border-radius: 10px; font-weight: bold; margin-bottom: 10px; font-size: 18px; }
    .wa-absent { background-color: #dc3545; }
    .wa-late { background-color: #fd7e14; }
    
    .main-header { 
        background-color: #1a237e; padding: 30px; text-align: center; color: white; 
        border-radius: 20px; margin-bottom: 25px; border-bottom: 8px solid #ffd700; 
    }
    .thank-you-card {
        text-align: center; padding: 50px; background: white; border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1); border: 2px solid #1a237e; margin-top: 50px;
    }
    </style>
''', unsafe_allow_html=True)

if 'page' not in st.session_state:
    st.session_state.page = "home"

# --- 🛠️ دالة بناء رسالة الواتساب المنسقة ---
def get_wa_link(df, status_type, d):
    if df.empty: return None
    header_emoji = "🚫" if "غائب" in status_type else "⏳"
    msg = f"{header_emoji} *قائمة {status_type}*%0A"
    msg += f"📅 *التاريخ:* {d}%0A"
    msg += "-----------------%0A"
    for _, r in df.iterrows():
        msg += f"📦 *اللجنة :* {r['committee']}%0A"
        msg += f"👤 *الاسم:* {r['student_name']}%0A"
        msg += f"🏫 *الشعبة:* {r.get('الشعبة','--')}%0A"
        msg += f"⚠️ *الحالة:* {r['status']}%0A"
        msg += "-----------------%0A" 
    return f"https://wa.me/?text={msg}"

# --- 1. الصفحة الرئيسية (الغلاف) ---
if st.session_state.page == "home":
    st.markdown(f'''
        <div class="main-header">
            <h1 style="margin:0; font-size: 35px;">التحضير التقني</h1>
            <h2 style="margin:0; font-size: 28px;">مدرسة القطيف الثانوية</h2>
            <p style="color:#ffd700; font-size:22px; margin-top:10px; font-weight: bold;">برمجة: أ. عارف أحمد الحداد</p>
            <div style="font-size: 20px; margin-top: 10px; border-top: 1px solid rgba(255,255,255,0.2); padding-top: 10px;">
                مدير المدرسة: أ. فراس آل عبدالمحسن
            </div>
        </div>
    ''', unsafe_allow_html=True)
    
    col_b = st.columns([1, 2, 1])[1]
    with col_b:
        if st.button("📝 رصد غياب الطلاب اليومي", use_container_width=True, type="primary"):
            st.session_state.page = "t_log"; st.rerun()
        st.write("")
        if st.button("⚙️ لوحة الإدارة والتقارير الموحدة", use_container_width=True):
            st.session_state.page = "a_log"; st.rerun()

# --- 2. تسجيل دخول المعلم بالرقم المدني ---
elif st.session_state.page == "t_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    tid = st.text_input("أدخل السجل المدني للمعلم:", type="password")
    if st.button("دخول للنظام"):
        res = supabase.table("teachers").select("*").eq("national_id", tid.strip()).execute()
        if res.data:
            st.session_state.teacher = res.data[0]['name_tech']
            st.session_state.page = "mark"; st.rerun()
        else: st.error("عذراً، السجل المدني غير مسجل.")

# --- 3. واجهة رصد الطلاب وتأثير النجاح ---
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
                choice = st.radio(f"👤 {s['student_name']}", ["حاضر", "غائب", "متأخر"], index=["حاضر", "غائب", "متأخر"].index(prev), key=s['student_name'], horizontal=True)
                results.append({"student_name": s['student_name'], "committee": str(sel_c), "status": choice, "date": today, "teacher_name": st.session_state.teacher})
            
            if st.button("💾 حفظ الرصد النهائي", use_container_width=True):
                supabase.table('attendance').delete().eq("committee", sel_c).eq("date", today).execute()
                supabase.table('attendance').insert(results).execute()
                st.snow() # تأثير الاحتفال
                st.session_state.page = "thank_you"; st.rerun()

# --- 4. صفحة الشكر النهائية ---
elif st.session_state.page == "thank_you":
    st.markdown(f'''
        <div class="thank-you-card">
            <h1 style="color: #22c55e; font-size: 50px;">👏 شكراً لك</h1>
            <h2 style="color: #1a237e;">الأستاذ: {st.session_state.get('teacher', 'المعلم')}</h2>
            <p style="font-size: 20px;">تم حفظ رصد الطلاب بنجاح في النظام.</p>
        </div>
    ''', unsafe_allow_html=True)
    st.write("")
    if st.button("🏠 العودة للصفحة الرئيسية", use_container_width=True, type="primary"):
        st.session_state.page = "home"; st.rerun()

# --- 5. قسم الإدارة والتقارير ---
elif st.session_state.page == "a_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    if st.text_input("كلمة مرور الإدارة:", type="password") == "1234": 
        st.session_state.page = "admin"; st.rerun()

elif st.session_state.page == "admin":
    if st.button("⬅️ تسجيل خروج"): st.session_state.page = "home"; st.rerun()
    tab1, tab2, tab3 = st.tabs(["📊 تقارير الواتساب", "🏘️ حالة اللجان", "💾 إدارة البيانات"])
    
    with tab1:
        d = st.date_input("تاريخ التقرير:", datetime.now())
        res_att = supabase.table("attendance").select("*").eq("date", str(d)).execute()
        if res_att.data:
            df_all = pd.DataFrame(res_att.data)
            res_std = supabase.table("students").select("student_name, class_name").execute()
            s_map = dict(zip([i['student_name'] for i in res_std.data], [i['class_name'] for i in res_std.data]))
            df_all['الشعبة'] = df_all['student_name'].map(s_map).fillna("---")
            
            # عرض الجدول باللغة العربية
            report_df = df_all[df_all['status'].isin(['غائب', 'متأخر'])][['committee', 'student_name', 'الشعبة', 'status']]
            report_df.columns = ['اللجنة', 'اسم الطالب', 'الشعبة', 'الحالة']
            st.dataframe(report_df, use_container_width=True, hide_index=True)
            
            c1, c2 = st.columns(2)
            with c1:
                link_abs = get_wa_link(df_all[df_all['status'] == "غائب"], "الغائبين", d)
                if link_abs: st.markdown(f'<a href="{link_abs}" target="_blank" class="wa-link wa-absent">🚫 إرسال الغائبين</a>', unsafe_allow_html=True)
            with c2:
                link_late = get_wa_link(df_all[df_all['status'] == "متأخر"], "المتأخرين", d)
                if link_late: st.markdown(f'<a href="{link_late}" target="_blank" class="wa-link wa-late">⏳ إرسال المتأخرين</a>', unsafe_allow_html=True)

    with tab2:
        st.subheader("🏘️ حالة رصد اللجان اليوم")
        att_today = supabase.table('attendance').select("committee, teacher_name").eq("date", str(datetime.now().date())).execute()
        done_dict = {str(i['committee']): i['teacher_name'] for i in att_today.data}
        res_s = supabase.table('students').select("committee").execute()
        all_c = sorted(list(set([str(i['committee']) for i in res_s.data])), key=lambda x: int(x) if x.isdigit() else 0)
        c1, c2 = st.columns(2)
        with c1:
            st.success("✅ تم الرصد")
            for c in all_c:
                if c in done_dict: st.write(f"📍 لجنة {c} - ({done_dict[c]})")
        with c2:
            st.error("❌ لم تُرصد")
            for c in all_c:
                if c not in done_dict: st.write(f"⚠️ لجنة {c}")

    with tab3:
        if st.text_input("رمز حماية البيانات:", type="password") == "4321":
            # --- حذف التحضير لتاريخ محدد ---
            st.subheader("🗑️ تنظيف البيانات")
            del_date = st.date_input("اختر تاريخاً لحذف تحضيره:", datetime.now(), key="del_date")
            if st.button("❌ تأكيد حذف سجلات هذا اليوم"):
                supabase.table('attendance').delete().eq("date", str(del_date)).execute()
                st.warning(f"تم مسح كافة سجلات يوم {del_date}")
            
            st.divider()

            # --- إدارة الطلاب (نسخ احتياطي واسترجاع) ---
            st.subheader("👨‍🎓 إدارة الطلاب")
            res_s = supabase.table('students').select("*").execute()
            if res_s.data:
                df_s = pd.DataFrame(res_s.data)
                sc1, sc2 = st.columns(2)
                with sc1: st.download_button("📥 نسخة طلاب CSV", df_s.to_csv(index=False).encode('utf-8-sig'), "students.csv", use_container_width=True)
                with sc2:
                    buf_s = io.BytesIO()
                    with pd.ExcelWriter(buf_s, engine='openpyxl') as wr: df_s.to_excel(wr, index=False)
                    st.download_button("📊 نسخة طلاب Excel", buf_s.getvalue(), "students.xlsx", use_container_width=True)
            
            up_s = st.file_uploader("رفع ملف الطلاب الجديد:", key="up_s")
            if up_s and st.button("🚀 تحديث قائمة الطلاب"):
                df_ns = pd.read_csv(up_s) if up_s.name.endswith('.csv') else pd.read_excel(up_s)
                supabase.table('students').delete().neq('student_name', '0').execute()
                supabase.table('students').insert(df_ns.to_dict('records')).execute()
                st.success("تم تحديث بيانات الطلاب!")

            st.divider()

            # --- إدارة المعلمين (نسخ احتياطي واسترجاع) ---
            st.subheader("👨‍🏫 إدارة المعلمين")
            res_t = supabase.table('teachers').select("*").execute()
            if res_t.data:
                df_t = pd.DataFrame(res_t.data)
                tc1, tc2 = st.columns(2)
                with tc1: st.download_button("📥 نسخة معلمين CSV", df_t.to_csv(index=False).encode('utf-8-sig'), "teachers.csv", use_container_width=True)
                with tc2:
                    buf_t = io.BytesIO()
                    with pd.ExcelWriter(buf_t, engine='openpyxl') as wr: df_t.to_excel(wr, index=False)
                    st.download_button("📊 نسخة معلمين Excel", buf_t.getvalue(), "teachers.xlsx", use_container_width=True)
            
            up_t = st.file_uploader("رفع ملف المعلمين الجديد:", key="up_t")
            if up_t and st.button("🔄 استرجاع وتحديث المعلمين"):
                df_nt = pd.read_csv(up_t) if up_t.name.endswith('.csv') else pd.read_excel(up_t)
                supabase.table('teachers').delete().neq('name_tech', '0').execute()
                supabase.table('teachers').insert(df_nt.to_dict('records')).execute()
                st.success("تم تحديث بيانات المعلمين بنجاح!")
