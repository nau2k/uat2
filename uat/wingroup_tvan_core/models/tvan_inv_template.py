# -*- coding: utf-8 -*-
from num2words import num2words
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.tools.misc import formatLang, format_date
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError


class InvoiceTemplate(models.Model):
    _name = 'wg.invoice.template'
    _description = 'Mẫu Hóa đơn điện tử'
    _order = 'sequence'

    sequence = fields.Integer('sequence')
    name = fields.Char('Tên mẫu', required=True)
    note = fields.Text('Diễn giải')
    data_file = fields.Binary('File mẫu', required=True)
    filename = fields.Char('Tên file mẫu')

    preview_data = fields.Binary('Xem trước')