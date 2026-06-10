/** @odoo-module **/

import { registry } from "@web/core/registry";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { PosComponent } from "@point_of_sale/app/components/pos_component/pos_component";

class FabricDiscountButton extends PosComponent {
    async onClick() {

        const order = this.env.pos.get_order();
        if (!order) return;

        const discount_product = this.env.pos.db.get_product_by_id(4);
        if (!discount_product) {
            alert("منتج الخصم غير موجود");
            return;
        }

        let total_discount = 0;

        for (const line of order.get_orderlines()) {

            if (line.product.id === discount_product.id) continue;

            const qty = line.get_quantity();
            const price = line.get_unit_price();

            const total_cm = qty * 100;
            const free_cm = total_cm % 100;

            if (free_cm > 0) {
                total_discount += (free_cm / 100) * price;
            }
        }

        if (total_discount > 0) {
            order.add_product(discount_product, {
                quantity: 1,
                price: -total_discount,
            });
        }
    }
}

// ⚠️ مهم: الاسم لازم يطابق XML
FabricDiscountButton.template = "fabric_discount_pos.FabricDiscountButton";

// تسجيل الزر
ProductScreen.addControlButton({
    component: FabricDiscountButton,
    position: ["after", "SetDiscountButton"],
});