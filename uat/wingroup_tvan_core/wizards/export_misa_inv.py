# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError

import xlrd
import base64
import pandas as pd
import re

class ExportMisaInvoice(models.TransientModel):
    _name = 'wg.export.misa.inv.wiz'
    _description = 'Xuất dữ liệu vào phần mềm Misa'


    date_from = fields.Date('Từ ngày', required=True)
    date_to = fields.Date('Đến ngày', required=True)


    def confirm(self):
        pass