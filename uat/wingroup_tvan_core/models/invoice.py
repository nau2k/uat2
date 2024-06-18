# -*- coding: utf-8 -*-

import json
import base64
from xml.dom import minidom
from lxml import etree

import requests
from requests.structures import CaseInsensitiveDict

from num2words import num2words
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.tools.misc import formatLang, format_date
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError
from odoo.addons.qr_code_base.models.qr_code_base import generate_qr_code


def _vn_num2words(val, affix=' đồng'):
    try:
        tmp_string = num2words(abs(val), lang='vi_VN') + affix
        res = tmp_string[0].upper() + tmp_string[1:]
        if val < 0:
            return '({})'.format(res)
        return res
    except Exception as e:
        return 'Đọc số bị lỗi!'

class AccountInvoice(models.Model):
    _name = 'wg.account.invoice'
    _description = 'Hóa đơn điện tử'
    _inherit = ['wg.invoice.mixin', 'wg.sign.mixin', 'mail.thread']
    _order = 'NLap desc,SHDon desc, id desc'

    def compute_tax(self):
        if len(self.line_ids) <= 0:
            raise ValidationError('Không thể tính "Thuế suất" khi "Chi tiết hàng hóa/dịch vụ" không có dữ liệu!')
        # clear data
        self.tax_ids.unlink()

        for vat in list(set(self.line_ids.mapped('TSuat'))):
            print(vat)
            record_by_vat = self.line_ids.filtered(lambda e: e.TSuat == vat)
            ThTien = sum(record_by_vat.mapped('ThTien'))
            TThue = sum(record_by_vat.mapped('TThue'))
            price_total = sum(record_by_vat.mapped('price_total'))
            self.tax_ids.create({
                'invoice_id': self.id,
                'TSuat': vat,
                'ThTien': ThTien,
                'TThue': TThue,
                'price_total': price_total,
            })
        

    def unlink(self):
        for record in self:
            if record.state != '0':
                raise ValidationError('Không thế xóa hóa dơn đã có chữ ký!')
        return super(AccountInvoice, self).unlink()

    @api.onchange('adjust_for_id')
    def onchange_adjust_for_id(self):
        if self.adjust_for_id:
            self.partner_type = self.adjust_for_id.partner_type
            self.MKHang = self.adjust_for_id.MKHang
            self.HVTNMHang = self.adjust_for_id.HVTNMHang
            self.TenNMua = self.adjust_for_id.TenNMua
            self.MSTNMua = self.adjust_for_id.MSTNMua
            self.DChiNMua = self.adjust_for_id.DChiNMua
            self.DCTDTuNMua = self.adjust_for_id.DCTDTuNMua
            self.STKNHangNMua = self.adjust_for_id.STKNHangNMua
            self.TNHangNMua = self.adjust_for_id.TNHangNMua
            self.email_cc = self.adjust_for_id.email_cc
            self.SDThoaiNMua = self.adjust_for_id.SDThoaiNMua

    @api.onchange('partner_type')
    def onchange_partner_type(self):
        if self.partner_type == '0':
            self.HVTNMHang = ''

    @api.onchange('TCHDon')
    def onchange_TCHDon(self):
        if self.TCHDon == '0':
            self.adjust_for_id = False      

    @api.onchange('inv_serial_id')
    def onchange_inv_serial_id(self):
        if self.inv_serial_id:
            self.KHMSHDon = self.inv_serial_id.name 
            self.KHHDon = self.inv_serial_id.serial 
        else:
            self.KHMSHDon = False
            self.KHHDon = False

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.MKHang = self.partner_id.ref
            self.HVTNMHang = self.partner_id.buyer_name
            self.TenNMua = self.partner_id.name
            self.MSTNMua = self.partner_id.vat
            self.DChiNMua = self.partner_id.address2
            self.DCTDTuNMua = self.partner_id.email
            self.STKNHangNMua = self.partner_id.acc_bank_number
            self.TNHangNMua = self.partner_id.acc_bank_name
            self.email_cc = self.partner_id.email_cc
            self.SDThoaiNMua = self.partner_id.phone
            self.partner_id = False

    partner_id = fields.Many2one('res.partner', 'Tìm khách hàng', domain="[('company_id','=',company_id)]")
    system_note = fields.Text('Ghi ghú hệ thống')
    inv_serial_id = fields.Many2one('wg.inv.serial', 'Ký hiệu', readonly=True,
        states={'0': [('readonly', False)]})
    inv_serial_note = fields.Text('Template name', related='inv_serial_id.note')
    adjust_for_id = fields.Many2one('wg.account.invoice', 'HĐ gốc', readonly=True,
        states={'0': [('readonly', False)]})
    partner_type = fields.Selection([('0', 'Công ty'), ('1', 'Cá nhân')], string='Khách hàng là', default='0', readonly=True,
        states={'0': [('readonly', False)]})
    extend_value = fields.Boolean('Thông tin bổ sung', readonly=True,
        states={'0': [('readonly', False)]})
    email_cc = fields.Char('Danh sách email cc', readonly=True,
        states={'0': [('readonly', False)]})
    state = fields.Selection(tracking=3, copy=False)
    line_ids = fields.One2many('wg.account.invoice.line', 'invoice_id', 'Chi tiết hàng hóa/dịch vụ', readonly=True,
        states={'0': [('readonly', False)]})
    tax_ids = fields.One2many('wg.account.invoice.tax', 'invoice_id', 'Chi tiết thuế suất', readonly=True,
        states={'0': [('readonly', False)]})
    fee_ids = fields.One2many('wg.account.invoice.fee', 'invoice_id', 'Các loại phí', readonly=True,
        states={'0': [('readonly', False)]})
    attachment_id = fields.Many2one('ir.attachment', 'File hóa đơn')
    pdf_preview = fields.Binary('pdf_preview')
    NKy = fields.Datetime('Ngay ky')

    attachment_link = fields.Char('Link xem HĐ')
    field_boolean_find_company = fields.Boolean('Lấy thông tin')

    @api.onchange('field_boolean_find_company')
    def onchange_field_boolean_find_company(self):
        if not self.MSTNMua:
            return
        try:
            headers = CaseInsensitiveDict()
            route_url = self.env['ir.config_parameter'].sudo().get_param('company_info.main_url')
            token = self.env['ir.config_parameter'].sudo().get_param('company_info.client_key')
            headers['Accept'] = '*/*'
            headers['Authorization'] = 'Bearer ' + token
            headers['Accept-Encoding'] = 'gzip, deflate, br'
            headers['Connection'] = 'keep-alive'   
            data = {
                'mst': self.MSTNMua,
            } 
            result = requests.post(route_url, json=data, headers=headers)
            data = json.loads(result.text)
            company_info = dict(data.get('result').get('data'))
            print (company_info, company_info.get('name'), type(company_info.get('name')))
            if company_info:
                self.TenNMua = company_info.get('name')
                self.DChiNMua = company_info.get('address')
        except Exception as e:
            pass

    def tvan_get_filename(self):
        return 'HOA_DON_{vat}_{SR_HD}_{SO_HD}_{date}.xml'.format(
            vat=self.MSTNMua,
            SR_HD=self.name,
            SO_HD=self.SHDon or 'draft',
            date=str(self.NLap).replace('-' , '_'),
        )

    # Gọi API TVan lấy mẫu XML
    def set_xml_data(self):
        attachment_origin_id = self.attachment_origin_id
        att_value = {
            'name': self.tvan_get_filename(),
            'res_model': self._name,
            'res_id': self.id,
            'type': 'binary',
            'datas': self.tvan_init_invoice_data(),
            'public': True,
        }
        if not attachment_origin_id:
            attachment_origin_id = self.env['ir.attachment'].create(att_value)
        else:
            attachment_origin_id.write(att_value)
        self.write({
            'attachment_origin_id': attachment_origin_id.id,
        })

    @api.model
    def tvan_refactor_decimal_value(self, value):
        if value == int(value):
            return int(value)
        return value        

    def tvan_prepare_json_data(self):
        try:
            SignDate = self.NLap.strftime(self.inv_serial_id.sign_display_id.code)
        except Exception as e:
            SignDate = "Ký " + self.NLap.strftime('ngày %d tháng %m năm %Y')
        res = {
            "TCHDon": self.TCHDon,
            "CompanyVat": self.inv_serial_id.partner_vat,
            "CompanyName": self.inv_serial_id.partner_name,
            "CompanyAddress": self.inv_serial_id.partner_address,
            "CompanyEmail": self.inv_serial_id.partner_email,
            "CompanyPhone": self.inv_serial_id.partner_phone,
            "CompanyWebsite": self.inv_serial_id.partner_website,
            "CompanyBankInfo": self.inv_serial_id.partner_bank_info,
            "CompanyImageLogo": self.inv_serial_id.image_logo and self.inv_serial_id.image_logo.decode('utf-8') or False,
            "CompanyImageBackground": self.inv_serial_id.image_background and self.inv_serial_id.image_background.decode('utf-8') or False,
            "CompanyImageSign": self.inv_serial_id.image_sign and self.inv_serial_id.image_sign.decode('utf-8') or False,
            "TCHDonName": "Hóa đơn gốc" if self.TCHDon == "0" else "Điều chỉnh" if self.TCHDon == "1" else "Thay thế'" if self.TCHDon == "2" else "",
            "HDLQKHMSHDon": self.adjust_for_id.KHMSHDon,
            "HDLQKHHDon": self.adjust_for_id.KHHDon,
            "HDLQSHDon": self.adjust_for_id.SHDon,
            "HDLQNKy": self.adjust_for_id and self.adjust_for_id.NLap.strftime('%d/%m/%Y') or '',            
            "HDLQNKyNgay": self.adjust_for_id and self.adjust_for_id.NLap.strftime('%d') or '',
            "HDLQNKyThang": self.adjust_for_id and self.adjust_for_id.NLap.strftime('%m') or '',
            "HDLQNKyNam": self.adjust_for_id and self.adjust_for_id.NLap.strftime('%Y') or '',
            "KHMSHDon": self.KHMSHDon,
            "KHHDon": self.KHHDon,
            "SHDon": self.SHDon,
            "NLap": str(self.NLap),
            "NLapNgay": self.NLap.strftime('%d'),
            "NLapThang": self.NLap.strftime('%m'),
            "NLapNam": self.NLap.strftime('%Y'),
            "NKy": str(self.NLap),
            "NKyNgay": self.NLap.strftime('%d'),
            "NKyThang": self.NLap.strftime('%m'),
            "NKyNam": self.NLap.strftime('%Y'),
            "SBKe": self.SBKe or "",
            "NBKe": self.NBKe and str(self.NBKe) or "",
            "DVTTe": self.DVTTe,
            "TGia": self.tvan_refactor_decimal_value(self.TGia),
            "HTTToan": self.HTTToan or "",
            "TenNBan": self.inv_serial_id.partner_name or self.company_id.name,
            "MSTNBan": self.inv_serial_id.partner_vat or self.company_id.vat,
            "DChiNban": self.inv_serial_id.partner_address or self.company_id.partner_id.address2,
            "SDThoaiNBan": self.inv_serial_id.partner_phone or self.company_id.phone or "",
            "TenNMua": self.TenNMua,
            "MSTNMua": self.MSTNMua,
            "DChiNMua": self.DChiNMua,
            "MKHang": self.MKHang or "",
            "HVTNMHang": self.HVTNMHang or "",
            "DSHHDVu": [
                {
                    "TChat": line.TChat,
                    "STT": index+1,
                    "MHHDVu": line.MHHDVu or "",
                    "THHDVu": line.THHDVu, # Bắt buộc
                    "DVTinh": line.DVTinh or "",
                    "SLuong": self.tvan_refactor_decimal_value(line.SLuong),
                    "SLuongStr": line.SLuong and formatLang(self.env, line.SLuong, digits=0) or 0,
                    "DGia": self.tvan_refactor_decimal_value(line.DGia),
                    "DGiaStr": line.DGia and formatLang(self.env, line.DGia, digits=0) or 0,
                    "TLCKhau": self.tvan_refactor_decimal_value(line.TLCKhau),
                    "TLCKhauStr": line.TLCKhau and formatLang(self.env, line.TLCKhau, digits=0) or 0,
                    "STCKhau": self.tvan_refactor_decimal_value(line.STCKhau),
                    "STCKhauStr": line.STCKhau and formatLang(self.env, line.STCKhau, digits=0) or 0,
                    "ThTien": self.tvan_refactor_decimal_value(line.ThTien),
                    "ThTienStr": line.ThTien and formatLang(self.env, line.ThTien, digits=0) or 0,
                    "TSuat": line.TSuat,
                    "TThueStr": line.TThue and formatLang(self.env, line.TThue, digits=0) or 0,
                    "TCongStr": line.price_total and formatLang(self.env, line.price_total, digits=0) or 0,
                } for index, line in enumerate(self.line_ids)
            ],
            "footer_data": [
                {
                    "STT": index+1,
                    "TSuat": line.TSuat,
                    "ThTien": self.tvan_refactor_decimal_value(line.ThTien),
                    "ThTienStr": line.ThTien and formatLang(self.env, line.ThTien, digits=0) or 0,
                    "TThue": self.tvan_refactor_decimal_value(line.TThue),
                    "TThueStr": line.TThue and formatLang(self.env, line.TThue, digits=0) or 0,
                    "TCongStr": line.price_total and formatLang(self.env, line.price_total, digits=0) or 0,
                } for index, line in enumerate(self.tax_ids)
            ],
            "footer_data2":  { 
                str(line.TSuat): {
                    "TSuat": line.TSuat,
                    "ThTien": self.tvan_refactor_decimal_value(line.ThTien),
                    "ThTienStr": line.ThTien and formatLang(self.env, line.ThTien, digits=0) or 0,
                    "TThue": self.tvan_refactor_decimal_value(line.TThue),
                    "TThueStr": line.TThue and formatLang(self.env, line.TThue, digits=0) or 0,
                    "TCongStr": line.price_total and formatLang(self.env, line.price_total, digits=0) or 0,
                }
                for index, line in enumerate(self.tax_ids) 
            } ,
            "DSLPhi": [
                {
                    "STT": index+1,
                    "TLPhi": line.name,
                    "TPhi": self.tvan_refactor_decimal_value(line.value),
                    "TPhiStr": line.value and formatLang(self.env, line.value, digits=0) or 0,
                } for index, line in enumerate(self.fee_ids)
            ],
            "MCCQT": self.MCCQT or "",
            "TgTCThue": self.tvan_refactor_decimal_value(self.TgTCThue),
            "TgTCThueStr": formatLang(self.env, self.TgTCThue, digits=0) or 0,
            "TgTThue": self.tvan_refactor_decimal_value(self.TgTThue),
            "TgTThueStr": formatLang(self.env, self.TgTThue, digits=0) or 0,
            "TgTTTBSo": self.tvan_refactor_decimal_value(self.TgTTTBSo),
            "TgTTTBSoStr": formatLang(self.env, self.TgTTTBSo, digits=0) or 0,
            "TongPhi": self.tvan_refactor_decimal_value(self.amount_fee),
            "TongPhiStr": formatLang(self.env, self.amount_fee, digits=0) or 0,
            "TgTTTBChu": self.TgTTTBChu,
            "SignTitle": "CHỮ KÝ SỐ HỢP LỆ",
            "SignBy": "Ký bởi: " + str(self.inv_serial_id.partner_name),
            "SignDate": "Ký " + self.NLap.strftime('ngày %d tháng %m năm %Y'),
            "TrackingLink": "https://tracuu.hoadonkhanhlinh.vn",
            "TrackingCode": "LACKUTE102",
            "ImageQRCode": generate_qr_code('https://hoadonkhanhlinh.vn').decode('utf-8'),
        }

        if self.TCHDon != '0':
            res["LHDCLQuan"] = {
                "TCHDon": self.TCHDon,
                "LHDCLQuan": self.KHMSHDonTT78,
                "KHMSHDCLQuan": self.adjust_for_id.KHMSHDon,
                "KHHDCLQuan": self.adjust_for_id.KHHDon,
                "SHDCLQuan": self.adjust_for_id.SHDon,
                "NLHDCLQuan": self.adjust_for_id and self.adjust_for_id.NLap.strftime('%Y-%m-%d') or '',
                "GChu": "",
            }
        return res

    def tvan_prepare_json_xml(self):
        try:
            SignDate = self.NLap.strftime(self.inv_serial_id.sign_display_id.code)
        except Exception as e:
            SignDate = "Ký " + self.NLap.strftime('ngày %d tháng %m năm %Y')
        res = {
            "TCHDon": self.TCHDon,
            "CompanyVat": self.inv_serial_id.partner_vat,
            "CompanyName": self.inv_serial_id.partner_name,
            "CompanyAddress": self.inv_serial_id.partner_address,
            "CompanyEmail": self.inv_serial_id.partner_email,
            "CompanyPhone": self.inv_serial_id.partner_phone,
            "CompanyWebsite": self.inv_serial_id.partner_website,
            "CompanyBankInfo": self.inv_serial_id.partner_bank_info,
            "CompanyImageLogo": self.inv_serial_id.image_logo and self.inv_serial_id.image_logo.decode('utf-8') or False,
            "CompanyImageBackground": self.inv_serial_id.image_background and self.inv_serial_id.image_background.decode('utf-8') or False,
            "CompanyImageSign": self.inv_serial_id.image_sign and self.inv_serial_id.image_sign.decode('utf-8') or False,
            "TCHDonName": "Hóa đơn gốc" if self.TCHDon == "0" else "Điều chỉnh" if self.TCHDon == "1" else "Thay thế'" if self.TCHDon == "2" else "",
            "HDLQKHMSHDon": self.adjust_for_id.KHMSHDon,
            "HDLQKHHDon": self.adjust_for_id.KHHDon,
            "HDLQSHDon": self.adjust_for_id.SHDon,
            "HDLQNKy": self.adjust_for_id and self.adjust_for_id.NLap.strftime('%d/%m/%Y') or '',            
            "HDLQNKyNgay": self.adjust_for_id and self.adjust_for_id.NLap.strftime('%d') or '',
            "HDLQNKyThang": self.adjust_for_id and self.adjust_for_id.NLap.strftime('%m') or '',
            "HDLQNKyNam": self.adjust_for_id and self.adjust_for_id.NLap.strftime('%Y') or '',
            "KHMSHDon": self.KHMSHDon,
            "KHHDon": self.KHHDon,
            "SHDon": self.SHDon,
            "NLap": str(self.NLap),
            "NLapNgay": self.NLap.strftime('%d'),
            "NLapThang": self.NLap.strftime('%m'),
            "NLapNam": self.NLap.strftime('%Y'),
            "NKy": str(self.NLap),
            "NKyNgay": self.NLap.strftime('%d'),
            "NKyThang": self.NLap.strftime('%m'),
            "NKyNam": self.NLap.strftime('%Y'),
            "SBKe": self.SBKe or "",
            "NBKe": self.NBKe and str(self.NBKe) or "",
            "DVTTe": self.DVTTe,
            "TGia": self.tvan_refactor_decimal_value(self.TGia),
            "HTTToan": self.HTTToan or "",
            "TenNBan": self.inv_serial_id.partner_name or self.company_id.name,
            "MSTNBan": self.inv_serial_id.partner_vat or self.company_id.vat,
            "DChiNban": self.inv_serial_id.partner_address or self.company_id.partner_id.address2,
            "SDThoaiNBan": self.inv_serial_id.partner_phone or self.company_id.phone or "",
            "TenNMua": self.TenNMua,
            "MSTNMua": self.MSTNMua,
            "DChiNMua": self.DChiNMua,
            "MKHang": self.MKHang or "",
            "HVTNMHang": self.HVTNMHang or "",
            "DSHHDVu": [
                {
                    "HHDVu": {
                        "TChat": line.TChat,
                        "STT": index+1,
                        "MHHDVu": line.MHHDVu or "",
                        "THHDVu": line.THHDVu, # Bắt buộc
                        "DVTinh": line.DVTinh or "",
                        "SLuong": self.tvan_refactor_decimal_value(line.SLuong),
                        "SLuongStr": line.SLuong and formatLang(self.env, line.SLuong, digits=0) or 0,
                        "DGia": self.tvan_refactor_decimal_value(line.DGia),
                        "DGiaStr": line.DGia and formatLang(self.env, line.DGia, digits=0) or 0,
                        "TLCKhau": self.tvan_refactor_decimal_value(line.TLCKhau),
                        "TLCKhauStr": line.TLCKhau and formatLang(self.env, line.TLCKhau, digits=0) or 0,
                        "STCKhau": self.tvan_refactor_decimal_value(line.STCKhau),
                        "STCKhauStr": line.STCKhau and formatLang(self.env, line.STCKhau, digits=0) or 0,
                        "ThTien": self.tvan_refactor_decimal_value(line.ThTien),
                        "ThTienStr": line.ThTien and formatLang(self.env, line.ThTien, digits=0) or 0,
                        "TSuat": line.TSuat,
                        "TThueStr": line.TThue and formatLang(self.env, line.TThue, digits=0) or 0,
                        "TCongStr": line.price_total and formatLang(self.env, line.price_total, digits=0) or 0,
                    }
                } for index, line in enumerate(self.line_ids)
            ],
            "footer_data": [
                {
                    "LTSuat": {
                        "STT": index+1,
                        "TSuat": line.TSuat,
                        "ThTien": self.tvan_refactor_decimal_value(line.ThTien),
                        "ThTienStr": line.ThTien and formatLang(self.env, line.ThTien, digits=0) or 0,
                        "TThue": self.tvan_refactor_decimal_value(line.TThue),
                        "TThueStr": line.TThue and formatLang(self.env, line.TThue, digits=0) or 0,
                        "TCongStr": line.price_total and formatLang(self.env, line.price_total, digits=0) or 0,
                    }
                } for index, line in enumerate(self.tax_ids)
            ],
            "footer_data2":  { 
                str(line.TSuat): {
                    "TSuat": line.TSuat,
                    "ThTien": self.tvan_refactor_decimal_value(line.ThTien),
                    "ThTienStr": line.ThTien and formatLang(self.env, line.ThTien, digits=0) or 0,
                    "TThue": self.tvan_refactor_decimal_value(line.TThue),
                    "TThueStr": line.TThue and formatLang(self.env, line.TThue, digits=0) or 0,
                    "TCongStr": line.price_total and formatLang(self.env, line.price_total, digits=0) or 0,
                }
                for index, line in enumerate(self.tax_ids) 
            } ,
            "DSLPhi": [
                {
                    "STT": index+1,
                    "TLPhi": line.name,
                    "TPhi": self.tvan_refactor_decimal_value(line.value),
                    "TPhiStr": line.value and formatLang(self.env, line.value, digits=0) or 0,
                } for index, line in enumerate(self.fee_ids)
            ],
            "MCCQT": self.MCCQT or "",
            "TgTCThue": self.tvan_refactor_decimal_value(self.TgTCThue),
            "TgTCThueStr": formatLang(self.env, self.TgTCThue, digits=0) or 0,
            "TgTThue": self.tvan_refactor_decimal_value(self.TgTThue),
            "TgTThueStr": formatLang(self.env, self.TgTThue, digits=0) or 0,
            "TgTTTBSo": self.tvan_refactor_decimal_value(self.TgTTTBSo),
            "TgTTTBSoStr": formatLang(self.env, self.TgTTTBSo, digits=0) or 0,
            "TongPhi": self.tvan_refactor_decimal_value(self.amount_fee),
            "TongPhiStr": formatLang(self.env, self.amount_fee, digits=0) or 0,
            "TgTTTBChu": self.TgTTTBChu,
            "SignTitle": "CHỮ KÝ SỐ HỢP LỆ",
            "SignBy": "Ký bởi: " + str(self.inv_serial_id.partner_name),
            "SignDate": "Ký " + self.NLap.strftime('ngày %d tháng %m năm %Y'),
            "TrackingLink": "https://tracuu.hoadonkhanhlinh.vn",
            "TrackingCode": "LACKUTE102",
            "ImageQRCode": generate_qr_code('https://hoadonkhanhlinh.vn').decode('utf-8'),
        }

        if self.TCHDon != '0':
            res["LHDCLQuan"] = {
                "TTHDLQuan":{
                    "TCHDon": self.TCHDon,
                    "LHDCLQuan": self.KHMSHDonTT78,
                    "KHMSHDCLQuan": self.adjust_for_id.KHMSHDon,
                    "KHHDCLQuan": self.adjust_for_id.KHHDon,
                    "SHDCLQuan": self.adjust_for_id.SHDon,
                    "NLHDCLQuan": self.adjust_for_id and self.adjust_for_id.NLap.strftime('%Y-%m-%d') or '',
                    "GChu": "",
                }
            }
        return res

    def tvan_prepare_json_data2(self):
        res = self.tvan_prepare_json_data()
        res.pop('CompanyImageLogo')
        res.pop('CompanyImageBackground')
        res.pop('CompanyImageSign')
        return json.dumps(res)

    def tvan_init_invoice_data(self):
        data = self.tvan_prepare_json_data()
        data.pop('CompanyImageLogo')
        data.pop('CompanyImageBackground')
        data.pop('CompanyImageSign')
        route_url = self.env['ir.config_parameter'].sudo().get_param('tvan.route_inv')
        res = self.tvan_call_api(route_url, data)        
        return res.get('data', False)

    # Ký hóa đơn
    def wg_sign_invoice_vat(self):
        self.set_xml_data()
        return self.wg_open_digial_link_backend()

    def wg_handle_signed_data(self, data):
        res = super(AccountInvoice, self).wg_handle_signed_data(data)
        self.wg_send_tct()
        self.create_pdf_file()
        return self.wg_view()

    def wg_send(self):
        pass

    def tvan_sign_with_hsm(self):
        headers = CaseInsensitiveDict()
        route_url = self.company_id.cts_hsm_link + '/hsm/xml-inv'
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

    def wg_send_tct(self):
        # TODO: Gọi API Tvan truyền dữ liệu
        if not self.MTDiep:
            route_url = self.env['ir.config_parameter'].sudo().get_param('tvan.RequestMTDiep')
            res = self.tvan_call_api(route_url, {})        
            self.MTDiep = res.get('data', False)
        data = {
            'type': '200',
            'inv_number': self.SHDon,
            'vat': self.company_id.vat,
            'company_name': self.company_id.name,
            'MTDiep': self.MTDiep,
            'datas': self.attachment_sign_id.datas.decode('utf-8')
        }
        res = self.tvan_call_api(self.env['ir.config_parameter'].sudo().get_param('tvan.SendMessage'), data)        
        if res.get('status') == 'fail':
            raise ValidationError(res.get('message'))
        self.state  = '1'        

    def tvan_search(self):
        res = self.tvan_call_api('/api/tvan/search', data={'MTDiep': self.MTDiep, 'pretty_print': False})
        print ('tvan search in Client', res)
        json_data = res.get('json_data', [])
        for line in json_data:
            if line.get('type') == '202':
                self.MCCQT = line.get('MCCQT')

    # Xử lý hóa đơn: Điều chỉnh/thay thế
    def wg_handle(self):
        action = self.env["ir.actions.actions"]._for_xml_id('wingroup_tvan_core.action_adjust_invoice')
        action['views'] = [(False, 'form')]
        action['target'] = 'new'
        action['context'] = {
            'default_invoice_id': self.id,
            'default_inv_serial_id': self.inv_serial_id.id,
            'default_SHDon': self.SHDon,
            'default_NLap': self.NLap,
            'default_MSTNMua': self.MSTNMua,
            'default_TenNMua': self.TenNMua,
            'default_DChiNMua': self.DChiNMua,
            'default_DCTDTuNMua': self.DCTDTuNMua,
            'default_SDThoaiNMua': self.SDThoaiNMua,
            'default_HVTNMHang': self.HVTNMHang,
        }
        return action 


    def tvan_create_pdf_file(self):
        headers = CaseInsensitiveDict()
        route_url = self.env['ir.config_parameter'].sudo().get_param('reportpdf.route_get_pdf')
        token = self.env['ir.config_parameter'].sudo().get_param('reportpdf.client_key')
        headers['Accept'] = '*/*'
        headers['Authorization'] = 'Bearer ' + token
        headers['Accept-Encoding'] = 'gzip, deflate, br'
        headers['Connection'] = 'keep-alive'  
        data = self.tvan_prepare_json_data()
        # if not self.company_id.tvan_report_code:
        #     raise ValidationError('Mẫu hoá đơn chưa được khởi tạo!')
        data['template_code'] = self.inv_serial_id.template_code
        data['print_report_name'] = "'{}'".format(self.tvan_get_filename())
        data.pop('CompanyImageLogo')
        data.pop('CompanyImageBackground')
        data.pop('CompanyImageSign')
        try:
            result = requests.post(route_url, json=data, headers=headers)
            res = json.loads(result.text)
            self.attachment_link = res.get('result').get('message').get('url')
            self.pdf_preview = res.get('result').get('message').get('pdf_data')
            return res.get('result').get('message')
        except Exception as e:
            raise e

    # Xem hoa don
    def tvan_view_pdf(self):
        # TODO
        self.tvan_create_pdf_file()
        action = self.env['ir.actions.actions']._for_xml_id('wingroup_tvan_core.action_hddt_popup')
        action['res_id'] = self.id
        return action

    def tvan_download_invoice(self):
        attachment = self.attachment_pdf_id
        att_value = {
            'name': self.tvan_get_filename().replace('.xml', '.pdf'),
            'res_model': self._name,
            'res_id': self.id,
            'type': 'binary',
            'datas': self.pdf_preview,
        }
        if not attachment:
            attachment = self.env['ir.attachment'].create(att_value)
        else:
            attachment.write(att_value)
        self.attachment_pdf_id = attachment.id
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{}/{}?download=1'.format(attachment.id, attachment.name),
            'target': 'self',
        } 


    TgTCThue = fields.Float(compute='_wg_compute_all_value', store=True)
    TgTCThue = fields.Float(compute='_wg_compute_all_value', store=True)
    TgTThue = fields.Float(compute='_wg_compute_all_value', store=True)
    TTCKTMai = fields.Float(compute='_wg_compute_all_value', store=True)
    TgTTTBSo = fields.Float(compute='_wg_compute_all_value', store=True)
    amount_fee = fields.Float(compute='_wg_compute_all_value', store=True)
    TgTTTBChu = fields.Char(compute='_wg_compute_all_value', store=True, readonly=True,
        states={'0': [('readonly', False)]})
    using_cts_hsm = fields.Boolean('Sử dụng CTS HSM', related='company_id.using_cts_hsm', store=True)

    @api.depends('line_ids', 'line_ids.ThTien', 'line_ids.STCKhau', 'line_ids.TThue', 'fee_ids', 'fee_ids.value')
    def _wg_compute_all_value(self):
        for record in self:
            record.TgTThue = round(sum(record.line_ids.mapped('TThue')), 2)
            record.TgTCThue = round(sum(record.line_ids.mapped('ThTien')), 3)
            record.TTCKTMai = round(sum(record.line_ids.mapped('STCKhau')), 3)
            record.amount_fee = round(sum(record.fee_ids.mapped('value')), 3)
            record.TgTTTBSo = round(record.TgTCThue + record.TgTThue + record.amount_fee, 3)
            record.TgTTTBChu = _vn_num2words(record.TgTTTBSo)

    def wg_get_id_content_to_sign(self):
        return ['DLHDon']

    def wg_get_tag_to_sign(self):
        return ['DSCKS', 'NBan']

