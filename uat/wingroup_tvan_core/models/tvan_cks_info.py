# -*- coding: utf-8 -*-
from num2words import num2words
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.tools.misc import formatLang, format_date
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError


class CSKInfo(models.Model):
    _name = 'wg.cks.info'
    _description = 'Thông tin Chữ ký số'

    issuer = fields.Char('Issuer', required=True)
    subject = fields.Text('Subject', required=True)
    serial = fields.Char('Serial', required=True)
    valid_from = fields.Char('Ngày bắt đầu', required=True)
    valid_to = fields.Char('Ngày hết hạn', required=True)
    HThuc = fields.Selection([('1', 'Thêm mới'), ('2', 'Gia hạn'), ('3', 'Ngừng sử dụng')], 'Hình thức', default='1')
    registry_ids = fields.Many2many('wg.inv.registry', 'wg_inv_registry_cks_info_rel', 'cks_id', 'registry_id', 'Sử dụng cho tờ khai')
