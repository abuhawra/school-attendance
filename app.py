import streamlit as st
import pandas as pd
from fpdf import FPDF
import arabic_reshaper
from bidi.algorithm import get_display
from datetime import datetime

# ==============================================================================
# 1. إعدادات الصفحة الرئيسية لنظام أثر
# ==============================================================================
st.set_page_config(page_title="نظام أثر الإداري - مدرسة القطيف الثانوية", layout="wide")

# ==============================================================================
# 2. دالة معالجة الخطوط والنصوص العربية (معالجة المحاذاة والقلب)
# ==============================================================================
def format_ar(text):
    if not text:
        return ""
    reshaped_text = arabic_reshaper.reshape(str(text))
    return get_display(reshaped_text)

# ==============================================================================
# 3. دالة التحقق من أسماء الملاحظين والمراقبين وتصفيتها
# ==============================================================================
def get_clean_observer_string(teacher_name, valid_teachers_set):
    name_str = str(teacher_name).strip()
    if name_str in valid_teachers_set:
        return name_str
    # إذا كان الاسم مركب أو يحتوي على فواصل، نأخذ الاسم الأول المتوفر كمثال أو نتركها فارغة للكتابة اليدوية
    if "|" in name_str:
        first_name = name_str.split("|")[0].strip()
        if first_name in valid_teachers_set:
            return first_name
    return "..........................................."

# ==============================================================================
# 4. دالة توليد "محضر غياب" الفردي الرسمي (بالتنسيق والمربعات الجديدة)
# ==============================================================================
def export_attendance_to_pdf_fpdf(df, report_date, valid_teachers_set):
    days_ar = {
        "Monday": "الإثنين", "Tuesday": "الثلاثاء", "Wednesday": "الأربعاء", 
        "Thursday": "الخميس", "Friday": "الجمعة", "Saturday": "السبت", "Sunday": "الأحد"
    }
    day_name_en = report_date.strftime('%A')
    day_name_ar = days_ar.get(day_name_en, day_name_en)
    date_str = report_date.strftime('%Y-%m-%d')
    
    # إنشاء كائن الـ PDF بمقاس A4 القياسي
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # الاعتماد المباشر على ملف الخط المرفوع في مجلد مشروعك (arial.ttf) لاستقرار السيرفر
    pdf.add_font("CustomArial", "", "arial.ttf")
    pdf.set_font("CustomArial", size=12)
    
    # توليد محضر مستقل في صفحة منفصلة لكل طالب غائب
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
        
        # --- العنوان العريض للمحضر المحدث بدلاً من محضر تأخر ---
        pdf.set_draw_color(0, 0, 0)
        pdf.set_line_width(0.5)
        pdf.rect(15, 63, 180, 12)
        pdf.set_xy(15, 66)
        pdf.set_font("CustomArial", style="", size=13)
        pdf.cell(180, 6, format_ar("محضر ( غـيـاب ) طالب في اختبارات نهاية الفصل الدراسي"), align="C", ln=True)
        
        # --- خانة اليوم والتاريخ المنفصلة التعبوية ---
        # التاريخ
        pdf.set_xy(80, 80)
        pdf.set_fill_color(220, 220, 220) 
        pdf.cell(30, 10, format_ar("التاريخ"), border=1, align="C", fill=True)
        pdf.cell(85, 10, format_ar(f"      /      /  ١٤٤٧ هـ  ({date_str})"), border=1, align="C")
        # اليوم
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
        
        # مربعات الاختيار التفاعلية داخل الجدول للفترات والفصول
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
        
        # حيز التوقيعات الصريح والخطوط
        pdf.set_xy(15, 228)
        pdf.cell(90, 6, format_ar("التوقيع: ..................................."), align="C")
        pdf.cell(90, 6, format_ar("التوقيع: ..................................."), align="C")

    return bytes(pdf.output())

# ==============================================================================
# 5. واجهة لوحة تحكم التطبيق الأساسية (Streamlit Interface)
# ==============================================================================
st.title("📊 نظام أثر الإداري - كشوفات ومحاضر الغياب")
st.markdown("---")

# اختيار تاريخ التقرير لطباعته آلياً في المحاضر
report_date = st.date_input("اختر تاريخ حصر الغياب للاختبارات:", datetime.now())

# ==============================================================================
# 6. إعداد وتصفية قائمة المعلمين (تم إصلاح قوس سطر 548 المفتوح سابقاً بشكل نهائي ومستقر)
# ==============================================================================
if 'teachers_data' not in st.session_state:
    st.session_state.teachers_data = [
        {'name_tech': 'عارف احمد'}, 
        {'name_tech': 'جعفر بن علي بن حسين آل ربح'}, 
        {'name_tech': 'سعيد بن حسن بن صالح المغرور'}
    ]

# تم إغلاق القوس البرمجي بنجاح وربطه بـ Session State لضمان عدم حدوث SyntaxError
valid_teachers_set = {str(t['name_tech']).strip() for t in st.session_state.teachers_data}

# ==============================================================================
# 7. جلب واستيراد بيانات الطلاب (محاكاة للجدول وتصفية الغياب فقط بدون التأخير)
# ==============================================================================
if 'student_data' not in st.session_state:
    st.session_state.student_data = pd.DataFrame({
        'اللجنة': ['1', '1', '1', '3', '2'],
        'اسم الطالب': [
            'رضا بن علي بن أحمد الناصر', 
            'حيدر بن محمد بن سعيد اغريب', 
            'حسين بن هاني بن سعود آل درويش', 
            'أحمد بن فراس بن علي آل ربيع',
            'طالب متأخر تجريبي'
        ],
        'الشعبة': ['201', '201', '201', '202', '205'],
        'الحالة': ['غائب', 'غائب', 'غائب', 'غائب', 'متأخر'],
        'المعلمون': [
            'عارف احمد | جعفر بن علي بن حسين آل ربح', 
            'عارف احمد | جعفر بن علي بن حسين آل ربح', 
            'عارف احمد | جعفر بن علي بن حسين آل ربح', 
            'فراس بن عبدالله حسن آل عبدالمحسن',
            'معلم مراقب آخر'
        ]
    })

df_all = st.session_state.student_data

# تصفية حاسمة: جلب الغياب فقط وبدون التأخير تماماً بناءً على طلبك
df_absence_only = df_all[df_all['الحالة'] == 'غائب']

# عرض جدول الحالات الفوري داخل واجهة التطبيق
st.subheader("📋 قائمة الطلاب الغائبين المسجلين حالياً (بدون المتأخرين)")
st.dataframe(df_absence_only, use_container_width=True)

# ==============================================================================
# 8. قسم توليد وطباعة المحاضر الرسمية بصيغة PDF
# ==============================================================================
if not df_absence_only.empty:
    try:
        # استدعاء دالة توليد المحاضر المحدثة
        pdf_bytes = export_attendance_to_pdf_fpdf(df_absence_only, report_date, valid_teachers_set)
        
        st.success(f"✨ تم تجهيز محاضر الغياب الفردية بنجاح لعدد ({len(df_absence_only)}) طلاب غائبين.")
        
        # زر التنزيل المباشر والتفاعلي للمحضر المحدث
        st.download_button(
            label="📥 تحميل وطباعة محاضر الغياب الرسمية (PDF)",
            data=pdf_bytes,
            file_name=f"محاضر_غياب_الاختبارات_{report_date}.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"⚠️ واجه النظام مشكلة أثناء معالجة ملف الـ PDF: {e}")
else:
    st.info("لا توجد أي حالات غياب مسجلة في هذا التاريخ حتى الآن.")
