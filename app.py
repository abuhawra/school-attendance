import streamlit as st
import pandas as pd
from fpdf import FPDF
import arabic_reshaper
from bidi.algorithm import get_display
from datetime import datetime

# ==============================================================================
# 1. إعدادات الصفحة الرئيسية لنظام أثر
# ==============================================================================
st.set_page_config(
    page_title="نظام أثر الإداري - مدرسة القطيف الثانوية", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 2. دوال الدعم الفنية ومعالجة النصوص والخطوط العربية للـ PDF
# ==============================================================================
def format_ar(text):
    if not text:
        return ""
    reshaped_text = arabic_reshaper.reshape(str(text))
    return get_display(reshaped_text)

def get_clean_observer_string(teacher_name, valid_teachers_set):
    name_str = str(teacher_name).strip()
    if name_str in valid_teachers_set:
        return name_str
    if "|" in name_str:
        first_name = name_str.split("|")[0].strip()
        if first_name in valid_teachers_set:
            return first_name
    return "..........................................."

# دالة توليد محاضر الغياب الفردية الرسمية المطابقة للنموذج المطلوب بالكامل
def export_attendance_to_pdf_fpdf(df, report_date, valid_teachers_set):
    days_ar = {
        "Monday": "الإثنين", "Tuesday": "الثلاثاء", "Wednesday": "الأربعاء", 
        "Thursday": "الخميس", "Friday": "الجمعة", "Saturday": "السبت", "Sunday": "الأحد"
    }
    day_name_en = report_date.strftime('%A')
    day_name_ar = days_ar.get(day_name_en, day_name_en)
    date_str = report_date.strftime('%Y-%m-%d')
    
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # الاعتماد المباشر على ملف الخط المرفوع في مجلد مشروعك (arial.ttf) لمنع الانهيار
    pdf.add_font("CustomArial", "", "arial.ttf")
    pdf.set_font("CustomArial", size=12)
    
    for _, row in df.iterrows():
        pdf.add_page()
        
        # --- الترويسة الرسمية لوزارة التعليم (يمين) ---
        pdf.set_font("CustomArial", style="", size=11)
        pdf.set_text_color(0, 0, 0)
        pdf.set_xy(135, 15)
        pdf.cell(60, 6, format_ar("المملكة العربية السعودية"), ln=True, align="R")
        pdf.set_x(135)
        pdf.cell(60, 6, format_ar("وزارة التعليم"), ln=True, align="R")
        pdf.set_x(135)
        pdf.cell(60, 6, format_ar("الإدارة العامة للتعليم بالمنطقة الشرقية"), ln=True, align="R")
        pdf.set_x(135)
        pdf.cell(60, 6, format_ar("مكتب التعليم بالقطيف"), ln=True, align="R")
        pdf.set_x(135)
        pdf.cell(60, 6, format_ar("مدرسة القطيف الثانوية"), ln=True, align="R")
        
        # --- ترويسة الرؤية (منتصف) ---
        pdf.set_font("CustomArial", style="", size=13)
        pdf.set_xy(85, 18)
        pdf.cell(40, 6, format_ar("رؤية VISION"), ln=True, align="C")
        pdf.set_x(85)
        pdf.cell(40, 6, format_ar("2 3 0"), ln=True, align="C")
        pdf.set_font("CustomArial", style="", size=9)
        pdf.set_x(85)
        pdf.cell(40, 5, format_ar("وزارة التعليم"), ln=True, align="C")
        
        # --- إطار العنوان الفرعي الكحلي الإداري ---
        pdf.set_draw_color(0, 32, 96) 
        pdf.set_line_width(0.6) 
        pdf.rect(75, 48, 60, 10)
        pdf.set_xy(75, 50)
        pdf.set_font("CustomArial", style="", size=12)
        pdf.cell(60, 6, format_ar("الاختبارات - محضر غياب"), align="C", ln=True)
        
        # --- العنوان العريض للمحضر المحدث ---
        pdf.set_draw_color(0, 0, 0)
        pdf.set_line_width(0.5)
        pdf.rect(15, 63, 180, 12)
        pdf.set_xy(15, 66)
        pdf.set_font("CustomArial", style="", size=13)
        pdf.cell(180, 6, format_ar("محضر ( غـيـاب ) طالب في اختبارات نهاية الفصل الدراسي"), align="C", ln=True)
        
        # --- خانة اليوم والتاريخ المنفصلة التعبوية ---
        pdf.set_xy(80, 80)
        pdf.set_fill_color(220, 220, 220) 
        pdf.cell(30, 10, format_ar("التاريخ"), border=1, align="C", fill=True)
        pdf.cell(85, 10, format_ar(f"      /      /  ١٤٤٧ هـ  ({date_str})"), border=1, align="C")
        
        pdf.set_xy(15, 80)
        pdf.cell(20, 10, format_ar("اليوم"), border=1, align="C", fill=True)
        pdf.cell(45, 10, format_ar(day_name_ar), border=1, align="C", ln=True)
        
        # --- جدول بيانات الطالب الأساسية ---
        pdf.set_xy(15, 95)
        pdf.cell(25, 10, format_ar("الاسم رباعي"), border=1, align="C", fill=True)
        pdf.set_font("CustomArial", style="", size=12)
        student_title = row.get('اسم الطالب', row.get('student_name', '---'))
        pdf.cell(100, 10, format_ar(student_title), border=1, align="R")
        pdf.set_font("CustomArial", style="", size=11)
        pdf.cell(20, 10, format_ar("الشعبة"), border=1, align="C", fill=True)
        pdf.cell(35, 10, format_ar(row.get('الشعبة', row.get('section', '---'))), border=1, align="C", ln=True)
        
        # --- شبكة البيانات الأكاديمية والخيارات للفترات والفصول ---
        pdf.set_xy(15, 110)
        pdf.cell(35, 8, format_ar("رقم اللجنة"), border=1, align="C", fill=True)
        pdf.cell(35, 8, format_ar("الصف"), border=1, align="C", fill=True)
        pdf.cell(40, 8, format_ar("المادة"), border=1, align="C", fill=True)
        pdf.cell(35, 8, format_ar("الفترة"), border=1, align="C", fill=True)
        pdf.cell(35, 8, format_ar("الفصل الدراسي"), border=1, align="C", fill=True, ln=True)
        
        # صف محتويات الشبكة التعبوي
        pdf.set_xy(15, 118)
        pdf.cell(35, 18, format_ar(row.get('اللجنة', row.get('committee', '---'))), border=1, align="C")
        pdf.cell(35, 18, format_ar(""), border=1, align="C")
        pdf.cell(40, 18, format_ar(""), border=1, align="C")
        
        pdf.set_font("CustomArial", size=10)
        pdf.cell(35, 18, format_ar("[  ] الأولى   [  ] الثانية"), border=1, align="C")
        pdf.cell(35, 18, format_ar("[  ] الأول     [ X ] الثاني"), border=1, align="C", ln=True)
        
        # --- صندوق الملاحظات والإجراءات الإدارية المخطط ---
        pdf.set_font("CustomArial", size=11)
        pdf.set_xy(15, 142)
        pdf.rect(15, 142, 180, 45)
        pdf.set_xy(18, 144)
        pdf.cell(174, 6, format_ar("الإجراءات والملاحظات الإدارية:"), ln=True, align="R")
        pdf.set_text_color(120, 120, 120)
        pdf.set_x(18)
        pdf.cell(174, 10, format_ar(".........................................................................................................................................."), ln=True, align="R")
        pdf.set_x(18)
        pdf.cell(174, 10, format_ar(".........................................................................................................................................."), ln=True, align="R")
        
        # --- التوقيعات والاعتماد أسفل المحضر المحدث ---
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("CustomArial", style="", size=12)
        pdf.set_xy(15, 202)
        pdf.cell(90, 6, format_ar("مدير المدرسة"), ln=True, align="C")
        pdf.set_x(15)
        pdf.cell(90, 8, format_ar("أ. فراس آل عبدالمحسن"), ln=True, align="C")
        
        raw_teacher_name = row.get('المعلمون', row.get('teacher_name', ''))
        resolved_observer = get_clean_observer_string(raw_teacher_name, valid_teachers_set)
        
        pdf.set_xy(105, 202)
        pdf.cell(90, 6, format_ar("الملاحظ / مراقب اللجنة"), ln=True, align="C")
        pdf.set_x(105)
        pdf.cell(90, 8, format_ar(resolved_observer), ln=True, align="C")
        
        pdf.set_xy(15, 228)
        pdf.cell(90, 6, format_ar("التوقيع: ..................................."), align="C")
        pdf.cell(90, 6, format_ar("التوقيع: ..................................."), align="C")

    return bytes(pdf.output())

# ==============================================================================
# 3. إدارة الجلسة والبيانات التأسيسية للنظام (Session State)
# ==============================================================================
if 'teachers_data' not in st.session_state:
    st.session_state.teachers_data = [
        {'name_tech': 'عارف احمد'}, 
        {'name_tech': 'جعفر بن علي بن حسين آل ربح'}, 
        {'name_tech': 'سعيد بن حسن بن صالح المغرور'}
    ]

# تم إغلاق وتأمين مصفوفة المعلمين بشكل نهائي هنا لمنع أخطاء الـ SyntaxError المسببة للصفحة البيضاء
valid_teachers_set = {str(t['name_tech']).strip() for t in st.session_state.teachers_data}

if 'student_data' not in st.session_state:
    st.session_state.student_data = pd.DataFrame({
        'اللجنة': ['1', '1', '1', '3', '2'],
        'اسم الطالب': [
            'رضا بن علي بن أحمد الناصر', 
            'حيدر بن محمد بن سعيد اغريب', 
            'حسين بن هاني بن سعود آل درويش', 
            'أحمد بن فراس بن علي آل ربيع',
            'علي بن جاسم آل غانم'
        ],
        'الشعبة': ['201', '201', '201', '202', '205'],
        'الحالة': ['حاضر', 'حاضر', 'حاضر', 'حاضر', 'حاضر'],
        'المعلمون': [
            'عارف احمد | جعفر بن علي بن حسين آل ربح', 
            'عارف احمد | جعفر بن علي بن حسين آل ربح', 
            'عارف احمد | جعفر بن علي بن حسين آل ربح', 
            'فراس بن عبدالله حسن آل عبدالمحسن',
            'سعيد بن حسن بن صالح المغرور'
        ]
    })

# ==============================================================================
# 4. شريط التنقل الجانبي لجميع نوافذ البرنامج (Navigation Sidebar)
# ==============================================================================
st.sidebar.image("https://img.icons8.com/fluent/96/000000/fingerprint.png", width=80)
st.sidebar.title("نظام أثر الإداري")
st.sidebar.write("مدرسة القطيف الثانوية")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "انتقل بين نوافذ النظام:",
    ["🏠 لوحة التحكم الرئيسية", "📂 إدارة ورفع البيانات", "📝 رصد الحالات اليومية", "🖨️ طباعة محاضر الغياب الرسمية"]
)

