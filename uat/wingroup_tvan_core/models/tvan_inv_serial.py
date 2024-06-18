# -*- coding: utf-8 -*-
import json
import base64
from io import BytesIO
from PIL import Image

import requests
from requests.structures import CaseInsensitiveDict

from num2words import num2words
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.tools.misc import formatLang, format_date
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError
from odoo.addons.qr_code_base.models.qr_code_base import generate_qr_code


class InvoiceSerial(models.Model):
    _name = 'wg.inv.serial'
    _inherit = ['mail.thread']
    _description = 'Mẫu số hoá đơn'


    @api.model 
    def tvan_get_selection_label(self, field_name):
        return dict(self._fields[field_name].selection).get(self[field_name])


    @api.onchange('KHMSHDonTT78')
    def onchange_KHMSHDonTT78(self):
        if self.KHMSHDonTT78:
            self.name = self.KHMSHDonTT78
            self.THDon = str(self.tvan_get_selection_label('KHMSHDonTT78'))
            self.serial = 'C{}{}'.format(
                str(fields.Date.today())[2:4],
                'T' if self.KHMSHDonTT78 in ('1', '2')  else 'D' if self.KHMSHDonTT78 in ('3', '4') else 'N' if self.KHMSHDonTT78 == '6' else 'G' if self.KHMSHDonTT78 == '5' else 'B'
            )

    @api.model
    def create(self, vals):
        res = super(InvoiceSerial, self).create(vals)
        if 'order_id' in vals:
            res.order_id.write({
                'inv_serial_id': res.id,
            })
        res.write({
            'partner_vat': res.order_id.partner_id.vat,
            'partner_name': res.order_id.partner_id.name,
            'partner_address': res.order_id.partner_id.address2,
            'partner_email': res.order_id.partner_id.email,
            'partner_phone': res.order_id.partner_id.phone,
        })
        return res

    order_id = fields.Many2one('sale.order', 'Đơn hàng')
    partner_vat = fields.Char('Mã số thuế', tracking=3, readonly=True, states={'new': [('readonly', False)]})
    partner_name = fields.Char('Tên công ty', tracking=3, readonly=True, states={'new': [('readonly', False)]})
    partner_address = fields.Char('Địa chỉ', tracking=3, readonly=True, states={'new': [('readonly', False)]})
    partner_email = fields.Char('Email', tracking=3, readonly=True, states={'new': [('readonly', False)]})
    partner_phone = fields.Char('Số điện thoại', tracking=3, readonly=True, states={'new': [('readonly', False)]})
    partner_website = fields.Char('Website', tracking=3, readonly=True, states={'new': [('readonly', False)]})
    partner_bank_info = fields.Char('Thông tin ngân hàng', tracking=3, readonly=True, states={'new': [('readonly', False)]})

    samplte_data_id = fields.Many2one('wg.inv.sample.data', 'Mẫu dữ liệu', tracking=3, readonly=True, states={'new': [('readonly', False)]})
    attachment_id = fields.Many2one('ir.attachment', 'File hóa đơn', readonly=True, states={'new': [('readonly', False)]})
    pdf_preview = fields.Binary('pdf_preview', related='attachment_id.datas', store=True)

    image_logo = fields.Binary('Logo công ty', readonly=True, states={'new': [('readonly', False)]})
    image_background = fields.Binary('Ảnh nền', readonly=True, states={'new': [('readonly', False)]})
    sign_display_id = fields.Many2one('wg.hddt.display', 'Định dạng ngày ký', tracking=3, readonly=True, states={'new': [('readonly', False)]})
    image_sign = fields.Binary('Khung chữ ký', readonly=True, states={'new': [('readonly', False)]})

    # inv_cqt_id = fields.Many2one('wg.cqt', 'Cơ quan thuế')
    inv_template_id = fields.Many2one('wg.invoice.template', 'Mẫu hóa đơn có sẵn', readonly=True, states={'new': [('readonly', False)]})
    inv_template_data = fields.Binary('Mẫu hóa đơn tùy chỉnh', readonly=True, states={'new': [('readonly', False)]})
    inv_template_filename = fields.Char('Tên file', tracking=3, readonly=True, states={'new': [('readonly', False)]})

    name = fields.Char('Mẫu số hoá đơn', tracking=3, size=6, readonly=True, states={'new': [('readonly', False)]})
    THDon = fields.Char('Tên hóa đơn', tracking=3, size=100, readonly=True, states={'new': [('readonly', False)]})
    serial = fields.Char('Ký hiệu', tracking=3, size=6, readonly=True, states={'new': [('readonly', False)]})
    quantity = fields.Integer('Số lượng', tracking=3, readonly=True, states={'new': [('readonly', False)]})
    from_qty = fields.Integer('Từ số', tracking=3, default=0, readonly=True, states={'new': [('readonly', False)]}) 
    to_qty = fields.Integer('Đến số', tracking=3, default=0, readonly=True, states={'new': [('readonly', False)]}) 
    current_number = fields.Integer('Số hiện tại', tracking=3, readonly=True, states={'new': [('readonly', False)]})
    residual = fields.Integer('Số còn lại', compute='_compute_residual')
    date = fields.Date('Ngày bắt đầu', tracking=3, readonly=True, states={'new': [('readonly', False)]})
    state = fields.Selection([('new', 'Mới khởi tạo'), ('use', 'Đang sử dụng'), ('cancel', 'Huỷ bỏ')], string='Trạng thái', tracking=3, default='new')

    KHMSHDonTT78 = fields.Selection([
        ('1', 'HĐĐT giá trị gia tăng'),
        ('2', 'HĐĐT bán hàng'),
        ('3', 'HĐĐT bán tài sản công'),
        ('4', 'HĐĐT bán hàng dự trữ quốc gia'),
        ('5', 'Tem/Vé/Thẻ/Phiếu thu/Chứng từ điện tử'),
        ('6', 'PXK kiêm VC nội bộ'),
        ], 'Loại hóa đơn', default='1', tracking=3, readonly=True, states={'new': [('readonly', False)]})

    note = fields.Text('Note', tracking=3)
    template_code = fields.Char('Template code', readonly=True, tracking=3)
    company_id = fields.Many2one('res.company', 'Công ty')

    def name_get(self):
        return [(r.id, '{}{}'.format(r.name or '', r.serial or '')) for r in self]

    @api.depends('current_number', 'to_qty')
    def _compute_residual(self):
        for record in self:
            record.residual = record.to_qty -  record.current_number

    def tvan_prepare_json_data(self):
        try:
            res = json.loads(self.samplte_data_id.data)
            res.update({
                "CompanyImageLogo": self.image_logo and self.image_logo.decode('utf-8') or False,
                "CompanyImageBackground": self.image_background and self.image_background.decode('utf-8') or False,
                "CompanyImageSign": self.image_sign and self.image_sign.decode('utf-8') or False,
            })
            return res
        except Exception as e:
            raise e

