# --- 1. واجهة المعلم (نسخة مصححة لظهور اللجان) ---
if page == "🔑 دخول المعلم":
    is_open = get_system_status()
    if not is_open:
        st.error("🚫 نظام رصد الغياب مغلق حالياً من قبل الإدارة.")
    else:
        if not st.session_state.get('logged_in', False):
            st.header("🔑 تسجيل دخول المعلم")
            nid_input = st.text_input("أدخل رقم السجل المدني:", key="login_id")
            if st.button("دخول"):
                res = supabase.table("teachers").select("*").eq("national_id", nid_input.strip()).execute()
                if res.data:
                    st.session_state.logged_in = True
                    st.session_state.teacher_name = res.data[0].get('name_tech', 'المعلم')
                    st.success(f"✅ مرحباً {st.session_state.teacher_name}")
                    time.sleep(0.5)
                    st.rerun() # تحديث الصفحة لضمان ظهور القوائم
                else:
                    st.error("❌ رقم السجل المدني غير مسجل في النظام.")
        else:
            # تم الدخول بنجاح - عرض قوائم الرصد
            st.success(f"✅ مرحباً أستاذ: **{st.session_state.teacher_name}**")
            
            # زر تسجيل الخروج للتبديل بين المعلمين
            if st.button("🔄 تسجيل خروج / تبديل المعلم"):
                st.session_state.logged_in = False
                st.rerun()

            st.divider()
            target_date = st.date_input("📅 تاريخ الرصد اليوم", datetime.now())
            
            # جلب اللجان
            try:
                s_data = supabase.table('students').select("committee").execute()
                all_committees = sorted(list(set([str(i['committee']) for i in s_data.data if i['committee']])), key=smart_sort)
                
                selected_committee = st.selectbox("🎯 اختر لجنتك للبدء بالرصد:", ["--- اختر اللجنة ---"] + all_committees)
                
                if selected_committee != "--- اختر اللجنة ---":
                    # عرض كشف الطلاب هنا...
                    st.write(f"📂 عرض طلاب لجنة رقم: {selected_committee}")
                    # (بقية كود عرض الأسماء...)
            except Exception as e:
                st.error("حدث خطأ أثناء جلب اللجان. تأكد من اتصال قاعدة البيانات.")