st.sidebar.markdown("---")
st.sidebar.info("تطوير أ. عارف أحمد الـحـداد")

# ==============================================================================
# النافذة الأولى: 🏠 لوحة التحكم الرئيسية
# ==============================================================================
if page == "🏠 لوحة التحكم الرئيسية":
    st.header("🏠 لوحة التحكم والإحصائيات العامة")
    st.markdown("مرحباً بك في لوحة تحكم نظام أثر لإدارة أعمال لجان الاختبارات.")
    
    # بطاقات إحصائية سريعة
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("إجمالي الطلاب المسجلين", len(st.session_state.student_data))
    with col2:
        total_absent = len(st.session_state.student_data[st.session_state.student_data['الحالة'] == 'غائب'])
        st.metric("عدد الغائبين اليوم", total_absent)
    with col3:
        total_late = len(st.session_state.student_data[st.session_state.student_data['الحالة'] == 'متأخر'])
        st.metric("عدد المتأخرين اليوم", total_late)
    with col4:
        st.metric("قائمة المعلمين المعتمدين", len(st.session_state.teachers_data))

    st.markdown("---")
    st.subheader("📋 ملخص الكشوفات الحالية للجان")
    st.dataframe(st.session_state.student_data, use_container_width=True)

# ==============================================================================
# النافذة الثانية: 📂 إدارة ورفع البيانات
# ==============================================================================
elif page == "📂 إدارة ورفع البيانات":
    st.header("📂 إدارة وتحديث كشوفات الطلاب والمعلمين")
    st.markdown("تتيح لك هذه النافذة رفع ملفات الكشوفات الجديدة أو إضافة معلمين ولجان جديدة إلى النظام.")
    
    tab1, tab2 = st.tabs(["👥 كشوفات الطلاب واللجان", "👨‍🏫 تحديث قائمة المعلمين"])
    
    with tab1:
        st.subheader("رفع كشف اللجان والطلاب (Excel / CSV)")
        uploaded_file = st.file_uploader("اختر ملف كشف الطلاب واللجان:", type=["xlsx", "csv"])
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.xlsx'):
                    new_df = pd.read_excel(uploaded_file)
                else:
                    new_df = pd.read_csv(uploaded_file)
                
                # التأكد من مطابقة الحقول الأساسية للنظام
                required_cols = ['اللجنة', 'اسم الطالب', 'الشعبة', 'الحالة', 'المعلمون']
                for col in required_cols:
                    if col not in new_df.columns:
                        new_df[col] = "---" if col != 'الحالة' else 'حاضر'
                        
                st.session_state.student_data = new_df
                st.success("✨ تم تحديث بيانات الطلاب واللجان في النظام بنجاح من الملف المرفوع!")
                st.dataframe(st.session_state.student_data.head(), use_container_width=True)
            except Exception as e:
                st.error(f"حدث خطأ أثناء قراءة الملف: {e}")
                
    with tab2:
        st.subheader("قائمة المعلمين المعتمدين الحالية")
        st.write(pd.DataFrame(st.session_state.teachers_data))
        
        st.markdown("---")
        st.subheader("➕ إضافة معلم جديد للنظام")
        new_teacher_name = st.text_input("أدخل اسم المعلم رباعياً:")
        if st.button("اعتماد وإضافة المعلم"):
            if new_teacher_name.strip():
                st.session_state.teachers_data.append({'name_tech': new_teacher_name.strip()})
                st.success(f"تمت إضافة أ. {new_teacher_name} لقائمة التدقيق بنجاح.")
                st.rerun()
            else:
                st.warning("الرجاء كتابة اسم صحيح.")

