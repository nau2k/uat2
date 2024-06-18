# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import json
import dicttoxml


class AccountInvoice(http.Controller):

    def tvan_check_account(self):
        try:
            Authorization = request.httprequest.headers.environ.get("HTTP_AUTHORIZATION")
            user = request.env['res.users'].sudo().get_api_rest_user(Authorization.replace('Bearer ', ''))
            if not user:
                return {
                    'status': 'Fail',
                    'message': 'Xác thực không chính xác',
                }
            else:
                return {
                    'status': 'Success',
                    'user_id': user.id,
                    'message': 'Xác thực thanh công',
                }
        except Exception as e:
            return {
                'status': 'Fail',
                'message': 'Đã có lỗi xảy ra',
            }

    def new_account_invoices(self, data_pos, user):
        partner = request.env['res.partner'].sudo().browse(data_pos['info'].get('partner_id'))
        inv_info = {
                'partner_type': '0' if partner.company_type == 'company' else '1',
                'partner_id': partner.id,
                'company_id': data_pos['info'].get('company_id'),
                'MKHang': partner.ref,
                'HVTNMHang': partner.buyer_name,
                'TenNMua': partner.name,
                'MSTNMua': partner.vat,
                'DChiNMua': partner.address2,
                'DCTDTuNMua': partner.email,
                'STKNHangNMua': partner.acc_bank_number,
                'TNHangNMua': partner.acc_bank_name,
                'email_cc': partner.email_cc,
                'SDThoaiNMua': partner.phone
            }
        account_inv = request.env['wg.account.invoice'].with_user(user).create(inv_info)
        return account_inv
    
    def new_account_invoice_line(self, data_pos, account_inv, user):
        inv_detail= []
        for line in data_pos['detail']:
            product = request.env['product.template'].sudo().browse(line.get('product_id'))
            inv_detail.append({
                "invoice_id": account_inv.id,
                "MHHDVu": product.default_code,
                "THHDVu":  product.name,
                "DVTinh": product.uom_name2,
                "DGia": product.list_price,
                "SLuong":line.get('SLuong'),
                "TLCKhau":line.get('TLCKhau'),
                "STCKhau":line.get('STCKhau'),
                "ThTien":line.get('ThTien'),
                "TSuat":line.get('TSuat'),
                "TThue":line.get('TThue'),
                "price_total":line.get('price_total'),
                # "TChat":line.get('TChat'),
                "company_id": line.get('company_id')
            })
        if len(inv_detail) > 0:
            account_inv_line = request.env['wg.account.invoice.line'].with_user(user).create(inv_detail)
            return account_inv_line

    @http.route('/api/new-account-invoice', auth='public', csrf=False, type='json')
    def new_account_inv(self, **data):
        try:
            auth_res = self.tvan_check_account()
            if auth_res.get('status') != 'Success':
                return auth_res
            user = request.env['res.users'].sudo().browse(auth_res.get('user_id'))
            data_pos = request.jsonrequest.get('data_pos', None)
            if not data_pos:
                return {
                    'status': 'Fail',
                    'message': 'Không có dữ liệu.',
                }
            account_inv = self.new_account_invoices(data_pos, user)
            account_inv_line = self.new_account_invoice_line(data_pos, account_inv, user)

            # compute tax
            if account_inv.line_ids:
                account_inv.with_user(user).compute_tax()
            return {
                'status': 'Success',
                'message': 'Hóa đơn đã được tạo thành công',
            }
        except Exception as e:
            return {
                'status': 'Fail',
                'message': 'Không tạo được HĐ',
                'log': e,
            }

    def tvan_check_account(self):
        try:
            Authorization = request.httprequest.headers.environ.get("HTTP_AUTHORIZATION")
            user = request.env['res.users'].sudo().get_api_rest_user(Authorization.replace('Bearer ', ''))
            if not user:
                return {
                    'status': 'Fail',
                    'message': 'Xác thực không chính xác',
                }
            else:
                return {
                    'status': 'Success',
                    'user_id': user.id,
                    'message': 'Xác thực thanh công',
                }
        except Exception as e:
            return {
                'status': 'Fail',
                'message': 'Đã có lỗi xảy ra',
            }
