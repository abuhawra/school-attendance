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
    .teacher-log-span {
        background-color: #f0f2f6; padding: 2px 8px; border-radius: 5px; color: #1a237e; font-weight: bold; font-size: 14px; border: 1px solid #d1d9e6;
    }
    </style>
''', unsafe_allow_html=True)

if 'page' not in st.session_state:
    st.session_state.page = "home"

# --- 🛠️ دالة بناء رسالة الواتساب ---
def get_wa_link(df, status_type, d):
    if df.empty: return None
    header_emoji = "🚫" if "غائب" in status_type else "⏳"
    msg = f"{header_emoji} *قائمة {status_type}*%0A"
    msg += f"📅 *التاريخ:* {d}%0A"
    msg += "-----------------%0A"
    df_sorted = df.copy()
    df_sorted['committee_int'] = pd.to_numeric(df_sorted['committee'], errors='coerce').fillna(0)
    df_sorted = df_sorted.sort_values(by='committee_int')
    
    for _, r in df_sorted.iterrows():
        msg += f"📦 *اللجنة :* {r['committee']}%0A"
        msg += f"👤 *الاسم:* {r['student_name']}%0A"
        msg += f"🏫 *الشعبة:* {r.get('الشعبة','--')}%0A"
        msg += f"⚠️ *الحالة:* {r['status']}%0A"
        msg += "-----------------%0A" 
    return f"https://wa.me/?text={msg}"

# --- 1. الصفحة الرئيسية ---
if st.session_state.page == "home":
    st.markdown(f'''
        <div class="main-header">
            <h1 style="margin:0; font-size: 35px;">التحضير التقني</h1>
            <h2 style="margin:0; font-size: 28px;">مدرسة القطيف الثانوية</h2>
            <p style="color:#ffd700; font-size:22px; margin-top:10px; font-weight: bold;">مدير المدرسة : أ. فراس آل عبدالمحسن</p>
            <div style="font-size: 22px; margin-top: 22px; border-top: 1px solid rgba(255,255,255,0.2); padding-top: 22px;">
                <h3 style="margin:0; font-size: 22px;">فكرة و برمجة </h3>
                <h4 style="margin:0; font-size: 22px;">أ. عارف أحمد الحداد </h4>
                <h5 style="margin:0; font-size: 22px;">2026</h5>
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

# --- 2. تسجيل دخول المعلم ---
elif st.session_state.page == "t_log":
    if st.button("⬅️ عودة"): st.session_state.page = "home"; st.rerun()
    tid = st.text_input("أدخل السجل المدني للمعلم:", type="password")
    if st.button("دخول للنظام"):
        res = supabase.table("teachers").select("*").eq("national_id", tid.strip()).execute()
        if res.data:
            st.session_state.teacher = res.data[0]['name_tech']
            st.session_state.page = "mark"; st.rerun()
        else: st.error("عذراً، السجل المدني غير مسجل.")

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
                choice = st.radio(f"👤 {s['student_name']}", ["حاضر", "غائب", "متأخر"], index=["حاضر", "غائب", "متأخر"].index(prev), key=s['student_name'], horizontal=True)
                results.append({"student_name": s['student_name'], "committee": str(sel_c), "status": choice, "date": today, "teacher_name": st.session_state.teacher})
            
            if st.button("💾 حفظ الرصد النهائي", use_container_width=True):
                # التعديل: جلب الأسماء السابقة للمعلمين الذين حضروا نفس اللجنة اليوم
                prev_teachers = [i['teacher_name'] for i in old_att.data if i.get('teacher_name')]
                all_teachers = list(dict.fromkeys(prev_teachers + [st.session_state.teacher]))
                teacher_string = " | ".join(all_teachers)
                
                # تحديث بيانات المعلم في النتائج الجديدة لتشمل الجميع
                for item in results:
                    item['teacher_name'] = teacher_string
                
                supabase.table('attendance').delete().eq("committee", sel_c).eq("date", today).execute()
                supabase.table('attendance').insert(results).execute()
                st.snow()
                st.session_state.page = "thank_you"; st.rerun()

