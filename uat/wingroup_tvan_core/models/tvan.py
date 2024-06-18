# -*- coding: utf-8 -*-
from num2words import num2words
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.tools.misc import formatLang, format_date
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError


class HDDTAdjustDocumentInv(models.Model):
    _name = 'wg.hddt.adjust.document.inv'    
    _description = 'Biên bản điều chỉnh hóa đơn'


    company_vat = fields.Char('Mã số thuế', required=True)
    company_name = fields.Char('Tên đơn vị', required=True)
    serial = fields.Char('Ký hiệu', size=6, required=True)
    inv_number = fields.Char('Số hóa đơn', size=7, required=True)
    inv_date = fields.Date('Ngày hóa đơn', required=True)
    reason = fields.Text('Lý do điều chỉnh')
    before_content = fields.Text('Nội dung trước điều chỉnh')
    after_content = fields.Text('Hai bên thống nhất điều chỉnh:')



class TvanHistory(models.Model):
    _name = 'wg.tvan.history'    
    _description = 'Lịch sử truyền nhận'

    user_id = fields.Many2one('res.users', 'Tài khoản', required=True)
    date = fields.Datetime('Thời gian', required=True)
    type = fields.Selection([
        ('100', 'Đăng ký/ thay đổi HDDT'),
        ('101', 'Đăng ký/ thay đổi HDDT ủy nhiệm'),
        ('106', 'Đăng ký/ thay đổi HDDT từng lần phát sinh'),
        ('200', 'Hóa đơn có mã'),
        ('201', 'Hóa đơn có mã từng lần phát sinh'),
        ('203', 'Hóa đơn không mã'),
        ('206', 'Hóa đơn có mã khởi tạo từ máy tính tiền'),
        ('300', 'Thông báo HĐ sai sót'),
        ('303', 'Thông báo HĐ khởi tạo từ máy tính tiền sai sót'),
        ('400', 'Bảng tổng hợp'),
        ('500', 'Uỷ quyền cấp mã'),
        ], 'Loại thông điệp', default='200', required=True)
    ip = fields.Char('IP')
    inv_number = fields.Char('Số hóa đơn')
    state = fields.Selection([('0', 'Đã gửi') ,('1', 'Gửi lỗi'), ('2', 'Tạo mới')], 'Trạng thái', default='0')
    message = fields.Text('Thông báo')
    handle_msg = fields.Text('Cách khắc phục')

    def result_msg(self):
        pass

    def send_msg(self):
        pass
