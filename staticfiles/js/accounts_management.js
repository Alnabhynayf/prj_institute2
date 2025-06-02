/**
 * ملف إدارة حسابات الموظفين - المعهد العالي للقضاء
 * يعالج عمليات إضافة/تعديل/حذف الموظفين باستخدام AJAX
 */

document.addEventListener('DOMContentLoaded', function() {
    // =============================================
    // تهيئة المتغيرات والعناصر الأساسية
    // =============================================
    const DOM = {
        formContainer: document.getElementById('employee-form-container'),
        form: document.getElementById('employee-form'),
        addBtn: document.getElementById('add-employee-btn'),
        closeBtn: document.getElementById('close-form-btn'),
        cancelBtn: document.getElementById('cancel-form-btn'),
        formTitle: document.getElementById('form-title'),
        deleteModal: document.getElementById('delete-modal'),
        cancelDeleteBtn: document.getElementById('cancel-delete-btn'),
        confirmDeleteBtn: document.getElementById('confirm-delete-btn'),
        searchInput: document.getElementById('search-input'),
        employeesTable: document.getElementById('employees-table')
    };

    let currentEmployeeId = null;
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    // =============================================
    // وظائف إدارة النماذج
    // =============================================

    /**
     * فتح نموذج إضافة موظف جديد
     */
    function openAddForm() {
        resetForm();
        DOM.formContainer.classList.remove('hidden');
        DOM.formTitle.textContent = 'إضافة موظف جديد';
        DOM.cancelBtn.classList.add('hidden');
        
        // جعل حقول كلمة المرور مطلوبة للإضافة
        document.getElementById('id_password1').required = true;
        document.getElementById('id_password2').required = true;
        document.getElementById('id_password1').placeholder = '';
        document.getElementById('id_password2').placeholder = '';
    }

    /**
     * فتح نموذج تعديل موظف
     * @param {string} employeeId - معرّف الموظف
     */
    function openEditForm(employeeId) {
        fetchEmployeeData(employeeId)
            .then(data => {
                populateForm(data);
                DOM.formTitle.textContent = 'تعديل بيانات الموظف';
                DOM.cancelBtn.classList.remove('hidden');
                DOM.formContainer.classList.remove('hidden');
            })
            .catch(error => {
                showToast('فشل في جلب بيانات الموظف', 'error');
                console.error('Fetch error:', error);
            });
    }

    /**
     * جلب بيانات الموظف من الخادم
     * @param {string} employeeId 
     * @returns {Promise} وعد ببيانات الموظف
     */
    function fetchEmployeeData(employeeId) {
        return fetch(`/manage_accounts/get_employee_data/${employeeId}/`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        });
    }

    /**
     * تعبئة النموذج ببيانات الموظف
     * @param {object} data - بيانات الموظف
     */
    function populateForm(data) {
        document.getElementById('employee-id').value = data.id || data.user_id;
        document.getElementById('id_username').value = data.username;
        document.getElementById('id_name').value = data.name;
        document.getElementById('id_phone').value = data.phone;
        document.getElementById('id_role').value = data.role;
        document.getElementById('id_email').value = data.email;
        
        // جعل كلمة المرور غير مطلوبة للتعديل
        document.getElementById('id_password1').required = false;
        document.getElementById('id_password2').required = false;
        document.getElementById('id_password1').placeholder = 'اتركه فارغاً للحفاظ على كلمة المرور الحالية';
        document.getElementById('id_password2').placeholder = 'اتركه فارغاً للحفاظ على كلمة المرور الحالية';
    }

    /**
     * إغلاق النموذج وإعادة تعيينه
     */
    function closeForm() {
        DOM.formContainer.classList.add('hidden');
        resetForm();
    }

    /**
     * إعادة تعيين النموذج
     */
    function resetForm() {
        if (DOM.form) DOM.form.reset();
        document.getElementById('employee-id').value = '';
        clearErrors();
    }

    // =============================================
    // إدارة الأخطاء والتحقق
    // =============================================

    /**
     * مسح جميع أخطاء النموذج
     */
    function clearErrors() {
        document.querySelectorAll('.error-message').forEach(el => {
            el.textContent = '';
        });
        document.querySelectorAll('.border-red-500').forEach(el => {
            el.classList.remove('border-red-500');
        });
    }

    /**
     * عرض أخطاء النموذج
     * @param {object} errors - كائن يحتوي على الأخطاء
     */
    function displayFormErrors(errors) {
        clearErrors();
        
        for (const field in errors) {
            const errorMessages = errors[field].map(error => error.message).join(' ');
            const errorElement = document.getElementById(`${field}-error`);
            const inputElement = document.getElementById(`id_${field}`);
            
            if (errorElement && inputElement) {
                errorElement.textContent = errorMessages;
                inputElement.classList.add('border-red-500');
            }
        }
    }

    // =============================================
    // إدارة عمليات الحذف
    // =============================================

    /**
     * فتح نافذة تأكيد الحذف
     * @param {string} employeeId - معرّف الموظف
     */
    function openDeleteModal(employeeId) {
        currentEmployeeId = employeeId;
        DOM.deleteModal.classList.remove('hidden');
    }

    /**
     * تأكيد حذف الموظف
     */
    function confirmDelete() {
        if (!currentEmployeeId) return;

        fetch(window.location.href, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: `employee_id=${currentEmployeeId}&delete_employee=true&csrfmiddlewaretoken=${csrfToken}`
        })
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            if (data.success) {
                removeEmployeeRow(currentEmployeeId);
                showToast('تم حذف الموظف بنجاح', 'success');
            } else {
                showToast(data.error || 'حدث خطأ أثناء الحذف', 'error');
            }
            closeDeleteModal();
        })
        .catch(error => {
            showToast('حدث خطأ في الاتصال بالخادم', 'error');
            console.error('Delete error:', error);
            closeDeleteModal();
        });
    }

    /**
     * إزالة صف الموظف من الجدول
     * @param {string} employeeId 
     */
    function removeEmployeeRow(employeeId) {
        const row = document.getElementById(`employee-${employeeId}`);
        if (row) row.remove();
    }

    /**
     * إغلاق نافذة تأكيد الحذف
     */
    function closeDeleteModal() {
        DOM.deleteModal.classList.add('hidden');
        currentEmployeeId = null;
    }

    // =============================================
    // إدارة إرسال النموذج
    // =============================================

    /**
     * معالجة إرسال النموذج
     * @param {Event} e - حدث الإرسال
     */
    function handleFormSubmit(e) {
        e.preventDefault();
        
        const formData = new FormData(DOM.form);
        const employeeId = document.getElementById('employee-id').value;
        const isEdit = !!employeeId;

        fetch(window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            if (data.success) {
                updateEmployeesTable(data.employees_html);
                closeForm();
                showToast(
                    isEdit ? 'تم تحديث بيانات الموظف بنجاح' : 'تم إضافة الموظف بنجاح', 
                    'success'
                );
            } else {
                displayFormErrors(data.errors);
            }
        })
        .catch(error => {
            showToast('حدث خطأ في الاتصال بالخادم', 'error');
            console.error('Submit error:', error);
        });
    }

    /**
     * تحديث جدول الموظفين
     * @param {string} html - كود HTML الجديد للجدول
     */
    function updateEmployeesTable(html) {
        if (DOM.employeesTable) {
            DOM.employeesTable.innerHTML = html;
        }
    }

    // =============================================
    // وظائف البحث والمساعدات
    // =============================================

    /**
     * البحث عن الموظفين
     */
    function searchEmployees() {
        const term = DOM.searchInput.value.toLowerCase();
        const rows = DOM.employeesTable.querySelectorAll('tr');
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(term) ? '' : 'none';
        });
    }

    /**
     * عرض رسالة تنبيه
     * @param {string} message - نص الرسالة
     * @param {string} type - نوع الرسالة (success/error)
     */
    function showToast(message, type) {
        const toast = document.createElement('div');
        toast.className = `fixed bottom-4 right-4 px-4 py-2 rounded-lg text-white flex items-center ${
            type === 'success' ? 'bg-green-500' : 'bg-red-500'
        } shadow-lg z-50`;
        
        const iconName = type === 'success' ? 'check-circle' : 'alert-circle';
        toast.innerHTML = `
            <i data-lucide="${iconName}" class="w-5 h-5 ml-2"></i>
            <span>${message}</span>
        `;
        
        document.body.appendChild(toast);
        lucide.createIcons();
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    // =============================================
    // ربط الأحداث
    // =============================================

    // أحداث النماذج
    if (DOM.addBtn) DOM.addBtn.addEventListener('click', openAddForm);
    if (DOM.closeBtn) DOM.closeBtn.addEventListener('click', closeForm);
    if (DOM.cancelBtn) DOM.cancelBtn.addEventListener('click', closeForm);
    if (DOM.form) DOM.form.addEventListener('submit', handleFormSubmit);

    // أحداث الحذف
    if (DOM.cancelDeleteBtn) DOM.cancelDeleteBtn.addEventListener('click', closeDeleteModal);
    if (DOM.confirmDeleteBtn) DOM.confirmDeleteBtn.addEventListener('click', confirmDelete);

    // أحداث البحث
    if (DOM.searchInput) DOM.searchInput.addEventListener('input', searchEmployees);

    // أحداث العناصر الديناميكية (التعديل والحذف)
    document.addEventListener('click', function(e) {
        // زر التعديل
        if (e.target.closest('.edit-employee')) {
            const employeeId = e.target.closest('.edit-employee').dataset.id;
            openEditForm(employeeId);
        }
        
        // زر الحذف
        if (e.target.closest('.delete-employee')) {
            const employeeId = e.target.closest('.delete-employee').dataset.id;
            openDeleteModal(employeeId);
        }
    });

    // تهيئة الأيقونات
    lucide.createIcons();
});