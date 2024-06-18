# -*- coding: utf-8 -*-
from num2words import num2words
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.tools.misc import formatLang, format_date
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError


class InvoiceSequence(models.Model):
    _name = 'wg.inv.sequence'
    _description = 'Thông báo phát hành/Dãy số hóa đơn'

    order_id = fields.Many2one('sale.order', 'Đơn hàng')
    company_name = fields.Char('Tên đơn vị')
    company_vat = fields.Char('Mã số thuế')
    company_address = fields.Char('Địa chỉ đơn vị')
    cqt_name = fields.Char('Tên cơ quan thuế chấp nhận thông báo')
    name = fields.Char('Mẫu số', size=6)
    serial = fields.Char('Ký hiệu', size=6)
    quantity = fields.Integer('Số lượng', default=300)
    from_qty = fields.Integer('Từ số', default=1) 
    to_qty = fields.Integer('Đến số', default=300) 
    date = fields.Date('Ngày bắt đầu sử dụng')
    company_id = fields.Many2one('res.company', string='Công ty', default=lambda self: self.env.company)


    @api.onchange('from_qty')
    def onchange_from_qty(self):
        self.to_qty = self.from_qty + self.quantity - 1


    @api.model
    def create(self, vals):
        res = super(InvoiceSequence, self).create(vals)
        if 'order_id' in vals:
            res.order_id.write({
                'inv_sequence_id': res.id,
            })
        return res        