# ==============================================================================
# النافذة الثالثة: 📝 رصد الحالات اليومية
# ==============================================================================
elif page == "📝 رصد الحالات اليومية":
    st.header("📝 رصد وتعديل حالات الطلاب اليومية")
    st.markdown("من هنا يمكنك تغيير حالة الطالب الفورية (حاضر / غائب / متأخر) وتحديثها مباشرة في قاعدة البيانات الحالية.")
    
    search_query = st.text_input("🔍 ابحث عن طالب بالاسم أو رقم اللجنة:")
    
    # تصفية جدول البحث
    df_search = st.session_state.student_data
    if search_query:
        df_search = df_search[
            df_search['اسم الطالب'].str.contains(search_query, na=False) | 
            df_search['اللجنة'].astype(str).str.contains(search_query, na=False)
        ]
        
    st.write(f"نتائج البحث: ({len(df_search)}) طالب.")
    
    # تعديل الحالة التفاعلي
    for index, row in df_search.iterrows():
        col_name, col_comm, col_status, col_btn = st.columns([4, 2, 3, 2])
        with col_name:
            st.write(row['اسم الطالب'])
        with col_comm:
            st.write(f"لجنة: {row['اللجنة']}")
        with col_status:
            status_options = ['حاضر', 'غائب', 'متأخر']
            current_idx = status_options.index(row['الحالة']) if row['الحالة'] in status_options else 0
            new_status = st.selectbox(f"الحالة لـ {row['اسم الطالب']}", status_options, index=current_idx, key=f"sel_{index}", label_visibility="collapsed")
        with col_btn:
            if st.button("حفظ التعديل", key=f"btn_{index}"):
                st.session_state.student_data.at[index, 'الحالة'] = new_status
                st.success("تم تحديث حالة الطالب!")
                st.rerun()

