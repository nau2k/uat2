# -*- coding: utf-8 -*-
import json
import requests
# from confluent_kafka import Consumer


from num2words import num2words
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.tools.misc import formatLang, format_date
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.model 
    def default_inv_display_id(self):
        inv_display = self.env['wg.hddt.display'].search([], limit=1)
        if inv_display:
            return inv_display.id 
        return False

    using_cts_hsm = fields.Boolean('Sử dụng CTS HSM')
    cts_hsm_link = fields.Char('HSM link', default='https://ecloud.wgroup.vn')
    cts_hsm_token = fields.Char('Mã xác thực HSM')
    
    tvan_report_code = fields.Char('Mã report template')

    inv_display_id = fields.Many2one('wg.hddt.display', 'Cấu hình hiển thị ngày ký', default=default_inv_display_id)
    CMTMTTien = fields.Boolean('HĐ có mã khởi tạo từ máy tính tiền')
    CMTMTTien_prefix = fields.Char('Tiền tố mã CQT trên hóa đơn')
    cqt_code = fields.Char('Mã CQT')
    cqt_name = fields.Char('Tên CQT')
    cqt_ddanh = fields.Char('Địa danh')

    @api.model
    def get_tvan_conifg(self):
        tvan_config = self.env['wg.tvan.config'].search([], limit=1)
        if not tvan_config:
            raise ValidationError('Cấu hình Tvan chưa được thiết lập!')
        return tvan_config

    @api.model
    def tvan_send(self, data):
        tvan_config = self.get_tvan_conifg()
        headers = {
            'content-type': 'application/json',
            'Authorization': 'token ' + tvan_config.api_token,
        }
        res = requests.post(tvan_config.api_link + tvan_config.api_send_url, data=json.dumps(data), headers=headers)
        try:
            return json.loads(res.text)
        except Exception as e:
            return {
                'status': 'Fail',
                'message': str(e + ' ' + res.text)
            }

    @api.model
    def kt_get_company(self, company_id=None):
        if not company_id:
            allowed_company_ids = self.env.context.get('allowed_company_ids', [])
            if allowed_company_ids:
                company = self.browse(allowed_company_ids[0])
            else:
                company = self.env.user.company_id
        else:
            company = self.browse(company_id)
        return company
