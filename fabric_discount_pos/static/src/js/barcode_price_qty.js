odoo.define('fabric_discount_pos.barcode_price_qty', function (require) {
    'use strict';

    const { PosGlobalState } = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');

    const CustomBarcode = (PosGlobalState) => class CustomBarcode extends PosGlobalState {

        async _barcodeProductAction(code) {
            // 👇 الباركود الخاص
            if (code.code.startsWith('21') && code.code.length >= 16) {
                try {
                    let barcode = code.code;

                    let product_code = barcode.substring(2, 7);
                    let qty = parseFloat(barcode.substring(7, 12)) / 100;
                    let price = parseFloat(barcode.substring(12, 16)) / 10;

                    let product = this.db.get_product_by_barcode(product_code);

                    if (product) {
                        let order = this.get_order();

                        let line = order.add_product(product, {
                            quantity: qty,
                            price: price,
                            merge: false,
                        });

                        if (line) {
                            line.set_unit_price(price); // 🔥 يجبر السعر
                        }

                        return;
                    }
                } catch (err) {
                    console.error('Barcode parse error:', err);
                }
            }

            return super._barcodeProductAction(code);
        }
    };

    Registries.Model.extend(PosGlobalState, CustomBarcode);
});