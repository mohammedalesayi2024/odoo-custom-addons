/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/services/pos_store";

patch(PosStore.prototype, {

    filterChangeByTags(tagIds, currentOrderChange) {

        console.log("filterChangeByTags Loaded");

        const matchesTags = (change) => {
            const product = this.models["product.product"].get(change.product_id);

            const productTags = product.product_tag_ids || [];

            return productTags.some(tagId => tagIds.includes(tagId));
        };

        const filterChanges = (changes) => {

            const validComboUuids = new Set(
                changes
                    .filter(change => change.combo_parent_uuid && matchesTags(change))
                    .map(change => change.combo_parent_uuid)
            );

            return changes.filter(change =>
                (change.isCombo && validComboUuids.has(change.uuid)) ||
                (!change.isCombo && matchesTags(change))
            );

        };

        return {
            new: filterChanges(currentOrderChange.new),
            cancelled: filterChanges(currentOrderChange.cancelled),
            noteUpdate: filterChanges(currentOrderChange.noteUpdate),
        };

    },

});