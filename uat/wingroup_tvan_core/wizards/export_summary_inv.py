# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError

import xlrd
import base64
import pandas as pd
import re

class ExportSummaryInvoice(models.TransientModel):
    _name = 'wg.export.summary.inv.wiz'
    _description = 'Bảng kê hóa đơn, chứng từ hàng hóa, dịch vụ bán ra'


    date_from = fields.Date('Từ ngày', required=True)
    date_to = fields.Date('Đến ngày', required=True)


    def confirm(self):
        pass