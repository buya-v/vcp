/** @odoo-module **/

import { Component } from "@odoo/owl";

export class MembershipForm extends Component {
    static template = "vcp.MembershipForm";

    async submitForm(ev) {
        ev.preventDefault();
        const formData = new FormData(ev.target);
        const response = await this.env.services.rpc({
            route: "/membership/request",
            params: Object.fromEntries(formData),
        });
        if (response.success) {
            alert("Membership request submitted successfully!");
        } else {
            alert("Failed to submit membership request.");
        }
    }
}