class AccountInvoiceLine(models.Model):
    _name = 'wg.account.invoice.line'
    _description = 'Hóa đơn điện tử'
    _inherit = 'wg.invoice.line.mixin'
    _order = 'invoice_id desc, sequence'

    # @api.onchange('ThTien', 'TLCKhau', 'TThue')
    # def onchange_ThTien(self):
    #     self.STCKhau = self.ThTien * self.TLCKhau / 100
    #     self.TThue = self.ThTien * self.TLCKhau / 100
    #     self.price_total = self.ThTien + self.TThue
    
    @api.onchange('SLuong', 'DGia')
    def onchange_sl_dgia(self):
        if self.SLuong and self.DGia:
            self.ThTien = self.SLuong * self.DGia
            
    @api.onchange('ThTien', 'TLCKhau')
    def onchange_ThTien_TLCKhau(self):
        if self.ThTien and self.TLCKhau:
            self.STCKhau = self.ThTien * self.TLCKhau / 100

    @api.onchange('ThTien', 'TLCKhau', 'TSuat')
    def onchange_TThue(self):
        try:
            vat_rate = int(self.TSuat.rstrip('%'))
            self.TThue = (self.ThTien - self.STCKhau) * vat_rate / 100
        except:
            self.TThue = 0

    @api.onchange('ThTien', 'STCKhau', 'TThue')
    def onchange_price_total(self):
        self.price_total = (self.ThTien - self.STCKhau) + self.TThue


    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.MHHDVu = self.product_id.default_code
            self.THHDVu = self.product_id.name
            self.DVTinh = self.product_id.uom_name2
            self.DGia = self.product_id.list_price
            self.product_id = False

    sequence = fields.Integer('sequence')
    invoice_id = fields.Many2one('wg.account.invoice', 'Hóa đơn', copy=False)
    company_id = fields.Many2one(related='invoice_id.company_id', store=True)
    product_id = fields.Many2one('product.template', 'Tìm HD/DV', domain="[('company_id','=',company_id)]")

    # tax_id = fields.Many2one('kt.account.tax')
    TThue = fields.Float('Tiền thuế', digits=(21, 6), help='Tiền thuế')
    price_total = fields.Float('TT có VAT', digits=(21, 6), help='Thành tiền đã bao gồm VAT')

    SLuong = fields.Float('Số lượng', digits=(21, 6), default=1)
    DGia = fields.Float(digits=(21, 3))
    TLCKhau = fields.Float(digits=(6, 2))
    STCKhau = fields.Float(digits=(21, 2))
    ThTien = fields.Float(digits=(21, 2))     


class AccountInvoiceTax(models.Model):
    _name = 'wg.account.invoice.tax'
    _description = 'Hóa đơn điện tử'
    _inherit = 'wg.invoice.tax.mixin'
    _order = 'invoice_id desc, sequence'

    @api.depends('TThue', 'ThTien')
    def _wg_compute_all_value(self):
        for record in self:
            record.price_total = record.ThTien + record.TThue

    sequence = fields.Integer('sequence')
    price_total = fields.Float('TT có VAT', compute='_wg_compute_all_value', digits=(21, 6), help='Thành tiền đã bao gồm VAT')
    invoice_id = fields.Many2one('wg.account.invoice', 'Hóa đơn', copy=False)    
    
    


class AccountInvoiceFee(models.Model):
    _name = 'wg.account.invoice.fee'
    _description = 'Hóa đơn điện tử'
    _order = 'invoice_id desc, sequence'

    sequence = fields.Integer('sequence')
    invoice_id = fields.Many2one('wg.account.invoice', 'Hóa đơn', copy=False)     
    name = fields.Char('Tên loại phí', size=100, required=True)   
    value = fields.Float('Tiền phí', digits=(21, 6))