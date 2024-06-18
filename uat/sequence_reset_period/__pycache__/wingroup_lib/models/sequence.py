# -*- coding: utf-8 -*-
import base64
import uuid
import json
import ast
from xml.dom import minidom
import xmltodict
from requests.structures import CaseInsensitiveDict
import requests

from num2words import num2words
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.tools.misc import formatLang, format_date
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError


class IrSequence(models.Model):
    _inherit = 'ir.sequence'


    max_number = fields.Integer('Số tối đa')

    # def _next(self, sequence_date=None):
    #     if self.max_number and self._get_current_sequence(sequence_date=sequence_date) > self.max_number:
    #         raise ValidationError('Đã sử dụng hết số lượng hóa đơn')
    #     return super(IrSequence, self)._next(sequence_date)