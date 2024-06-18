# -*- coding: utf-8 -*-
from num2words import num2words
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.tools.misc import formatLang, format_date
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    name = fields.Char('Tên khách hàng')
    vat = fields.Char('Mã số thuế')
    ref = fields.Char('Mã khách hàng')
    phone = fields.Char('Số điện thoại')
    
    # New fields
    buyer_name = fields.Char('Tên người mua')
    acc_bank_number = fields.Char('Số tài khoản')
    acc_bank_name = fields.Char('Tên ngân hàng')
    email_cc = fields.Char('Email CC')
    
    def name_get(self):
        if not self._context.get('only_show_ref'):
            return super(ResPartner, self).name_get()
        return [(r.id, r.ref or 'Chưa thiếp lập') for r in self]

    field_boolean_find_partner = fields.Boolean('Lấy thông tin')

    @api.onchange('field_boolean_find_partner')
    def onchange_field_boolean_find_partner(self):
        if not self.vat:
            return
        try:
            headers = CaseInsensitiveDict()
            route_url = self.env['ir.config_parameter'].sudo().get_param('company_info.main_url')
            token = self.env['ir.config_parameter'].sudo().get_param('company_info.client_key')
            headers['Accept'] = '*/*'
            headers['Authorization'] = 'Bearer ' + token
            headers['Accept-Encoding'] = 'gzip, deflate, br'
            headers['Connection'] = 'keep-alive'   
            data = {
                'mst': self.vat,
            } 
            result = requests.post(route_url, json=data, headers=headers)
            data = json.loads(result.text)
            company_info = dict(data.get('result').get('data'))
            print (company_info, company_info.get('name'), type(company_info.get('name')))
            if company_info:
                self.name = company_info.get('name')
                self.address2 = company_info.get('address')
        except Exception as e:
            pass


    # def wg_view_company_info(self):
    #     action = self.env["ir.actions.actions"]._for_xml_id('wingroup_tvan_core.action_res_partner')
    #     action['views'] = [(False, 'form')]
    #     action['res_id'] = self.env.user.company_id.id
    #     return action 