# --- 4. صفحة الشكر ---
elif st.session_state.page == "thank_you":
    st.markdown(f'''
        <div class="thank-you-card">
            <h1 style="color: #22c55e; font-size: 50px;">👏 شكراً لك</h1>
            <h2 style="color: #1a237e;">الأستاذ: {st.session_state.get('teacher', 'المعلم')}</h2>
            <p style="font-size: 20px;">تم حفظ رصد الطلاب بنجاح في النظام.</p>
        </div>
    ''', unsafe_allow_html=True)
    if st.button("🏠 العودة للصفحة الرئيسية", use_container_width=True, type="primary"):
        st.session_state.page = "home"; st.rerun()

# --- 5. قسم الإدارة ---
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
            
            report_df = df_all[df_all['status'].isin(['غائب', 'متأخر'])].copy()
            report_df['committee_sort'] = pd.to_numeric(report_df['committee'], errors='coerce').fillna(0)
            report_df = report_df.sort_values(by='committee_sort')
            
            final_view = report_df[['committee', 'student_name', 'الشعبة', 'status']]
            final_view.columns = ['اللجنة', 'اسم الطالب', 'الشعبة', 'الحالة']
            st.dataframe(final_view, use_container_width=True, hide_index=True)
            
            c1, c2 = st.columns(2)
            with c1:
                link_abs = get_wa_link(df_all[df_all['status'] == "غائب"], "الغائبين", d)
                if link_abs: st.markdown(f'<a href="{link_abs}" target="_blank" class="wa-link wa-absent">🚫 إرسال الغائبين</a>', unsafe_allow_html=True)
            with c2:
                link_late = get_wa_link(df_all[df_all['status'] == "متأخر"], "المتأخرين", d)
                if link_late: st.markdown(f'<a href="{link_late}" target="_blank" class="wa-link wa-late">⏳ إرسال المتأخرين</a>', unsafe_allow_html=True)

    with tab2:
        st.subheader("🏘️ سجل تحضير اللجان (كل من شارك بالرصد)")
        att_today = supabase.table('attendance').select("committee, teacher_name").eq("date", str(datetime.now().date())).execute()
        
        # تجميع المعلمين لكل لجنة
        com_teachers = {}
        for row in att_today.data:
            c = str(row['committee'])
            t_name = row['teacher_name']
            if c not in com_teachers:
                com_teachers[c] = t_name # هنا t_name يحتوي بالفعل على السلسلة المدمجة

        res_s = supabase.table('students').select("committee").execute()
        all_c = sorted(list(set([str(i['committee']) for i in res_s.data])), key=lambda x: int(x) if x.isdigit() else 0)
        
        c1, c2 = st.columns(2)
        with c1:
            st.success("✅ لجان تم رصدها")
            for c in all_c:
                if c in com_teachers:
                    names = com_teachers[c].replace(" | ", " ⬅️ ")
                    st.markdown(f"📍 **لجنة {c}** : <span class='teacher-log-span'>{names}</span>", unsafe_allow_html=True)
        with c2:
            st.error("❌ لجان لم تُرصد")
            for c in all_c:
                if c not in com_teachers: st.write(f"⚠️ لجنة {c}")

    with tab3:
        if st.text_input("رمز حماية البيانات:", type="password") == "4321":
            st.subheader("🗑️ تنظيف البيانات")
            del_date = st.date_input("اختر تاريخاً لحذف تحضيره:", datetime.now(), key="del_date")
            if st.button("❌ تأكيد حذف سجلات هذا اليوم"):
                supabase.table('attendance').delete().eq("date", str(del_date)).execute()
                st.warning(f"تم مسح سجلات {del_date}")
            
            st.divider()
            st.subheader("👨‍🎓 إدارة الطلاب والمعلمين")
            # (أكواد الرفع والتحميل المعتادة لم تتغير لضمان استقرار الوظائف)
            res_s = supabase.table('students').select("*").execute()
            if res_s.data:
                df_s = pd.DataFrame(res_s.data)
                st.download_button("📥 نسخة طلاب Excel", io.BytesIO(pd.ExcelWriter(io.BytesIO(), engine='openpyxl').book.save(io.BytesIO()) or b'').getvalue(), "students.xlsx")
            
            up_s = st.file_uploader("تحديث الطلاب:", key="up_s")
            if up_s and st.button("🚀 تحديث الطلاب"):
                df_ns = pd.read_csv(up_s) if up_s.name.endswith('.csv') else pd.read_excel(up_s)
                supabase.table('students').delete().neq('student_name', '0').execute()
                supabase.table('students').insert(df_ns.to_dict('records')).execute()
                st.success("تم التحديث!")
