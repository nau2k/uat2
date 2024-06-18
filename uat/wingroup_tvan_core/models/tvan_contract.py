# -*- coding: utf-8 -*-
from num2words import num2words
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.tools.misc import formatLang, format_date
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError


class HDDTContract(models.Model):
    _name = 'wg.hddt.contract'
    _description = 'Hợp đồng sử dụng Hóa đơn điện tử'

    order_id = fields.Many2one('sale.order', 'Đơn hàng')
    date = fields.Date('Ngày hợp đồng', required=True)
    name = fields.Char('Số hợp đồng', required=True)
    company_name = fields.Char('Bên A')
    company_is_sign = fields.Boolean('Bên A đã ký')
    partner_name = fields.Char('Bên B')
    partner_is_sign = fields.Boolean('Bên B đã ký')


    @api.model
    def create(self, vals):
        res = super(HDDTContract, self).create(vals)
        if 'order_id' in vals:
            res.order_id.write({
                'inv_contract_id': res.id,
            })
        return res    