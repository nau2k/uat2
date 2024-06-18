# -*- coding: utf-8 -*-

from odoo import fields, models, api
from dateutil.relativedelta import relativedelta
import requests
import json
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)



class InvoiceAdjustWiz(models.TransientModel):
    _name = 'tvan.inv.adjust.wiz'
    _description = 'Điều chỉnh hóa đơn'

    invoice_id = fields.Many2one('wg.account.invoice', required=True, string='Hóa đơn gốc')
    inv_serial_id = fields.Many2one('wg.inv.serial', 'Ký hiệu')
    SHDon = fields.Char('Số hóa đơn VAT')
    NLap = fields.Date('Ngày HĐ VAT')
    adjust_number = fields.Char('Số biên bản')
    HVTNMHang = fields.Char('Người mua hàng')

    TCHDon = fields.Selection([
        ('1', 'Điều chỉnh'),
        ('2', 'Thay thế'),
        # ('2', 'Điều chỉnh tăng'),
        # ('3', 'Điều chỉnh giảm'),
    ], string='Phân loại', default='1')

    partner_id = fields.Many2one('res.partner', 'Tìm khách hàng')
    TenNMua = fields.Char('Tên khách hàng')
    MSTNMua = fields.Char('Mã số thuế')
    DChiNMua = fields.Char('Địa chỉ')
    SDThoaiNMua = fields.Char('Số điện thoại')
    DCTDTuNMua = fields.Char('Email')

    product_name = fields.Char('Sản phẩm/dịch vụ')
    product_price = fields.Float('Giá xuất hóa đơn', digits=(20, 0))


    # @api.onchange('wg_partner_id')
    # def onchange_wg_partner_id(self):
    #     self.update({
    #         'wg_partner_name': self.wg_partner_id.name,
    #         'wg_partner_vat': self.wg_partner_id.vat,
    #         'wg_partner_address': self.wg_partner_id.address2,
    #         'wg_SDThoaiNMua': self.wg_partner_id.phone,
    #         'wg_DCTDTuNMua': self.wg_partner_id.email,
    #     })

   
    def action_confirm(self):
        new_inv = self.invoice_id.copy({
            'TCHDon': self.TCHDon,
            'adjust_for_id': self.invoice_id.id,
            'TenNMua': self.TenNMua,
            'MSTNMua': self.MSTNMua,
            'DChiNMua': self.DChiNMua,
            'SDThoaiNMua': self.SDThoaiNMua,
            'DCTDTuNMua': self.DCTDTuNMua,
            'SHDon': False,
        })
        if self.TCHDon == '1':
            self.invoice_id.write({'state': '4'})
        if self.TCHDon in '2':
            self.invoice_id.write({'state': '3'})
        action = self.env["ir.actions.actions"]._for_xml_id('wingroup_tvan_core.action_hddt_gtgt')
        action['res_id'] = new_inv.id
        # action['views'] = [(self.env.ref('wingroup_tvan_core.view_move_form_tvan').id, 'form')]
        action['views'] = [(False, 'form')]
        return action
