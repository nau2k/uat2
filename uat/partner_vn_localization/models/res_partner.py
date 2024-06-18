# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class ResPartnerVnLocalization(models.Model):
    _inherit = "res.partner"

    def _default_country_id(self):
        country_id = self.env['res.country'].search([('name', 'ilike', 'Việt Nam')], limit=1)
        return country_id.id if country_id else False

    country_id = fields.Many2one('res.country', default=_default_country_id, string='Country', ondelete='restrict')
    ward_id = fields.Many2one('res.country.ward', string=_('Ward'))
    district_id = fields.Many2one('res.country.district', string=_('District'))
    short_name = fields.Char(string='Tên viết tắt')
    address2 = fields.Char(string=_('Address'), compute='_compute_address2', store=True, compute_sudo=True, readonly=False)

    @api.depends('district_id', 'ward_id', 'street', 'street2', 'state_id', 'country_id')
    def _compute_address2(self):
        for record in self:
            district_name = record.district_id.name if record.district_id else ''
            ward_name = record.ward_id.name if record.ward_id else ''
            state_name = record.state_id.name if record.state_id else ''
            address = ''
            if record.street:
                address += ' ' + record.street
            if record.street2:
                address += ', ' + record.street2
            if ward_name:
                address += ', ' + ward_name
            if district_name:
                address += ', ' + district_name
            if state_name:
                address += ', ' + state_name
            if record.country_id:
                address += ' ' + record.country_id.name
            record.address2 = address

    @api.onchange('state_id')
    def _state_id_onchange(self):
        self.district_id = False
        self.ward_id = False
        self.city = self.state_id.name

    def _display_address(self, without_company=False):
        # Overwire for ....
        full_address = ''
        if self.address2:
            full_address += self.address2
        if self.commercial_company_name and not without_company:
            full_address = self.commercial_company_name + ' ' + full_address
        if self.mobile or self.phone:
            space = '-' if self.mobile and self.phone else ''
            mobile = self.mobile if self.mobile else ''
            phone = self.phone if self.phone else ''
            contact = ' ( %s %s %s ) ' % (mobile, space, phone)
            full_address += contact
        return full_address
