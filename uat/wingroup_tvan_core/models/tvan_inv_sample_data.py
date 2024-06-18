# -*- coding: utf-8 -*-
from num2words import num2words
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.tools.misc import formatLang, format_date
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError


class InvoiceSampleData(models.Model):
    _name = 'wg.inv.sample.data'
    _description = 'Mẫu dữ liệu hóa đơn'
    _order = 'sequence'

    sequence = fields.Integer('Sequence')
    name = fields.Char('Tên', required=True)
    note = fields.Char('Ghi chú')
    data = fields.Text('Json data', default=str({}))
