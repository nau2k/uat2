# -*- coding: utf-8 -*-
from num2words import num2words
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.tools.misc import formatLang, format_date
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError


class TvanTemplate(models.Model):
    _name = 'wg.tvan.template'
    _description = 'Định dạng truyền nhận'
    _order = 'sequence'

    sequence = fields.Integer('sequence')
    name = fields.Char('Loại thông điệp', required=True)
    code = fields.Char('Quyết định')
    note = fields.Text('Diễn giải')
    parent_id = fields.Many2one('wg.tvan.template', 'Thuộc thông điệp')
    xml_data = fields.Text('XML template')