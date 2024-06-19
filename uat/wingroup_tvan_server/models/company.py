# -*- coding: utf-8 -*-
import json
import requests
from confluent_kafka import Consumer


from num2words import num2words
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.tools.misc import formatLang, format_date
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.model
    def get_tvan_conifg(self):
        tvan_config = self.env['wg.tvan.config'].search([], limit=1)
        if not tvan_config:
            raise ValidationError('Cấu hình Tvan chưa được thiết lập!')
        return tvan_config