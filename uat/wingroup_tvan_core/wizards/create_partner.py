# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError

import xlrd
import base64
import pandas as pd
import re

class CreatePartner(models.TransientModel):
    _name = 'wg.create.partner.wiz'
    _description = 'Tạo Khách hàng mới'

    name = fields.Char('Tên khách hàng (*)')
    ref = fields.Char('Mã khách hàng (*)')
    vat = fields.Char('Mã số thuế (*)')
    address2 = fields.Char('Địa chỉ (*)')
    email = fields.Char('Mail khách hàng')

    buyer_name = fields.Char('Tên người mua')
    phone = fields.Char('Số điện thoại')
    acc_bank_number = fields.Char('Số tài khoản')
    acc_bank_name = fields.Char('Tên ngân hàng')
    email_cc = fields.Char('Email CC')


    def wg_find_partner(self):
        action = self.env["ir.actions.actions"]._for_xml_id('wingroup_tvan_core.action_create_partner')
        action['views'] = [(False, 'form')]
        action['target'] = 'new'
        action['res_id'] = self.id
        return action 
    

    def wg_save(self):
        pass