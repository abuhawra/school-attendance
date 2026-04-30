# --- داخل لوحة الإدارة - تبويب التقارير ---
with tab1:
    d = st.date_input("اختر التاريخ", datetime.now())
    res = supabase.table("attendance").select("*").eq("date", str(d)).execute()
    
    if res.data:
        df = pd.DataFrame(res.data)
        # تصفية الطلاب غير الحاضرين فقط
        df_view = df[df['status'].isin(['غائب', 'متأخر'])]
        
        if not df_view.empty:
            st.dataframe(df_view[['student_name', 'status', 'committee']], use_container_width=True)
            
            st.subheader("إرسال التقارير التفصيلية 📲")
            for _, row in df_view.iterrows():
                # تجهيز نص الرسالة مع الصور (الإيموجي) والتنسيق العريض
                # ملاحظة: تم استخدام %0A لعمل سطر جديد في الواتساب
                
                name_student = row['student_name']
                status_student = row['status']
                committee_student = row['committee']
                # إذا كانت الشعبة غير موجودة في قاعدة بيانات الغياب، سنحاول جلبها من جدول الطلاب
                class_student = row.get('class_name', 'غير محدد') 

                whatsapp_msg = (
                    f"🗓️ *التاريخ:* {d}%0A%0A"
                    f"👤 *الاسم:* {name_student}%0A"
                    f"🏫 *الشعبة:* {class_student}%0A"
                    f"📦 *اللجنة:* {committee_student}%0A"
                    f"⚠️ *الحالة:* *{status_student}*%0A%0A"
                    f"نتمنى منكم المتابعة.. مدرسة القطيف الثانوية"
                )
                
                # الرابط يدعم الواتساب العادي والاعمال تلقائياً
                link = f"https://wa.me/?text={whatsapp_msg}"
                
                # عرض الزر بشكل احترافي
                st.markdown(f"""
                <a href="{link}" target="_blank" style="text-decoration: none;">
                    <div style="background-color: #25D366; color: white; padding: 10px; border-radius: 10px; text-align: center; margin-bottom: 10px; font-weight: bold;">
                        إرسال تقرير: {name_student} 📲
                    </div>
                </a>
                """, unsafe_allow_html=True)
        else:
            st.success("ما شاء الله، لا يوجد غياب أو تأخر في هذا التاريخ.")