# DDansh 

    def create_pdf_file(self):
        # raise ValidationError(str(self.tvan_prepare_json_data()))
        try:
            report_data = { 
                'type': 'ir.actions.report',
                'model': self._name,
                'report_type':'aeroo',
                'in_format':'oo-odt',
                'out_format': self.env['report.mimetypes'].search([('code','=', 'oo-pdf')], limit=1).id,
                'tml_source': 'database',
                'print_report_name': "'Hoá đơn %s'" % (self.partner_vat),
                'report_data': self.inv_template_data,
            }
            report = self.env['ir.actions.report'].new(report_data)
            file_data, out_code, filename = report.with_context(self._context).render_aeroo([self.id], data={})
            attachment_id = self.attachment_id
            att_value = {
                'name': 'HOADON_{}_.pdf'.format(self.partner_vat),
                'res_model': self._name,
                'res_id': self.id,
                'type': 'binary',
                'datas': base64.b64encode(file_data),
                'public': False,
            }
            if not attachment_id:
                attachment_id = self.env['ir.attachment'].create(att_value)
            else:
                attachment_id.write(att_value)
            self.write({
                'attachment_id': attachment_id.id,
            })
        except Exception as e:
            raise e
            # self.create_pdf_file()

    def wg_download_invoice(self):
        if not self.attachment_id:
            self.create_pdf_file()
        attachment = self.attachment_id
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{}/{}?download=1'.format(attachment.id, attachment.name),
            'target': 'self',
        } 

    def test_print(self):
        self.create_pdf_file()
        action = self.env["ir.actions.actions"]._for_xml_id('wingroup_tvan_core.action_hddt_popup2')
        action['res_id'] = self.id
        return action       

    def opacity_background_image(self):
        img = Image.open(BytesIO(base64.b64decode(self.image_background)))
        img.putalpha(50)  # Half alpha; alpha argument must be an int
        with BytesIO() as output:
            img.save(output, format='PNG')
            self.write({
                'image_background': base64.b64encode(output.getvalue())
,
            })


    def action_draft(self):
        self.state = 'new'

    def action_cancel(self):
        self.state = 'cancel'

    def action_confirm(self):
        headers = CaseInsensitiveDict()
        # route_url = 'https://uat.latido.vn/api/report/create'
        # token = '4qp4eEorxZLmUI2Hv42j6cC0XbjhqLMyFZU91NkcSJRLG_2LCwqZoA'
        route_url = self.env['ir.config_parameter'].sudo().get_param('reportpdf.route_commit_template')
        token = self.env['ir.config_parameter'].sudo().get_param('reportpdf.client_key')

        print (route_url, token)
        headers['Accept'] = '*/*'
        headers['Authorization'] = 'Bearer ' + token
        headers['Accept-Encoding'] = 'gzip, deflate, br'
        headers['Connection'] = 'keep-alive'  
        list_fields = ['type', 'partner_vat', 'partner_name', 'partner_vat'] 
        data = {
            'type': self.KHMSHDonTT78,
            'company_vat': self.partner_vat,
            'company_name': self.partner_name,
            'company_address': self.partner_address,
            'inv_template_data': self.inv_template_data.decode('utf-8'),
            'inv_template_filename': self.inv_template_filename,
            'image_logo': self.image_logo.decode('utf-8'),
            'image_background': self.image_background.decode('utf-8'),
            'image_sign': self.image_sign.decode('utf-8'),
            'template_code': self.template_code,
        } 
        try:
            result = requests.post(route_url, json=data, headers=headers)
            data = json.loads(result.text)
            self.template_code = data.get('result').get('data')
        except Exception as e:
            raise ValidationError('Chưa điền đủ các thông tin cần thiết!' + str(e))
        self.state = 'use'