# ==============================================================================
# النافذة الرابعة: 🖨️ طباعة محاضر الغياب الرسمية
# ==============================================================================
elif page == "🖨️ طباعة محاضر الغياب الرسمية":
    st.header("🖨️ طباعة وتوليد محاضر غياب الاختبارات الرسمية")
    st.markdown("تقوم هذه النافذة بفرز وحصر الطلاب الغائبين وتوليد محضر غياب فردي رسمي لكل طالب يطابق النموذج المطلوب.")
    
    report_date = st.date_input("اختر تاريخ حصر الغياب وطباعة المحاضر:", datetime.now(), key="report_date_picker")
    
    # تصفية حاسمة ومستقرة: سحب الطلاب الغائبين فقط واستبعاد حالات التأخر تماماً
    df_all_students = st.session_state.student_data
    df_absence_only = df_all_students[df_all_students['الحالة'] == 'غائب']
    
    st.subheader("📋 معاينة كشف الطلاب الغائبين اليوم قبل الطباعة")
    st.dataframe(df_absence_only, use_container_width=True)
    
    if not df_absence_only.empty:
        try:
            # استدعاء دالة توليد محاضر الغياب الفردية بالـ PDF والتعديلات المستقرة
            pdf_bytes = export_attendance_to_pdf_fpdf(df_absence_only, report_date, valid_teachers_set)
            
            st.success(f"✨ تم بناء وتجهيز محاضر الغياب بنجاح لعدد ({len(df_absence_only)}) طالب غائب.")
            st.markdown("اضغط على الزر أدناه لتنزيل ملف الـ PDF الجاهز والمطابق للمحضر الرسمي:")
            
            # زر التحميل المباشر للمحضر بعد التحديث
            st.download_button(
                label="📥 تحميل وطباعة محاضر الغياب الفردية (PDF)",
                data=pdf_bytes,
                file_name=f"محاضر_غياب_مدرسة_القطيف_{report_date}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"⚠️ واجه النظام مشكلة أثناء معالجة وتوليد ملف الـ PDF: {e}")
    else:
        st.info("لا توجد أي حالات غياب مسجلة في هذا التاريخ، تأكد من رصد الحالات أولاً من نافذة 'رصد الحالات اليومية'.")
