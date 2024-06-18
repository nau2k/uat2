# -*- coding: utf-8 -*-
from odoo import api, fields, models
import secrets


class ResPartner(models.Model):
    _inherit = 'res.partner'

    api_rest_key = fields.Char()


class ResUsers(models.Model):
    _inherit = 'res.users'

    def generate_api_rest_key(self):
        self.ensure_one()
        if self.api_rest_key:
            return
        while True:
            api_rest_key = secrets.token_urlsafe(40)
            if not self.sudo().search([('api_rest_key', '=', api_rest_key)]):
                self.sudo().write({'api_rest_key': api_rest_key})
                return

    @api.model
    def get_api_rest_user(self, api_rest_key):
        return self.sudo().search([('api_rest_key', '=', api_rest_key)], limit=1)
