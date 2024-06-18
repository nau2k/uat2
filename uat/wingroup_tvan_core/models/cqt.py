# -*- coding: utf-8 -*-
from num2words import num2words
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.tools.misc import formatLang, format_date
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError


class CQT(models.Model):
    _name = 'wg.cqt'
    _description = 'Cơ quan thuế'
    _order = 'sequence'

    sequence = fields.Integer('sequence')
    name = fields.Char('Tên CQT', required=True)
    code = fields.Char('Mã CQT', required=True)
    city_id = fields.Many2one('res.country.state', 'Tỉnh/Thành phố')

    def name_get(self):
        return [(r.id, '{} - {}'.format(r.code, r.name)) for r in self]