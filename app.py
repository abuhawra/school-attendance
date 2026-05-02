# --- إدارة بيانات المعلمين ---
st.subheader("👨‍🏫 إدارة بيانات المعلمين")

# عرض خيارات النسخ الاحتياطي أولاً
res_t = supabase.table('teachers').select("*").execute()
if res_t.data:
    df_t = pd.DataFrame(res_t.data)
    col3, col4 = st.columns(2)
    with col3: 
        st.download_button("📥 نسخة معلمين CSV", df_t.to_csv(index=False).encode('utf-8-sig'), "teachers_backup.csv", use_container_width=True)
    with col4:
        out_t = io.BytesIO()
        with pd.ExcelWriter(out_t, engine='openpyxl') as wr: df_t.to_excel(wr, index=False)
        st.download_button("📊 نسخة معلمين Excel", out_t.getvalue(), "teachers_backup.xlsx", use_container_width=True)

# أداة رفع الملف الجديد للتحديث
up_t = st.file_uploader("تحديث قائمة المعلمين:", key="up_t")
if up_t and st.button("🔄 استرجاع وتحديث المعلمين"):
    # قراءة الملف المرفوع
    df_nt = pd.read_csv(up_t) if up_t.name.endswith('.csv') else pd.read_excel(up_t)
    
    # 1. حذف البيانات القديمة
    supabase.table('teachers').delete().neq('name_tech', '0').execute()
    
    # 2. إدخال البيانات الجديدة
    supabase.table('teachers').insert(df_nt.to_dict('records')).execute()
    st.success("تم تحديث بيانات المعلمين بنجاح!")
