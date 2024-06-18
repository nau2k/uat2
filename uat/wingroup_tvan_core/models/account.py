# -*- coding: utf-8 -*-

import json
import base64
from xml.dom import minidom
from lxml import etree

from num2words import num2words
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.tools.misc import formatLang, format_date
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _name = 'account.move'
    _inherit = ['account.move', 'wg.sign.mixin']

    @api.model
    def default_get(self, default_fields):
        res = super(AccountMove, self).default_get(default_fields)
        default_sequence = self.env['wg.inv.serial'].search([], limit=1)
        if default_sequence:
            res['inv_serial_id'] = default_sequence.id
        return res

    @api.model
    def _wg_get_in_serial(self):
        return [(r['name'], r['name']) for r in self.env['wg.inv.sequence'].search([]).read(['name'])]

    @api.onchange('search_partner_id')
    def wg_onchange_search_partner_id(self):
        if self.search_partner_id:
            self.partner_id = self.search_partner_id
        self.search_partner_id = False


    @api.onchange('partner_id')
    def wg_onchange_partner_id(self):
        if self.partner_id:
            self.partner_vat = self.partner_id.vat
            self.partner_name = self.partner_id.name
            self.partner_address = self.partner_id.address2
            self.partner_vat = self.partner_id.vat
            self.buyer_name = self.partner_id.buyer_name
            self.acc_bank_number = self.partner_id.acc_bank_number
            self.acc_bank_name = self.partner_id.acc_bank_name
            self.partner_email = self.partner_id.email
            self.partner_email_cc = self.partner_id.email_cc
        else:
            self.partner_vat = False
            self.partner_name = False
            self.partner_address = False
            self.partner_vat = False
            self.buyer_name = False
            self.acc_bank_number = False
            self.acc_bank_name = False
            self.partner_email = False
            self.partner_email_cc = False


    @api.model 
    def create(self, vals):
        if 'partner_id' in vals:
            partner = self.env['res.partner'].sudo().browse(vals.get('partner_id'))
            if not vals.get('inv_serial_id'):
                default_sequence = self.env['wg.inv.serial'].search([], limit=1)
                vals['inv_serial_id'] = default_sequence.id
            if not vals.get('partner_vat'):
                vals['partner_vat'] = partner.vat
            if partner.vat and not 'buyer_name' in vals:
                vals['buyer_name'] = partner.name
            if not partner.vat and not 'partner_name' in vals:
                vals['partner_name'] = partner.name
            if not vals.get('partner_address'):
                vals['partner_address'] = partner.address2
            if not vals.get('partner_email'):
                vals['partner_email'] = partner.email
        return super(AccountMove, self).create(vals)


    @api.onchange('wg_extend_value')
    def wg_onchange_wg_extend_value(self):
        if self.wg_extend_value:
            self.partner_phone = self.partner_id and self.partner_id.phone or False
        else:
            self.partner_phone = False

    search_partner_id = fields.Many2one('res.partner', 'Tìm khách hàng')
    inv_serial_id = fields.Many2one('wg.inv.serial', 'Ký hiệu')
    inv_name = fields.Char(related='inv_serial_id.name')
    inv_serial = fields.Char(related='inv_serial_id.serial')

    inv_date = fields.Date('Ngày tạo lập', default=fields.Date.today, copy=False)
    inv_number = fields.Char('Số hoá đơn', readonly=False, copy=False)

    partner_vat = fields.Char('Mã số thuế', required=False)
    partner_name = fields.Char('Đơn vị mua', required=False)
    partner_address = fields.Char('Địa chỉ', required=False)
    partner_email = fields.Char('Email khách hàng')
    partner_email_cc = fields.Char('Danh sách cc')

    buyer_name = fields.Char('Tên người mua', required=False)
    acc_bank_number = fields.Char('Số tài khoản', required=False)
    acc_bank_name = fields.Char('Tên ngân hàng', required=False)
    
    wg_state = fields.Selection([
        ('0', 'Hóa đơn vừa khởi tạo'),
        ('1', 'Hóa đơn có đủ chữ ký'),
        ('3', 'Hóa đơn sai sót bị thay thế'),
        ('4', 'Hóa đơn sai sót bị điều chỉnh'),
        ('5', 'Hoá đơn huỷ'),
    ], string='Trạng thái phát hành hóa đơn', default='0', tracking=3, copy=False)
    
    wg_payment_method = fields.Selection([
        ('1', 'Tiền mặt'),
        ('2', 'Chuyển khoản'),
        ('3', 'Tiền mặt/Chuyển khoản'),
        ('4', 'Đối trừ công nợ'),
        ('5', 'Không thu tiền'),
        ('9', 'Khác'),
        ], string='Hình thức thanh toán', default='3', required=True)
    currency_rate = fields.Float('Tỉ giá', default=1)

    wg_extend_value = fields.Boolean('Thông tin bổ sung')
    wg_report_number = fields.Char('Số bản kê')
    wg_report_date = fields.Date('Ngày bản kê')
    partner_phone = fields.Char('Số điện thoại', size=20)
    wg_note = fields.Char('Ghi chú')

    attachment_id = fields.Many2one('ir.attachment', 'File hoá đơn', copy=False)
    MCCQT = fields.Char('Mã CQT', readonly=True)


    adjust_type = fields.Selection([
        ('0', 'Hóa đơn gốc'),
        ('1', 'Điều chỉnh thông tin'),
        ('2', 'Điều chỉnh tăng'),
        ('3', 'Điều chỉnh giảm'),
        ('4', 'Thay thế'),
    ], string='Là hóa đơn', default='0')

    adjust_for_id = fields.Many2one('account.move', 'HĐ gốc')

    # wg_invoice_link = fields.Char('Link hóa đơn', readonly=True)
    # # wininvoice_account_id = fields.Many2one('wininvoice.account', 'Tài khoản WinInvoice')
    # wininvoice_oid = fields.Char('WinInvoice OID', readonly=False, tracking=3)
    # wininvoice_ref = fields.Char('WinInvoice ref', readonly=False, tracking=3)
    # wininvoice_number = fields.Char('Số hóa đơn VAT', readonly=False, tracking=3)
    # wininvoice_msg = fields.Text('WinInvoice message', readonly=False)

    def wg_create_partner(self):
        action = self.env["ir.actions.actions"]._for_xml_id('wingroup_tvan_core.action_create_partner')
        action['views'] = [(False, 'form')]
        action['target'] = 'new'
        action['context'] = {
            'default_vat': self.partner_vat,
            'default_name': self.partner_name,
            'default_vat': self.partner_vat,
            'default_address2': self.partner_address,
            'default_email': self.partner_email,
            'default_email_cc': self.partner_email_cc,
            'default_buyer_name': self.buyer_name,
            'default_acc_bank_number': self.acc_bank_number,
            'default_acc_bank_name': self.acc_bank_name,
            'default_phone': self.partner_phone,
        }
        return action 

    def wg_find_partner(self):
        pass

    def wg_save_report_file(self):
        report_xml_id = 'wingroup_tvan_core.invoice_vat_pdf' 
        self = self.sudo()
        attachment = self.attachment_id
        docids = [self.id]
        data = {}
        report = self.env.ref(report_xml_id)
        file_data, out_code, filename = report.with_context(self._context).render_aeroo(docids, data=data)
        if not attachment:
            attachment = self.env['ir.attachment'].create({
                'name': filename,
                'res_model': self._name,
                'res_id': self.id,
                'type': 'binary',
            })
            self.write({'attachment_id': attachment.id})
        attachment.write({
            'name': filename,
            'datas': base64.b64encode(file_data),
            'public': True,
        })
        return attachment

    # Xem hoá đơn
    def wg_view(self):
        try:
            attachment = self.wg_save_report_file()
        except Exception as e:
            try:
                attachment = self.wg_save_report_file()
            except Exception as e:
                raise e
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{}/{}'.format(attachment.id, attachment.name),
            'target': 'new',
        } 

    def wg_edit(self):
        pass

    def wg_get_id_content_to_sign(self):
        return ['DLHDon']

    def wg_get_tag_to_sign(self):
        return ['DSCKS', 'NBan']

    def wg_sign_invoice_vat(self):
        return self.wg_open_digial_link_backend()

    def wg_send(self):
        pass

    def wg_handle(self):
        action = self.env["ir.actions.actions"]._for_xml_id('wingroup_tvan_core.action_adjust_invoice')
        action['views'] = [(False, 'form')]
        action['target'] = 'new'
        action['context'] = {
            'default_move_id': self.id,
            'default_inv_serial_id': self.inv_serial_id.id,
            'default_inv_number': self.inv_number,
            'default_invoice_date': self.invoice_date,
            'default_partner_vat': self.partner_vat,
            'default_partner_name': self.partner_name,
            'default_partner_address': self.partner_address,
            'default_partner_email': self.partner_email,
            'default_partner_phone': self.partner_phone,
            'default_buyer_name': self.buyer_name,
            # 'default_partner_email_cc': self.partner_email_cc,
            # 'default_partner_acc_bank_number': self.acc_bank_number,
            # 'default_partner_acc_bank_name': self.acc_bank_name,
        }
        return action 

    def set_xml_data(self):
        attachment_origin_id = self.attachment_origin_id
        att_value = {
            'name': 'Hóa đơn {}.xml'.format(self.partner_vat),
            'res_model': self._name,
            'res_id': self.id,
            'type': 'binary',
            # 'datas': base64.b64encode(self.tvan_init_invoice_data().encode('utf-8')),
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

    def tvan_prepare_json_data(self):
        tax_totals_json = json.loads(self.tax_totals_json)
        groups_by_subtotal = tax_totals_json.get('groups_by_subtotal') and \
            tax_totals_json.get('groups_by_subtotal').get(list(tax_totals_json.get('groups_by_subtotal').keys())[0]) or []
        tax_datas = groups_by_subtotal
        res = {
            "KHMSHDon": self.inv_serial_id.name,
            "KHHDon": self.inv_serial_id.serial,
            "SHDon": self.inv_number,
            "NLap": str(self.invoice_date),
            "SBKe": self.wg_report_number or "",
            "NBKe": self.wg_report_date and str(self.wg_report_date) or "",
            "DVTTe": self.currency_id.name,
            "TGia": self.currency_rate,
            "HTTToan": str(self.tvan_get_selection_label("wg_payment_method")),
            "TenNBan": self.company_id.name,
            "MSTNBan": self.company_id.vat,
            "DChiNban": self.company_id.partner_id.address2,
            "SDThoaiNBan": self.company_id.phone or "",
            "TenNMua": self.partner_name,
            "MSTNMua": self.partner_vat,
            "DChiNMua": self.partner_address,
            "MKHang": self.partner_id.ref or "",
            "body_data": [
                {
                    "TChat": line.wg_type,
                    "STT": index+1,
                    "MHHDVu": line.product_code or "",
                    "THHDVu": line.name,
                    "DVTinh": line.uom_name2 or "",
                    "SLuong": line.quantity,
                    "DGia": line.price_unit,
                    "TLCKhau": 0,
                    "STCKhau": 0,
                    "ThTien": line.price_subtotal,
                    "TLCKhau": 0,
                    "TSuat": line.wg_tax_id.name or "KCT",
                } for index, line in enumerate(self.invoice_line_ids)
            ],
            "footer_data": [
                {
                    "TSuat": line.get("tax_group_name").replace("Thuế GTGT ", ""),
                    "ThTien": line.get("tax_group_base_amount"),
                    "TThue": line.get("tax_group_amount")
                } for line in tax_datas
            ],
            "MCCQT": self.MCCQT,
            "TgTCThue": self.amount_untaxed,
            "TgTThue": self.amount_tax,
            "TgTTTBSo": self.amount_total,
            "TgTTTBChu": ""
        }
        return res

    def tvan_init_invoice_data(self):
        data = self.tvan_prepare_json_data()
        route_url = self.env['ir.config_parameter'].sudo().get_param('tvan.route_inv')
        res = self.tvan_call_api(route_url, data)        
        return res.get('data', False)

    # TODO: Gọi API Tvan truyền dữ liệu
    def wg_send_tct(self):
        # TODO: Gọi API Tvan truyền dữ liệu
        if not self.MTDiep:
            route_url = self.env['ir.config_parameter'].sudo().get_param('tvan.RequestMTDiep')
            res = self.tvan_call_api(route_url, {})        
            self.MTDiep = res.get('data', False)
        data = {
            'type': '200',
            'inv_number': self.inv_name,
            'MTDiep': self.MTDiep,
            'datas': self.attachment_sign_id.datas.decode('utf-8')
        }
        res = self.tvan_call_api(self.env['ir.config_parameter'].sudo().get_param('tvan.SendMessage'), data)        
        if res.get('status') == 'fail':
            raise ValidationError(res.get('message'))
        self.wg_state  = '1'


    t_KHMSHDon = fields.Char(compute='_compute_all_tvan_report_data')
    t_KHHDon = fields.Char(compute='_compute_all_tvan_report_data')
    t_SHDon = fields.Char(compute='_compute_all_tvan_report_data')
    t_NLap = fields.Char(compute='_compute_all_tvan_report_data')
    t_SBKe = fields.Char(compute='_compute_all_tvan_report_data')
    t_NBKe = fields.Char(compute='_compute_all_tvan_report_data')
    t_DVTTe = fields.Char(compute='_compute_all_tvan_report_data')
    t_TGia = fields.Char(compute='_compute_all_tvan_report_data')
    t_HTTToan = fields.Char(compute='_compute_all_tvan_report_data')
    t_TenNBan = fields.Char(compute='_compute_all_tvan_report_data')
    t_MSTNBan = fields.Char(compute='_compute_all_tvan_report_data')
    t_DChiNban = fields.Char(compute='_compute_all_tvan_report_data')
    t_SDThoaiNBan = fields.Char(compute='_compute_all_tvan_report_data')
    t_TenNMua = fields.Char(compute='_compute_all_tvan_report_data')
    t_MSTNMua = fields.Char(compute='_compute_all_tvan_report_data')
    t_DChiNMua = fields.Char(compute='_compute_all_tvan_report_data')
    t_MKHang = fields.Char(compute='_compute_all_tvan_report_data')
    
    t_MCCQT = fields.Char(compute='_compute_all_tvan_report_data')
    t_TgTCThue = fields.Char(compute='_compute_all_tvan_report_data')
    t_TgTThue = fields.Char(compute='_compute_all_tvan_report_data')
    t_TgTTTBSo = fields.Char(compute='_compute_all_tvan_report_data')
    t_TgTTTBChu = fields.Char(compute='_compute_all_tvan_report_data')
    t_KHMSHDon = fields.Char(compute='_compute_all_tvan_report_data')

    # t_line_ids = fields.Manymany('account.invoice.line', compute='_compute_all_tvan_report_data_line')
    
    def t_get_product_line_datas(self):
        return [
            {
                "TChat": line.wg_type,
                "STT": index+1,
                "MHHDVu": line.product_code or "",
                "THHDVu": line.name,
                "DVTinh": line.uom_name2 or "",
                "SLuong": line.quantity,
                "DGia": line.price_unit,
                "TLCKhau": 0,
                "STCKhau": 0,
                "ThTien": line.price_subtotal,
                "TLCKhau": 0,
                "TSuat": line.wg_tax_id.name or "KCT",
            } for index, line in enumerate(self.invoice_line_ids)
        ]

    def t_get_tax_line_datas(self):
        tax_totals_json = json.loads(self.tax_totals_json)
        tax_datas = tax_totals_json.get('groups_by_subtotal').get(list(tax_totals_json.get('groups_by_subtotal').keys())[0])
        return [
            {
                "TSuat": line.get("tax_group_name").replace("Thuế GTGT ", ""),
                "ThTien": line.get("tax_group_base_amount"),
                "TThue": line.get("tax_group_amount")
            } for line in tax_datas
        ]

    def _compute_all_tvan_report_data(self):
        for record in self:
            record.update({
                "t_KHMSHDon": record.inv_serial_id.name,
                "t_KHHDon": record.inv_serial_id.serial,
                "t_SHDon": record.inv_number,
                "t_NLap": str(record.invoice_date),
                "t_SBKe": record.wg_report_number or "",
                "t_NBKe": record.wg_report_date and str(record.wg_report_date) or "",
                "t_DVTTe": record.currency_id.name,
                "t_TGia": record.currency_rate,
                "t_HTTToan": str(record.tvan_get_selection_label("wg_payment_method")),
                "t_TenNBan": record.company_id.name,
                "t_MSTNBan": record.company_id.vat,
                "t_DChiNban": record.company_id.partner_id.address2,
                "t_SDThoaiNBan": record.company_id.phone or "",
                "t_TenNMua": record.partner_name,
                "t_MSTNMua": record.partner_vat,
                "t_DChiNMua": record.partner_address,
                "t_MKHang": record.partner_id.ref or "",

                "t_MCCQT": record.MCCQT,
                "t_TgTCThue": record.amount_untaxed,
                "t_TgTThue": record.amount_tax,
                "t_TgTTTBSo": record.amount_total,
                "t_TgTTTBChu": "Đây là số tiền được ghi bằng chữ."
            })


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'        

    @api.onchange('product_id')
    def wg_onchange_product_id(self):
        if self.product_id:
            self.product_code = self.product_id.barcode
        else:
            self.product_code = False

    @api.onchange('product_uom_id')
    def wg_onchange_product_uom_id(self):
        if self.product_uom_id:
            self.uom_name2 = self.product_uom_id.name
        else:
            self.uom_name2 = False

    @api.onchange('wg_tax_id')
    def wg_onchange_tax_id(self):
        if self.wg_tax_id:
            self.tax_ids = self.wg_tax_id
        else:
            self.tax_ids = False

    wg_type = fields.Selection([
        ('1', 'HH, DV'),
        ('2', 'KM'),
        ('3', 'CK'),
        ('4', 'Ghi chú'),
        ], 'Tính chất', default='1')
    product_code = fields.Char('Mã HH/DV')
    uom_name2 = fields.Char('Đơn vị tính')
    wg_tax_id = fields.Many2one('account.tax', 'Thuế')


