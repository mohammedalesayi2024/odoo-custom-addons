/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/services/pos_store";

patch(PosStore.prototype, {

    filterChangeByTags(tagIds, currentOrderChange) {
        console.log("POS Printer Tags", tagIds);

        return {
            new: [],
            cancelled: [],
            noteUpdate: [],
        };
    },

});