# -*- coding: utf-8 -*-
import re
import uuid
import json

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class WGReportMixin(models.AbstractModel):
    _name = 'wg.report.pdf.mixin'
    _description = 'Cấu trúc lưu trữ hóa đơn'
    _order = 'create_date desc'

    @api.model
    def get_code(self, company_vat=None):
        code = self._name.split('.')[-1] + company_vat + str(uuid.uuid4()).upper().replace('-', '')
        if self.sudo().search([('code', '=', code)], limit=1):
            return self.get_code()
        return code

    @api.model
    def create(self, vals):
        vals['code'] = self.get_code(vals.get('company_vat'))
        return super(WGReportMixin, self).create(vals)

    def _compute_link(self):
        for record in self:
            record.link = self.get_view_link_by_code(record.code)

    template_id = fields.Many2one('wg.report.template.odt', 'Template', required=True, ondelete='cascade')
    name = fields.Char('Tên file', required=True)
    company_vat = fields.Char('Mã số thuế', related='', store=True)
    company_name = fields.Char('Tên công ty', related='', store=True)
    data = fields.Text('Data', default=str({}))
    code = fields.Char('Code', index=1, readonly=True)    
    attachment_id = fields.Many2one('ir.attachment', 'File hóa đơn')
    pdf_preview = fields.Binary('pdf_preview', related='attachment_id.datas')
    link = fields.Char('Link', compute='_compute_link')
    company_id = fields.Many2one('res.company', 'Công ty')

    def view_data(self):
        raise ValidationError(str(json.loads(self.data)))

    @api.model
    def get_view_link_by_code(self, code):
        record = self.sudo().search([('code', '=', code)], limit=1)
        return '{}/view/pdf/{}/{}'.format(
            self.env['ir.config_parameter'].sudo().get_param('web.base.url'), 
            record.attachment_id.id, 
        record.attachment_id.name)

    @api.model
    def get_download_link_by_code(self, code):
        return self.get_view_link_by_code() + '?download=1'

    def open_link_by_new_tab(self):
        return {
            'type': 'ir.actions.act_url',
            'url': self.get_view_link_by_code(self.code),
            'target': 'new',
        } 

    def tvan_prepare_json_data(self):
        try:
            res = json.loads(self.data)
            res.update({
                "CompanyImageLogo": self.template_id.image_logo and self.template_id.image_logo.decode('utf-8') or False,
                "CompanyImageBackground": self.template_id.image_background and self.template_id.image_background.decode('utf-8') or False,
                "CompanyImageSign": self.template_id.image_sign and self.template_id.image_sign.decode('utf-8') or False,
            })
            return res
        except Exception as e:
            raise e

class WGReportTMP(models.TransientModel):
    _name = 'wg.report.pdf.tmp'
    _inherit = 'wg.report.pdf.mixin'
    _description = 'File tạm'


class WGReportStore(models.Model):
    _name = 'wg.report.pdf.store'
    _inherit = 'wg.report.pdf.mixin'
    _description = 'Lưu trữ File'

