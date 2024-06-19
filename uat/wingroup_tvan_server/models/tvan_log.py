# -*- coding: utf-8 -*-
import base64
from num2words import num2words
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.tools.misc import formatLang, format_date
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError


class TvanLog(models.Model):
    _name = 'wg.tvan.log'    
    _description = 'Lịch sử truyền nhận'
    _order = 'date desc'

    user_id = fields.Many2one('res.users', 'Tài khoản', required=True)
    date = fields.Datetime('Thời gian', required=True, default=fields.Datetime.now)
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
    vat = fields.Char('Mã số thuế')
    company_name = fields.Char('Tên công ty')
    state = fields.Selection([('0', 'Đã gửi') ,('1', 'Gửi lỗi'), ('2', 'Tạo mới')], 'Trạng thái', default='2')
    message = fields.Text('Thông báo')
    handle_msg = fields.Text('Cách khắc phục')
    datas = fields.Binary('Thông điệp')

    TDiep = fields.Binary('Thông điệp TCT')

    MTDiep = fields.Char('Mã thông điệp', copy=False, index=True)
    tvan_config_id = fields.Many2one('wg.tvan.config', 'Môi trường')
    tvan_config_type = fields.Selection(related='tvan_config_id.type', string='Loại môi trường', store=True)

    # @api.model 
    # def create(self, vals):
    #     if not 'MTDiep' in vals:
    #         vals['MTDiep'] = 'G0307633556' + str(uuid.uuid4()).upper().replace('-', '')
    #     res = super(TvanLog, self).create(vals)
    #     return res

    def result_msg(self):
        pass

    def gen_xml_to_send_tct(self):
        DLieu = base64.b64decode(self.datas).decode('utf-8')
        xml_data = self.tvan_config_id.tct_template_id.xml_data
        res = xml_data.format(MTDiep=self.MTDiep, MLTDiep='', SLuong=1, MST=self.vat, DLieu=DLieu)
        self.write({
            'TDiep': base64.b64encode(res.encode('utf-8')) 
        })

    def send_msg(self):
        TDiep = base64.b64decode(self.TDiep).decode('utf-8')
        res = self.tvan_config_id.tvan_send_message(TDiep)
        # self.write({
        #     'message': str(res),
        # })
        return res