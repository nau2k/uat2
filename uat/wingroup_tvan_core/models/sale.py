# -*- coding: utf-8 -*-

import base64

from num2words import num2words
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.tools.misc import formatLang, format_date
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'


    @api.onchange('partner_id')
    def wg_onchange_partner_id(self):
        if self.partner_id:
            self.partner_vat = self.partner_id.vat
            self.partner_name = self.partner_id.name
            self.partner_address = self.partner_id.address2
            self.partner_phone = self.partner_id.phone
            self.partner_email = self.partner_id.email
        else:
            self.partner_vat = False
            self.partner_name = False
            self.partner_address = False
            self.partner_phone = False
            self.partner_email = False


    @api.onchange('inv_template_id')
    def wg_onchange_inv_template_id(self):
        if self.inv_template_id:
            self.inv_template_data = self.inv_template_id.data_file

    partner_vat = fields.Char('Mã số thuế', required=False)
    partner_name = fields.Char('Tên khách hàng', required=False)
    partner_address = fields.Char('Địa chỉ', required=False)
    partner_phone = fields.Char('Số điện thoại')
    partner_email = fields.Char('Email khách hàng')

    inv_template_id = fields.Many2one('wg.invoice.template', 'Mẫu hóa đơn có sẵn')
    inv_template_data = fields.Binary('Mẫu hóa đơn tùy chỉnh')
    inv_template_filename = fields.Char('Tên file')

    inv_registry_id = fields.Many2one('wg.inv.registry', 'Tờ khai sử dụng HĐĐT')
    inv_registry_state = fields.Selection(related='inv_registry_id.state')

    inv_registry_signed = fields.Boolean('Đã ký tờ khai', readonly=True)

    inv_cqt_id = fields.Many2one('wg.cqt', 'Cơ quan thuế')

    product_name = fields.Text('Dịch vụ', related='order_line.name')
    user_name = fields.Char('Nhân viên kinh doanh', related='user_id.name', store=True)

    inv_contract_id = fields.Many2one('wg.hddt.contract', 'Hợp đồng HĐĐT')
    contract_company_is_sign = fields.Boolean('Cty ký HĐ', related='inv_contract_id.company_is_sign')
    contract_partner_is_sign = fields.Boolean('KH ký HĐ', related='inv_contract_id.partner_is_sign')

    inv_sequence_id = fields.Many2one('wg.inv.sequence', 'Phát hành tài khoản')
    inv_name = fields.Char('Mẫu số')
    inv_serial = fields.Char('Ký hiệu')

    inv_signed = fields.Boolean('Đã xuất Hóa đơn')
    inv_done = fields.Boolean('Đã phát hành tài khoản')

    inv_serial_id = fields.Many2one('wg.inv.serial', 'Mẫu số hóa đơn')

    # inv_partner_name = fields.Char('Tên công ty')
    # inv_partner_name = fields.Char('Tên công ty')
    # inv_partner_name = fields.Char('Tên công ty')
    # inv_partner_name = fields.Char('Tên công ty')

    def tvan_view_registry(self):
        action = self.env["ir.actions.actions"]._for_xml_id('wingroup_tvan_core.action_inv_registry')
        action['views'] = [(False, 'form')]
        action['target'] = 'new'
        action['context'] = {
            'default_order_id': self.id,
            'default_partner_vat': self.partner_id.vat,
            'default_partner_name': self.partner_id.name,
            'default_partner_address': self.partner_id.address2,
            'default_email': self.partner_id.email,
            'default_partner_phone': self.partner_id.phone,
            'default_partner_contact_name': self.partner_id.buyer_name,
            'default_cqt_code': self.inv_cqt_id.code,
            'default_cqt_name': self.inv_cqt_id.name,
        }
        if self.inv_registry_id:
            action['res_id'] = self.inv_registry_id.id
        return action 

    def tvan_view_registry_tree(self):
        if self.inv_registry_id:
            return self.inv_registry_id.wg_open_digial_link_client()
        return self.tvan_view_registry()


    def tvan_view_contract(self):
        action = self.env["ir.actions.actions"]._for_xml_id('wingroup_tvan_core.action_hddt_contract')
        action['views'] = [(False, 'form')]
        action['target'] = 'new'
        action['context'] = {
            'default_order_id': self.id,
            'default_name': 'HD{}/{}'.format(str(self.date_order)[:10], self.partner_vat),
            'default_date': self.date_order,
            'default_company_name': self.company_id.name,
            'default_partner_name': self.partner_name,
        }
        if self.inv_contract_id:
            action['res_id'] = self.inv_contract_id.id
        return action 

    def tvan_view_invoice(self):
        action = self.env["ir.actions.actions"]._for_xml_id('sale.action_view_sale_advance_payment_inv')
        return action

    def tvan_view_sequence(self):
        action = self.env["ir.actions.actions"]._for_xml_id('wingroup_tvan_core.action_inv_sequence')
        action['views'] = [(False, 'form')]
        action['target'] = 'new'
        action['context'] = {
            'default_order_id': self.id,
            'default_create_date': self.date_order,
            'default_date': fields.Date.today(),
            'default_company_name': self.partner_name,
            'default_company_vat': self.partner_vat,
            'default_company_address': self.partner_address,
            'default_cqt_name': self.inv_cqt_id.name,
            'default_name': self.inv_name,
            'default_serial': self.inv_serial,
            'default_quantity': self.order_line.filtered(lambda r: r.product_id.hddt_ok).product_id.hddt_qty,
            'default_from_qty': 1,
            'default_to_qty': self.order_line.filtered(lambda r: r.product_id.hddt_ok).product_id.hddt_qty,
        }
        if self.inv_sequence_id:
            action['res_id'] = self.inv_sequence_id.id
        return action  

    def tvan_view_serial(self):
        action = self.env["ir.actions.actions"]._for_xml_id('wingroup_tvan_core.action_inv_serial')
        action['views'] = [(False, 'form')]
        action['target'] = 'new'
        action['context'] = {
            'default_order_id': self.id,
            # 'default_create_date': self.date_order,
            # 'default_date': fields.Date.today(),
            # 'default_company_name': self.partner_name,
            # 'default_company_vat': self.partner_vat,
            # 'default_company_address': self.partner_address,
            # 'default_cqt_name': self.inv_cqt_id.name,
            # 'default_name': self.inv_name,
            # 'default_serial': self.inv_serial,
            'default_quantity': self.order_line.filtered(lambda r: r.product_id.hddt_ok).product_id.hddt_qty,
            'default_from_qty': 1,
            'default_to_qty': self.order_line.filtered(lambda r: r.product_id.hddt_ok).product_id.hddt_qty,
        }
        if self.inv_serial_id:
            action['res_id'] = self.inv_serial_id.id
        return action  

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

    def t_get_product_line_datas(self):
        return [
            {
                "TChat": 1,
                "STT": 1,
                "MHHDVu": "SP01",
                "THHDVu": "Sản phẩm mẫu 02",
                "DVTinh": "Cái",
                "SLuong": 1,
                "DGia": 120000,
                "TLCKhau": 0,
                "STCKhau": 0,
                "ThTien": 120000,
                "TLCKhau": 0,
                "TSuat": "10%",
            },
            {
                "TChat": 1,
                "STT": 1,
                "MHHDVu": "SP02",
                "THHDVu": "Sản phẩm mẫu 02",
                "DVTinh": "Cái",
                "SLuong": 1,
                "DGia": 200000,
                "TLCKhau": 0,
                "STCKhau": 0,
                "ThTien": 200000,
                "TLCKhau": 0,
                "TSuat": "5%",
            },
        ]

    def t_get_tax_line_datas(self):
        return [
            {
                "TSuat": "10%",
                "ThTien": 12000,
                "TThue": 120000,
            },
            {
                "TSuat": "5%",
                "ThTien": 10000,
                "TThue": 200000,
            }
        ]

    def _compute_all_tvan_report_data(self):
        tax_totals_json = json.loads(self.tax_totals_json)
        tax_datas = tax_totals_json.get('groups_by_subtotal').get(list(tax_totals_json.get('groups_by_subtotal').keys())[0])
        for record in self:
            record.update({
                "t_KHMSHDon": record.inv_serial_id.name,
                "t_KHHDon": record.inv_serial_id.serial,
                "t_SHDon": "0000231",
                "t_NLap": str(fields.Date.today()),
                "t_SBKe": "",
                "t_NBKe": "",
                "t_DVTTe": "VND",
                "t_TGia": 1,
                "t_HTTToan": "Chuyển khoản/Tiền mặt",
                "t_TenNBan": record.partner_name,
                "t_MSTNBan": record.partner_vat,
                "t_DChiNban": record.partner_address,
                "t_SDThoaiNBan": record.partner_phone,
                "t_TenNMua": "NGUYÊN VĂN A",
                "t_MSTNMua": "0316633432",
                "t_DChiNMua": "16-18 Xuân Diệu, Phường 4, Quân Tân Bình, TP.HCM",
                "t_MKHang": "",
                "t_MCCQT": "M1-23-6QH6L-00000000000000008",
                "t_TgTCThue": 300000,
                "t_TgTThue": 22000,
                "t_TgTTTBSo": 322000,
                "t_TgTTTBChu": "Ba trăm hai mươi hai nghìn đồng."
            })        