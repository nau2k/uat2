# -*- coding: utf-8 -*-
from num2words import num2words
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.tools.misc import formatLang, format_date
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    hddt_ok = fields.Boolean('Gói HĐĐT')
    hddt_qty = fields.Integer('Số lượng')
    uom_name2 = fields.Char('Đơn vị tính')
    
    @api.onchange('uom_id')
    def wg_onchange_uom_id(self):
        if self.uom_id:
            self.uom_name2 = self.uom_id.name
