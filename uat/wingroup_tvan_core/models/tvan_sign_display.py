# -*- coding: utf-8 -*-
from num2words import num2words
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.tools.misc import formatLang, format_date
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError


class HDDTDateDisplay(models.Model):
    _name = 'wg.hddt.display'
    _description = 'Cấu hình hiển thị ngày ký'    
    _order = 'sequence'

    sequence = fields.Integer('Sequence')
    code = fields.Char('Quy cách')
    name = fields.Char('Định dạng')
    image = fields.Binary('Hiển thị')
    default = fields.Boolean('Mặc định')

    image_no_date = fields.Binary('Ảnh không hình')