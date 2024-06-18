# -*- coding: utf-8 -*-
import base64
from xml.dom import minidom

import json
import requests
from requests.structures import CaseInsensitiveDict


from num2words import num2words
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.tools.misc import formatLang, format_date
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError


class HDDTNoticeErrorInv(models.Model):
    _name = 'wg.hddt.notice.error.inv'    
    _inherit = ['wg.tb04.mixin', 'wg.sign.mixin', 'mail.thread']
    _description = 'Thông báo Hóa đơn sai sót'    
    _order = 'NTBao desc,id desc'

    @api.model 
    def default_get(self, default_fields):
        res = super(HDDTNoticeErrorInv, self).default_get(default_fields)
        company = self.env['res.company'].kt_get_company()
        if company:
            res.update({
                'MCQT': company.cqt_code,
                'TCQT': company.cqt_name,
                'DDanh': company.cqt_ddanh,
                'TNNT': company.name,
                'MST': company.vat,
            })
        return res

    def name_get(self):
        return [(r.id, '{} {}'.format(r.MSo, r.MST)) for r in self]


    state = fields.Selection(tracking=3, copy=False)
    reason = fields.Text('Lý do chung', readonly=True, states={'0': [('readonly', False)]})
    line_ids = fields.One2many('wg.hddt.notice.error.inv.line', 'inv_error_id', 'Danh sách hóa đơn', 
        readonly=True, states={'0': [('readonly', False)]})
    using_cts_hsm = fields.Boolean('Sử dụng CTS HSM', related='company_id.using_cts_hsm', store=True)

    # TODO: 
    # 1 Tòa khai đăng ký sở dụng hóa đơn điện tử ['DLTKhai']
    # 2 Hóa đơn điện tử ['DLHDon']
    # 3 Thông báo sai sót ['DLTBao']
    def wg_get_id_content_to_sign(self):
        return ['DLTBao']

        
    def wg_send_tct(self):
        # TODO: Gọi API Tvan truyền dữ liệu
        if not self.MTDiep:
            route_url = self.env['ir.config_parameter'].sudo().get_param('tvan.RequestMTDiep')
            res = self.tvan_call_api(route_url, {})        
            self.MTDiep = res.get('data', False)
        data = {
            'type': '300',
            'inv_number': 'x',
            'vat': self.company_id.vat,
            'company_name': self.company_id.name,
            'MTDiep': self.MTDiep,
            'datas': self.attachment_sign_id.datas.decode('utf-8')
        }
        res = self.tvan_call_api(self.env['ir.config_parameter'].sudo().get_param('tvan.SendMessage'), data)        
        if res.get('status') == 'fail':
            raise ValidationError(res.get('message'))
        self.state  = '1'  

    def tvan_prepare_json_data(self):
        res = {
            "MSo": self.MSo,
            "Ten": self.Ten,
            "Loai": self.Loai,
            "So": self.So or "",
            "NTBCCQT": self.NTBCCQT or "",
            "MCQT": self.MCQT,
            "TCQT": self.TCQT,
            "TNNT": self.TNNT,
            "MST": self.MST,
            "MDVQHNSach": self.MDVQHNSach or "",
            "DDanh": self.DDanh,
            "NTBao": str(self.NTBao),
            "DSHDon": [
                {
                    "HDon":{
                            "STT": index+1,
                            "MCQTCap": line.MCQTCap or "",
                            "KHMSHDon": line.KHMSHDon or "",
                            "KHHDon": line.KHHDon or "",
                            "SHDon": line.SHDon or "",
                            "Ngay": str(line.Ngay) or "",
                            "LADHDDT": line.LADHDDT or "",
                            "TCTBao": line.TCTBao or "",
                            "LDo": line.LDo or "",
                        }
                } for index, line in enumerate(self.line_ids)
            ],
        }
        print (res)
        return res

    def tvan_init_tb04_data(self):
        data = self.tvan_prepare_json_data()
        route_url = self.env['ir.config_parameter'].sudo().get_param('tvan.route_tbss')
        res = self.tvan_call_api(route_url, data)        
        return res.get('data', False)

    def tvan_get_filename(self):
        return 'TBSS_{}.xml'.format(self.MST)

    # Gọi API TVan lấy mẫu XML
    def set_xml_data(self):
        attachment_origin_id = self.attachment_origin_id
        att_value = {
            'name': self.tvan_get_filename(),
            'res_model': self._name,
            'res_id': self.id,
            'type': 'binary',
            'datas': self.tvan_init_tb04_data(),
            'public': True,
        }
        if not attachment_origin_id:
            attachment_origin_id = self.env['ir.attachment'].create(att_value)
        else:
            attachment_origin_id.write(att_value)
        self.write({
            'attachment_origin_id': attachment_origin_id.id,
        })

    # Ký TBSS
    def wg_sign_invoice_vat(self):
        return self.wg_open_digial_link_backend()        

    def tvan_sign_with_hsm(self):
        headers = CaseInsensitiveDict()
        route_url = self.company_id.cts_hsm_link + '/hsm/xml-04'
        token = self.company_id.cts_hsm_token
        print (route_url, token)
        headers['Accept'] = '*/*'
        headers['Authorization'] = 'Bearer ' + token
        headers['Accept-Encoding'] = 'gzip, deflate, br'
        headers['Connection'] = 'keep-alive'  
        data = {
            # 'output_format': 'text',
            # 'input_format': 'text',
            'file_data': self.attachment_origin_id.datas,
        }
        try:
            result = requests.post(route_url, json=data, headers=headers)
            res = json.loads(result.text).get('result')
            if res.get('status') == 'Success':
                attachment_sign_id = self.attachment_sign_id
                att_value = {
                    'name': self.tvan_get_filename().replace('.xml', '_sign.xml'),
                    'res_model': self._name,
                    'res_id': self.id,
                    'type': 'binary',
                    'datas': res.get('file_data'),
                    # 'public': True,
                }
                if not attachment_sign_id:
                    attachment_sign_id = self.env['ir.attachment'].create(att_value)
                else:
                    attachment_sign_id.write(att_value)
                self.write({
                    'attachment_sign_id': attachment_sign_id.id,
                })
            else:
                raise ValidationError(res.get('message'))
        except Exception as e:
            raise e   

    # TODO
    def tvan_search(self):
        res = self.tvan_call_api('/api/tvan/search', data={'MTDiep': self.MTDiep, 'pretty_print': False})
        print ('tvan search in Client', res)


class HDDTNoticeErrorInvLine(models.Model):
    _name = 'wg.hddt.notice.error.inv.line'    
    _inherit = ['wg.tb04.line.mixin', 'mail.thread']
    _description = 'Chi tiết thông báo Hóa đơn điện tử có sai sót'    
    _order = 'inv_error_id, sequence'


    @api.onchange('invoice_id')
    def onchange_invoice_id(self):
        if self.invoice_id:
            self.inv_serial_id = self.invoice_id.inv_serial_id
            self.MCQTCap = self.invoice_id.MCCQT
            self.KHMSHDon = self.invoice_id.KHMSHDon
            self.KHHDon = self.invoice_id.KHHDon
            self.SHDon = self.invoice_id.SHDon
            self.Ngay = self.invoice_id.NLap


    sequence = fields.Integer('sequence')
    inv_error_id = fields.Many2one('wg.hddt.notice.error.inv', 'Thông báo sai sót')
    invoice_id = fields.Many2one('wg.account.invoice', 'Hóa đơn', copy=False)
    inv_serial_id = fields.Many2one('wg.inv.serial', 'Ký hiệu')