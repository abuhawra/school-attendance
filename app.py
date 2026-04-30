import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
import urllib.parse
import io

# 1. إعدادات الاتصال بقاعدة البيانات
url = "https://lsmevvsogsqqqjyuqzbx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzbWV2dnNvZ3NxcXFqeXVxemJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MDMyOTgsImV4cCI6MjA5Mjk3OTI5OH0.ecqJS75fPbKqwSAiBzP6Qonn4cuymgwjB96tIGek8j0"

if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(url, key)
supabase = st.session_state.supabase

# 2. التنسيق الجمالي (CSS)
st.set_page_config(page_title="التحضير التقني - مدرسة القطيف", layout="centered")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    .stApp { background-color: #f8f9fa; }
    .center-div { width: 100%; text-align: center; direction: rtl; }
    .main-title { font-size: 30px; font-weight: 800; color: #1a237e; }
    .sub-title { font-size: 20px; color: #455a64; }
    
    /* تنسيق الأزرار */
    div.stButton > button { 
        width: 100% !important; 
        max-width: 350px !important; 
        height: 55px !important; 
        border-radius: 12px !important; 
        font-size: 18px !important; 
        font-weight: bold !important; 
        margin: 10px auto !important; 
        display: block !important; 
    }
    div.stButton > button[kind="primary"] { background-color: #007bff !important; color: white !important; border: none; }
    div.stButton > button[kind="secondary"] { background-color: #ff9800 !important; color: white !important; border: none; }
    
    /* تنسيق جدول البيانات */
    div[data-testid="stDataFrame"] { direction: rtl !important; }
    </style>
    """, unsafe_allow_html=True)

if 'page' not in st.session_state: st.session_state.page = "home"

def go_home():
    st.session_state.page = "home"
    st.rerun()

# ==========================================
# 1. الواجهة الرئيسية
# ==========================================
if st.session_state.page == "home":
    st.markdown('<div class="center-div">', unsafe_allow_html=True)
    st.markdown('<p class="main-title">التحضير التقني لمدرسة القطيف الثانوية</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">تصميم وتنفيذ أستاذ عارف أحمد الحداد</p>', unsafe_allow_html=True)
    st.markdown('<p style="font-weight:bold; color:#1565c0;">مدير المدرسة أ. فراس عبدالله آل عبدالمحسن</p>', unsafe_allow_html=True)
    st.markdown('<hr>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("📝 الدخول للتحضير", type="primary"):
        st.session_state.page = "att_login"; st.rerun()
    
    if st.button("⚙️ دخول الإدارة", type="secondary"):
        st.session_state.page = "admin_login"; st.rerun()

# ==========================================
# 2. صفحة رصد الحضور
# ==========================================
elif st.session_state.page == "att_login":
    if st.button("⬅️ عودة"): go_home()
    st.markdown('<div class="center-div"><h3>تسجيل دخول المعلم</h3></div>', unsafe_allow_html=True)
    t_id = st.text_input("أدخل رقم السجل المدني:", type="password")
    if st.button("دخول", type="primary"):
        res = supabase.table("teachers").select("*").eq("national_id", t_id.strip()).execute()
        if res.data:
            st.session_state.teacher_name = res.data[0]['name_tech']
            st.session_state.page = "taking_attendance"; st.rerun()
        else: st.error("السجل المدني غير مسجل")

elif st.session_state.page == "taking_attendance":
    today = str(datetime.now().date())
    st.markdown(f'<div style="text-align:right; font-weight:bold; color:#1a237e;">📅 تاريخ اليوم: {today}</div>', unsafe_allow_html=True)
    st.info(f"المعلم: {st.session_state.teacher_name}")
    
    # جلب اللجان وترتيبها رقمياً
    s_data = supabase.table('students').select("committee").execute()
    raw_coms = list(set([i['committee'] for i in s_data.data if i['committee'] is not None]))
    try:
        sorted_coms = sorted(raw_coms, key=lambda x: int(x))
    except:
        sorted_coms = sorted([str(x) for x in raw_coms])

    sel_c = st.selectbox("اختر اللجنة:", ["---"] + [str(x) for x in sorted_coms])
    
    if sel_c != "---":
        # 1. جلب الطلاب
        students = supabase.table('students').select("*").eq('committee', sel_c).execute()
        
        # 2. جلب الرصد السابق لتاريخ اليوم (للتعديل)
        existing_att = supabase.table('attendance').select("*").eq('committee', sel_c).eq('date', today).execute()
        att_dict = {a['student_name']: a['status'] for a in existing_att.data} if existing_att.data else {}

        results = []
        st.write("---")
        for s in students.data:
            st.write(f"👤 **{s['student_name']}**")
            
            # تحديد الحالة المسجلة سابقاً أو الافتراضي "حاضر"
            prev_status = att_dict.get(s['student_name'], "حاضر")
            idx = ["حاضر", "غائب", "متأخر"].index(prev_status)
            
            stat = st.radio(f"الحالة لـ {s['student_name']}", ["حاضر", "غائب", "متأخر"], index=idx, key=f"s_{s['id']}", horizontal=True)
            results.append({
                "student_name": s['student_name'], 
                "committee": str(sel_c), 
                "status": stat, 
                "date": today, 
                "teacher_name": st.session_state.teacher_name
            })
        
        if st.button("💾 حفظ وإرسال الكشف", type="primary"):
            try:
                # مسح الرصد القديم لنفس اليوم واللجنة لتجنب التكرار
                supabase.table('attendance').delete().eq('committee', sel_c).eq('date', today).execute()
                supabase.table('attendance').insert(results).execute()
                st.success("✅ تم حفظ وتحديث الرصد بنجاح!")
                time.sleep(1)
                go_home()
            except Exception as e:
                st.error(f"خطأ أثناء الحفظ: {e}")

# ==========================================
# 3. لوحة الإدارة والتقارير
# ==========================================
elif st.session_state.page == "admin_login":
    if st.button("⬅️ عودة"): go_home()
    pw = st.text_input("رمز دخول الإدارة:", type="password")
    if pw == "1234": st.session_state.page = "admin_panel"; st.rerun()

elif st.session_state.page == "admin_panel":
    if st.button("⬅️ تسجيل خروج"): go_home()
    
    tab1, tab2, tab3 = st.tabs(["📊 تقارير الواتساب", "🏘️ متابعة اللجان", "🛠️ إدارة البيانات"])
    
    # نافذة الواتساب
    with tab1:
        d_report = st.date_input("اختر التاريخ", datetime.now())
        res_att = supabase.table("attendance").select("*").eq("date", str(d_report)).execute()
        
        if res_att.data:
            df = pd.DataFrame(res_att.data)
            df_view = df[df['status'].isin(['غائب', 'متأخر'])]
            
            if not df_view.empty:
                st.subheader("إرسال التقارير التفصيلية 📲")
                for _, row in df_view.iterrows():
                    # جلب الشعبة بأمان
                    try:
                        s_info = supabase.table('students').select("class_name").eq("student_name", row['student_name']).execute()
                        c_name = s_info.data[0]['class_name'] if s_info.data else "غير محدد"
                    except: c_name = "غير محدد"

                    whatsapp_msg = (
                        f"🗓️ *التاريخ:* {d_report}%0A%0A"
                        f"👤 *الاسم:* {row['student_name']}%0A"
                        f"🏫 *الشعبة:* {c_name}%0A"
                        f"📦 *اللجنة:* {row['committee']}%0A"
                        f"⚠️ *الحالة:* *{row['status']}*%0A%0A"
                        f"مدرسة القطيف الثانوية"
                    )
                    wa_link = f"https://wa.me/?text={whatsapp_msg}"
                    st.markdown(f'<a href="{wa_link}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366;color:white;padding:12px;border-radius:10px;text-align:center;margin-bottom:8px;font-weight:bold;border:1px solid #128C7E;">إرسال تقرير: {row["student_name"]} 📲</div></a>', unsafe_allow_html=True)
            else: st.success("لا يوجد غياب أو تأخر في هذا التاريخ.")

    # نافذة متابعة اللجان
    with tab2:
        st.subheader("رصد اللجان اليوم")
        all_st = supabase.table('students').select("committee").execute()
        all_coms = set([str(i['committee']) for i in all_st.data if i['committee']])
        
        # اللجان التي رصدت اليوم فعلياً
        res_today = supabase.table("attendance").select("committee").eq("date", str(datetime.now().date())).execute()
        done_coms = set([str(i['committee']) for i in res_today.data]) if res_today.data else set()
        
        col1, col2 = st.columns(2)
        col1.error(f"لجان لم تُرصد ({len(all_coms - done_coms)})")
        col1.write(sorted(list(all_coms - done_coms), key=lambda x: int(x) if x.isdigit() else x))
        
        col2.success(f"لجان تـم رصدها ({len(done_coms)})")
        col2.write(sorted(list(done_coms), key=lambda x: int(x) if x.isdigit() else x))

    # نافذة إدارة البيانات
    with tab3:
        adm_pw = st.text_input("رمز الإدارة العليا (12345):", type="password")
        if adm_pw == "12345":
            st.write("---")
            if st.button("📥 تحميل نسخة احتياطية للطلاب (CSV)"):
                data = supabase.table("students").select("*").execute()
                csv = pd.DataFrame(data.data).to_csv(index=False).encode('utf-8-sig')
                st.download_button("حفظ الملف الآن", csv, "students_backup.csv", "text/csv")
            
            st.divider()
            st.write("📤 **إرجاع البيانات من ملف CSV**")
            up_file = st.file_uploader("اختر الملف المنسق", type="csv")
            if up_file and st.button("تأكيد رفع البيانات"):
                df_up = pd.read_csv(up_file)
                # حذف القديم ورفع الجديد
                supabase.table("students").delete().neq("id", 0).execute()
                supabase.table("students").insert(df_up.to_dict(orient='records')).execute()
                st.success("تم استيراد البيانات بنجاح!")
