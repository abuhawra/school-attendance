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

# 2. التنسيق الجمالي (CSS) لتوسيط الواجهة وتلوين الأزرار
st.set_page_config(page_title="التحضير التقني - مدرسة القطيف", layout="centered")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    .stApp { background-color: #f8f9fa; }
    .center-div { width: 100%; text-align: center; direction: rtl; }
    .main-title { font-size: 30px; font-weight: 800; color: #1a237e; margin-bottom: 0px; }
    .sub-title { font-size: 20px; color: #455a64; margin-top: 5px; }
    .manager-title { font-size: 18px; color: #1565c0; font-weight: bold; margin-top: 10px; }
    
    /* تنسيق الأزرار */
    div.stButton > button { width: 100% !important; max-width: 350px !important; height: 55px !important; border-radius: 12px !important; font-size: 18px !important; font-weight: bold !important; margin: 10px auto !important; display: block !important; }
    div.stButton > button[kind="primary"] { background-color: #007bff !important; color: white !important; border: none; }
    div.stButton > button[kind="secondary"] { background-color: #ff9800 !important; color: white !important; border: none; }
    
    div[data-testid="stDataFrame"] { direction: rtl !important; }
    </style>
    """, unsafe_allow_html=True)

if 'page' not in st.session_state: st.session_state.page = "home"

# --- دالة العودة للرئيسية ---
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
    st.markdown('<p class="manager-title">مدير المدرسة أ. فراس عبدالله آل عبدالمحسن</p>', unsafe_allow_html=True)
    st.markdown('<hr>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("📝 الدخول للتحضير", type="primary"):
        st.session_state.page = "att_login"; st.rerun()
    
    if st.button("⚙️ دخول الإدارة", type="secondary"):
        st.session_state.page = "admin_login"; st.rerun()

# ==========================================
# 2. صفحة التحضير
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
    st.info(f"المعلم: {st.session_state.teacher_name}")
    today = str(datetime.now().date())
    
    # جلب اللجان وترتيبها رقمياً
    s_data = supabase.table('students').select("committee").execute()
    raw_coms = list(set([i['committee'] for i in s_data.data if i['committee'] is not None]))
    try:
        sorted_coms = sorted(raw_coms, key=lambda x: int(x))
    except:
        sorted_coms = sorted([str(x) for x in raw_coms])

    sel_c = st.selectbox("اختر اللجنة:", ["---"] + [str(x) for x in sorted_coms])
    
    if sel_c != "---":
        students = supabase.table('students').select("*").eq('committee', sel_c).execute()
        results = []
        for s in students.data:
            st.write(f"👤 **{s['student_name']}**")
            # الافتراضي حاضر
            stat = st.radio(f"الحالة لـ {s['student_name']}", ["حاضر", "غائب", "متأخر"], index=0, key=f"s_{s['id']}", horizontal=True)
            results.append({
                "student_name": s['student_name'],
                "committee": str(sel_c),
                "status": stat,
                "date": today,
                "teacher_name": st.session_state.teacher_name,
                "class_name": s.get('class_name', 'غير محدد')
            })
        
        if st.button("💾 حفظ وإرسال الكشف", type="primary"):
            try:
                # حذف القديم وحفظ الجديد (بدون عمود class_name لتجنب أخطاء السوبابيس إذا لم يكن موجوداً)
                clean_results = [{k: v for k, v in r.items() if k != 'class_name'} for r in results]
                supabase.table('attendance').delete().eq('committee', sel_c).eq('date', today).execute()
                supabase.table('attendance').insert(clean_results).execute()
                st.success("✅ تم الحفظ بنجاح!")
                time.sleep(1)
                go_home()
            except Exception as e:
                st.error(f"خطأ في الحفظ: {e}")

# ==========================================
# 3. لوحة الإدارة والتقارير
# ==========================================
elif st.session_state.page == "admin_login":
    if st.button("⬅️ عودة"): go_home()
    pw = st.text_input("رمز دخول الإدارة:", type="password")
    if pw == "1234":
        st.session_state.page = "admin_panel"; st.rerun()

elif st.session_state.page == "admin_panel":
    if st.button("⬅️ خروج"): go_home()
    
    tab1, tab2, tab3 = st.tabs(["📊 تقارير الغياب", "🏘️ متابعة اللجان", "🛠️ إدارة الأسماء"])
    
    with tab1:
        d = st.date_input("اختر التاريخ", datetime.now())
        res = supabase.table("attendance").select("*").eq("date", str(d)).execute()
        
        if res.data:
            df = pd.DataFrame(res.data)
            df_view = df[df['status'].isin(['غائب', 'متأخر'])]
            
            if not df_view.empty:
                st.subheader("قائمة الغياب والتأخر")
                st.dataframe(df_view[['student_name', 'status', 'committee']], use_container_width=True)
                
                st.divider()
                st.subheader("إرسال تقارير الواتساب التفصيلية 📲")
                
                for _, row in df_view.iterrows():
                    # جلب بيانات الطالب الإضافية (مثل الشعبة) من جدول الطلاب
                    s_info = supabase.table('students').select("class_name").eq("student_name", row['student_name']).execute()
                    class_name = s_info.data[0]['class_name'] if s_info.data else "غير محدد"
                    
                    # صياغة رسالة الواتساب المنسقة
                    msg_text = (
                        f"🗓️ *التاريخ:* {d}%0A%0A"
                        f"👤 *الاسم:* {row['student_name']}%0A"
                        f"🏫 *الشعبة:* {class_name}%0A"
                        f"📦 *اللجنة:* {row['committee']}%0A"
                        f"⚠️ *الحالة:* *{row['status']}*%0A%0A"
                        f"مدرسة القطيف الثانوية"
                    )
                    
                    wa_link = f"https://wa.me/?text={msg_text}"
                    
                    # زر واتساب أخضر جذاب لكل طالب
                    st.markdown(f"""
                        <a href="{wa_link}" target="_blank" style="text-decoration: none;">
                            <div style="background-color: #25D366; color: white; padding: 12px; border-radius: 10px; text-align: center; margin-bottom: 8px; font-weight: bold; border: 1px solid #128C7E;">
                                إرسال تقرير الطالب: {row['student_name']} 📲
                            </div>
                        </a>
                    """, unsafe_allow_html=True)
            else:
                st.success("لا يوجد حالات غياب أو تأخر مسجلة لهذا اليوم.")

    with tab2:
        st.subheader("حالة اللجان")
        all_st = supabase.table('students').select("committee").execute()
        all_coms = set([str(i['committee']) for i in all_st.data if i['committee']])
        done_coms = set([str(i['committee']) for i in res.data]) if res.data else set()
        
        col1, col2 = st.columns(2)
        col1.error(f"لجان لم تحضر ({len(all_coms - done_coms)})")
        col1.write(list(all_coms - done_coms))
        col2.success(f"لجان حضرت ({len(done_coms)})")
        col2.write(list(done_coms))

    with tab3:
        st.subheader("إدارة البيانات")
        adm_pw = st.text_input("أدخل رمز الإدارة العليا (12345):", type="password")
        if adm_pw == "12345":
            st.success("صلاحية الوصول مقبولة")
            if st.button("📥 نسخة احتياطية لبيانات الطلاب"):
                all_s = supabase.table("students").select("*").execute()
                st.download_button("تحميل CSV", pd.DataFrame(all_s.data).to_csv(index=False).encode('utf-8-sig'), "students.csv")
            
            if st.button("🗑️ حذف جميع بيانات الطلاب", type="secondary"):
                st.error("هذا الإجراء سيقوم بمسح كافة الأسماء!")
