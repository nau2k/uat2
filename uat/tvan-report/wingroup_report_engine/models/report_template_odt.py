# -*- coding: utf-8 -*-
import uuid
import json
import base64

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.qr_code_base.models.qr_code_base import generate_qr_code


class ReportTemplateODT(models.Model):
    _name = 'wg.report.template.odt'
    _description = 'Mẫu bản in (odt)'
    _order = 'create_date desc'


    @api.model
    def get_code(self, company_vat=None):
        code = company_vat + str(uuid.uuid4()).upper().replace('-', '')
        if self.sudo().search([('code', '=', code)], limit=1):
            return self.get_code()
        return code

    def name_get(self):
        return [(r.id, '{} - {}'.format(r.company_vat, r.company_name)) for r in self]

    @api.model
    def create(self, vals):
        vals['code'] = self.get_code(vals.get('company_vat'))
        return super(ReportTemplateODT, self).create(vals)

    code = fields.Char('Mã nhận dạng', index=1)
    type = fields.Selection([
        ('1', 'HĐĐT giá trị gia tăng'),
        ('2', 'HĐĐT bán hàng'),
        ('3', 'HĐĐT bán tài sản công'),
        ('4', 'HĐĐT bán hàng dự trữ quốc gia'),
        ('5', 'Tem/Vé/Thẻ/Phiếu thu/Chứng từ điện tử'),
        ('6', 'PXK kiêm VC nội bộ'),
        ], 'Loại hóa đơn', required=True)
    active = fields.Boolean('Có hiệu lực', default=True)
    company_vat = fields.Char('Mã số thuế', required=True)
    company_name = fields.Char('Tên công ty', required=True)
    company_address = fields.Char('Địa chỉ', required=True)

    inv_template_data = fields.Binary('Mẫu hóa đơn (odt)', required=True)
    inv_template_filename = fields.Char('Tên file mẫu', required=True)

    image_logo = fields.Binary('Logo công ty', required=True)
    image_background = fields.Binary('Ảnh nền', required=True)
    image_sign = fields.Binary('Khung chữ ký', required=True)
    sample_data = fields.Text('Dữ liệu mẫu')
    company_id = fields.Many2one('res.company', 'Công ty')

    def test_tmp_file(self):
        res = self.action_print(self.code, data=self.sample_data)
        return res

    def test_store_file(self):
        res = self.action_print(self.code, data=self.sample_data, storage=True)
        return res

    @api.model
    def action_print(self, template_code, data={}, storage=False):
        template = self.sudo().search([('code', '=', template_code)], limit=1)
        if not template:
            raise ValidationError('Không tìm thấy mẫu "{}"'.format(template_code))            
        try:
            data = json.loads(data)
            data.update({
                "CompanyImageLogo": self.image_logo and self.image_logo.decode('utf-8') or False,
                "CompanyImageBackground": self.image_background and self.image_background.decode('utf-8') or False,
                "CompanyImageSign": self.image_sign and self.image_sign.decode('utf-8') or False,
                "ImageQRCode": generate_qr_code('https://hoadonkhanhlinh.vn').decode('utf-8'),
            })
        except Exception as e:
            pass
        model_name = 'wg.report.pdf.tmp'
        if storage:
            model_name = 'wg.report.pdf.store'
        record = self.env[model_name].create({
            'template_id': template.id,
            'data': json.dumps(data),
            'company_vat': data.get('company_vat') or data.get('CompanyVat') or template.company_vat,
            'company_name': data.get('company_name') or data.get('CompanyName') or template.company_name,
            'name': data.get('print_report_name') or "'Không_xác_định.pdf'",
        })
        report_data = { 
            'type': 'ir.actions.report',
            'model': model_name,
            'report_type':'aeroo',
            'in_format':'oo-odt',
            'out_format': self.env['report.mimetypes'].search([('code','=', 'oo-pdf')], limit=1).id,
            'tml_source': 'database',
            'print_report_name': data.get('print_report_name') or "'Không_xác_định.pdf'",
            'report_data': template.inv_template_data,
        }
        report = self.env['ir.actions.report'].new(report_data)
        file_data, out_code, filename = report.with_context(self._context).render_aeroo([record.id], data={})
        attachment_id = record.attachment_id
        att_value = {
            'name': filename,
            'res_model': model_name,
            'res_id': record.id,
            'type': 'binary',
            'datas': base64.b64encode(file_data),
            'public': True,
        }
        if not attachment_id:
            attachment_id = self.env['ir.attachment'].create(att_value)
        else:
            attachment_id.write(att_value)
        record.write({
            'attachment_id': attachment_id.id,
        })
        return record.open_link_by_new_tab()
