/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

// ✅ نحفظ الدالة الأصلية
const originalDuplicate = FormController.prototype.duplicateRecord;

patch(FormController.prototype, {
    async duplicateRecord() {
        return new Promise((resolve) => {
            this.dialogService.add(ConfirmationDialog, {
                title: "تأكيد",
                body: "هل تريد عمل نسخة؟",
                confirm: () => {
                    // ✅ استدعاء الدالة الأصلية بشكل صحيح
                    originalDuplicate.call(this);
                    resolve(true);
                },
                cancel: () => {
                    resolve(false);
                },
            });
        });
    },
});