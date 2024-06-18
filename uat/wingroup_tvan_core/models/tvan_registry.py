# -*- coding: utf-8 -*-
import base64
from xml.dom import minidom
from lxml import etree
import uuid
import json
import requests
from requests.structures import CaseInsensitiveDict

from num2words import num2words
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.tools.misc import formatLang, format_date
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError

registry_state = {
    '0': 'Tờ khai được khởi tạo',
    '1': 'Gủi thành công',
    '2': 'Gửi lỗi',
    '3': 'Đã tiếp nhận',
    '4': 'Không tiếp nhận',
    '5': 'Được chấp nhận',
    '6': 'Không chấp nhận',
}


class InvoiceRegistry(models.Model):
    _name = 'wg.inv.registry'
    _inherit = ['wg.sign.mixin', 'mail.thread']
    _description = 'Tờ khai Đăng ký sử dụng hóa đơn điện tử'
    _table = 'wg_inv_registry'
    _order = 'date desc'
    # _sequence = 'wg_sign_mixin_id_seq'


    def tvan_get_filename(self):
        return 'TK_HDDT_{}_{}.xml'.format(
            self.partner_vat,
            str(self.date)[:10].replace('-', '_'),
        )

    def set_xml_data(self):
        attachment_origin_id = self.attachment_origin_id
        att_value = {
            'name': self.tvan_get_filename(),
            'res_model': self._name,
            'res_id': self.id,
            'type': 'binary',
            # 'datas': base64.b64encode(self.init_01_data().encode('utf-8')),
            'datas': self.init_01_data(),
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
    def create(self, vals):
        res = super(InvoiceRegistry, self).create(vals)
        if 'order_id' in vals:
            res.order_id.write({
                'inv_registry_id': res.id,
            })
            # self.set_xml_data()
            
        return res

    order_id = fields.Many2one('sale.order', 'Đơn hàng')
    type = fields.Selection([
        ('1', 'Đăng ký'), 
        ('2', 'Thay đổi')], 'Hình thức', required=True, default='1', readonly=True, states={'0': [('readonly', False)]})
    document_type = fields.Selection([
        ('1', 'Đăng ký sử dụng HDDT'), 
        ('2', 'Đăng ký hóa đơn ủy nhiệm'),
        ('3', 'Đăng ký hóa đơn có mã từng lần phát sinh'),
    ], 'Loại tờ khai', required=True, default='1', readonly=True, states={'0': [('readonly', False)]})
    date = fields.Datetime('Ngày lập', default=fields.Datetime.now, required=True, readonly=True, states={'0': [('readonly', False)]})
    email = fields.Char('Email', readonly=True, states={'0': [('readonly', False)]})
    company_id = fields.Many2one('res.company', string='Công ty', readonly=True)
    state = fields.Selection([
        ('0', 'Tờ khai được khởi tạo'), 
        ('1', 'Gủi thành công'),
        ('2', 'Gửi lỗi'),
        ('3', 'Đã tiếp nhận'),
        ('4', 'Không tiếp nhận'),
        ('5', 'Được chấp nhận'),
        ('6', 'Không chấp nhận'),
    ], 'Trạng thái', required=True, default='0')
    message = fields.Char('Thông báo', readonly=True, states={'0': [('readonly', False)]})
    cks_ids = fields.Many2many('wg.cks.info', 'wg_inv_registry_cks_info_rel', 'registry_id', 'cks_id', 'Chữ ký số',
        readonly=True, states={'0': [('readonly', False)]})

    document_name = fields.Char('Mẫu số tờ khai', default='01/ĐKTĐ-HĐĐT',
        readonly=True, states={'0': [('readonly', False)]})

    partner_vat = fields.Char('Mã số thuế', required=False,
        readonly=True, states={'0': [('readonly', False)]})
    partner_name = fields.Char('Tên người nộp thuế', required=False,
        readonly=True, states={'0': [('readonly', False)]})
    partner_address = fields.Char('Địa chỉ liên hệ', required=False,
        readonly=True, states={'0': [('readonly', False)]})
    partner_phone = fields.Char('Số điện thoại',
        readonly=True, states={'0': [('readonly', False)]})
    partner_contact_name = fields.Char('Người liên hệ',
        readonly=True, states={'0': [('readonly', False)]})

    cqt_code = fields.Char('Mã CQT', readonly=True, states={'0': [('readonly', False)]})
    cqt_name = fields.Char('Tên CQT', readonly=True, states={'0': [('readonly', False)]})    

    NNTDBKKhan = fields.Boolean('NNT địa bàn khó khăn (Doanh nghiệp nhỏ và vừa, hợp tác xã, hộ, \
        cá nhân kinh doanh tại địa bàn có điều kiện kinh tế xã hội khó khăn, địa bàn có điều kiện \
        kinh tế xã hội đặc biệt khó khăn)', readonly=True, states={'0': [('readonly', False)]})
    NNTKTDNUBND = fields.Boolean('NNT khác theo đề nghị UBND (Doanh nghiệp nhỏ và vừa khác theo \
        đề nghị của Ủy ban nhân dân tỉnh, thành phố trực thuộc trung ương gửi Bộ Tài chính trừ \
        doanh nghiệp hoạt động tại các khu kinh tế, khu công nghiệp, khu công nghệ cao)', 
        readonly=True, states={'0': [('readonly', False)]})
    CDLTTDCQT = fields.Boolean('Chuyển dữ liệu trực tiếp đến CQT (Chuyển dữ liệu hóa đơn điện tử \
        trực tiếp đến cơ quan thuế (điểm b1, khoản 3, Điều 22 của Nghị định 123/2020/NĐ-CP))',
        readonly=True, states={'0': [('readonly', False)]})
    CDLQTCTN = fields.Boolean('Chuyển dữ liệu qua TCTN (Thông qua tổ chức cung cấp dịch vụ hóa đơn \
        điện tử (điểm b2, khoản 3, Điều 22 của Nghị định 123/2020/NĐ-CP))', 
        readonly=True, states={'0': [('readonly', False)]})

    CDDu = fields.Boolean('Chuyển đầy đủ nội dung từng hóa đơn', default=1, 
        help='Chuyển đầy đủ nội dung từng hóa đơn', readonly=True, states={'0': [('readonly', False)]})
    CBTHop = fields.Boolean('Chuyển bảng tổng hợp', 
        help='Chuyển theo bảng tổng hợp dữ liệu hóa đơn điện tử (điểm a1, khoản 3, Điều 22 của Nghị định \
        123/2020/NĐ-CP)', readonly=True, states={'0': [('readonly', False)]})

    HDGTGT = fields.Boolean('Hóa đơn GTGT', default=1, readonly=True, states={'0': [('readonly', False)]})
    HDBHang = fields.Boolean('Hóa đơn bán hàng', readonly=True, states={'0': [('readonly', False)]})
    HDBTSCong = fields.Boolean('Hóa đơn bán tài sản công', readonly=True, states={'0': [('readonly', False)]})
    HDBHDTQGia = fields.Boolean('Hóa đơn bán hàng dự trữ quốc gia', readonly=True, states={'0': [('readonly', False)]})
    HDKhac = fields.Boolean('Hóa đơn khác', readonly=True, states={'0': [('readonly', False)]})
    CTu = fields.Boolean('Chứng từ điện tử được sử dụng và quản lý như hóa đơn', readonly=True, states={'0': [('readonly', False)]})

    CMa = fields.Boolean('Có mã của cơ quan thuế', default=1, readonly=True, states={'0': [('readonly', False)]})
    KCMa = fields.Boolean('Không có mã của cơ quan thuế', readonly=True, states={'0': [('readonly', False)]})
    CMTMTTien = fields.Boolean('HĐ có mã khởi tạo từ máy tính tiền', readonly=True, states={'0': [('readonly', False)]})

    using_cts_hsm = fields.Boolean('Sử dụng CTS HSM', related='company_id.using_cts_hsm', store=True)


    @api.onchange('CMa')
    def onchange_CMa(self):
        if self.CMa:
            self.CDDu = True
            self.CBTHop = False

    @api.onchange('CMTMTTien')
    def onchange_CMTMTTien(self):
        if self.CMTMTTien:
            self.CDDu = True
            self.CBTHop = False            
            self.HDBTSCong = False            
            self.HDBHDTQGia = False            
            self.CTu = False            


    def wg_delete_signed_file(self):
        res = super(InvoiceRegistry, self).wg_delete_signed_file()
        if self.order_id:
            self.order_id.write({
                'inv_registry_signed': False,
            })
        return res

    def wg_get_sign_model_inherit(self):
        res = super(InvoiceRegistry, self).wg_get_sign_model_inherit()
        res.append(self._name)
        return res

    def wg_send_tct(self):
        # TODO: Gọi API Tvan truyền dữ liệu
        if not self.MTDiep:
            route_url = self.env['ir.config_parameter'].sudo().get_param('tvan.RequestMTDiep')
            print ('route_url', route_url)
            res = self.tvan_call_api(route_url, {})        
            self.MTDiep = res.get('data', False)
        data = {
            'type': '100',
            'inv_number': 'x',
            'vat': self.company_id.vat,
            'company_name': self.company_id.name,
            'MTDiep': self.MTDiep,
            'datas': self.attachment_sign_id.datas.decode('utf-8')
        }
        res = self.tvan_call_api(self.env['ir.config_parameter'].sudo().get_param('tvan.SendMessage'), data)        
        if res.get('status') == 'fail':
            raise ValidationError(res.get('message'))
        self.state  = '1'

    def wg_get_html_data_for_registry(self):
        tr_template = """
            <tr>
                <td style="width: 50px;text-align:center">{}</td>
                <td style="width: 200px;text-align:center">{}</td>
                <td style="width: 200px;text-align:center">{}</td>
                <td style="width: 200px;text-align:center">{}</td>
                <td style="width: 200px;text-align:center">{}</td>
                <td style="width: 200px;text-align:center">Thêm mới</td>
            </tr>
        """
        body_data = ' '.join(
            tr_template.format(index+1, line.issuer, line.serial, line.valid_from, line.valid_to) for index, line in enumerate(self.cks_ids))
        res = """
            <table class="table table-bordered table-hover" style="margin-bottom: 20px">
                <thead>
                    <tr>
                        <th style="width: 50px; text-align: left;">Tên</th>
                        <th style="width: 100px; text-align: left;">Giá trị</th>
                    </tr>
                </thead>
                <tbody id="msgPackageResultModalBody">
                    <tr>
                        <td style="width: 50px ;text-align:left"> Loại </td> 
                        <td style="width: 100px;text-align:left">Đăng ký/Thay đổi thông tin sử dụng hóa đơn điện tử</td> 
                    </tr>
                    <tr>
                        <td style="width: 50px ;text-align:left"> Mẫu số tờ khai </td> 
                        <td style="width: 100px;text-align:left">{document_name}</td> 
                    </tr>
                    <tr> 
                        <td style="width: 50px ;text-align:left"> Loại thông điệp </td> 
                        <td style="width: 100px;text-align:left">Đăng ký</td> 
                    </tr>
                    <tr> 
                        <td style="width: 50px ;text-align:left"> Mã số thuế </td> 
                        <td style="width: 100px;text-align:left">{partner_vat}</td> 
                    </tr>
                    <tr> 
                        <td style="width: 50px ;text-align:left"> Tên NNT </td> 
                        <td style="width: 100px;text-align:left">{partner_name}</td> 
                    </tr>
                    <tr> 
                        <td style="width: 50px ;text-align:left"> Tên CQT </td> 
                        <td style="width: 100px;text-align:left">{cqt_name}</td> 
                        </tr>
                    <tr> 
                        <td style="width: 50px ;text-align:left"> Mã CQT </td> 
                        <td style="width: 100px;text-align:left">{cqt_code}</td> 
                    </tr>
                    <tr> 
                        <td style="width: 50px ;text-align:left"> Người liên hệ </td> 
                        <td style="width: 100px;text-align:left">{partner_contact_name}</td> 
                    </tr>
                        <tr> <td style="width: 50px ;text-align:left"> Địa chỉ liên hệ </td> 
                        <td style="width: 100px;text-align:left">{partner_address}</td> 
                    </tr>
                    <tr> 
                        <td style="width: 50px ;text-align:left"> Email </td> 
                        <td style="width: 100px;text-align:left">{partner_email}</td> 
                    </tr>
                    <tr>
                        <td style="width: 50px ;text-align:left"> Điện thoại </td> 
                        <td style="width: 100px;text-align:left">{partner_phone}</td> 
                    </tr>
                    <tr> 
                        <td style="width: 50px ;text-align:left"> Nơi lập </td> 
                        <td style="width: 100px;text-align:left">Hồ Chí Minh</td> 
                    </tr>
                    <tr> 
                        <td style="width: 50px ;text-align:left"> Ngày lập </td> 
                        <td style="width: 100px;text-align:left">{date}</td> 
                    </tr>
                    <tr> 
                        <td style="width: 50px ;text-align:left"> Trạng thái </td> 
                        <td style="width: 100px;text-align:left">{state}</td> 
                    </tr>
                    <tr> 
                        <td style="width: 50px ;text-align:left"> Áp dụng hóa đơn </td> 
                        <td style="width: 100px;text-align:left">Có mã</td> 
                    </tr>
                    <tr>
                        <td style="width: 50px ;text-align:left"> Chuyển đầy đủ </td>
                        <td style="width: 100px;text-align:left"> Có </td> 
                    </tr>
                    <tr> 
                        <td style="width: 50px ;text-align:left"> Sử dụng Hóa đơn GTGT </td> 
                        <td style="width: 100px;text-align:left"> Có </td> 
                    </tr>
                    <tr> 
                        <td colspan="2"> <strong>Danh sách chữ ký số</strong>
                            <table class="table table-bordered table-hover" style="margin - bottom: 20px"> 
                                <tbody>
                                    <tr>
                                        <th rowspan="2" style="width: 50px; text-align: center;">STT</th>
                                        <th rowspan="2" style="width: 50px; text-align: center;">Tên tổ chức</th>
                                        <th rowspan="2" style="width: 50px; text-align: center;">Số Seri</th>
                                        <th colspan="2" style="width: 50px; text-align: center;">Thời gian sử dụng</th>
                                        <th rowspan="2" style="width: 50px; text-align: center;">Hình thức đăng ký</th>
                                    </tr>
                                    <tr>
                                        <th style="width: 50px; text-align: center;">Từ ngày</th>
                                        <th style="width: 50px; text-align: center;">Đến ngày</th>
                                    </tr>
                                    {body_data}
                                </tbody>
                            </table>
                        </td> 
                    </tr>
                </tbody>
            </table>

        """.format(
            document_name=self.document_name,
            partner_vat=self.partner_vat,
            partner_name=self.partner_name,
            partner_phone=self.partner_phone,
            partner_address=self.partner_address,
            partner_email=self.email,
            cqt_name=self.cqt_name,
            cqt_code=self.cqt_code,
            date=str(self.date)[:10],
            state=registry_state.get(self.state),
            partner_contact_name=self.partner_contact_name,
            body_data=body_data,
        )
        return res

    def wg_get_data_html_from_file(self, show_signed_file):
        return self.wg_get_html_data_for_registry()

    # Dữ liệu dể render trang client
    def wg_get_portal_sign_data(self):
        res = super(InvoiceRegistry, self).wg_get_portal_sign_data()
        abc = self.wg_get_html_data_for_registry()
        res['html_data'] = abc
        res['cks_info'] = 'YES' if self.cks_ids else 'NO'
        return res

    # Xử lý data sau khi sign
    def wg_handle_signed_data(self, data):
        # Case: Thêm CKS vào 
        if data.get('add_cks') == '1':            
            CksObj = self.env['wg.cks.info']
            old_cks = CksObj.search([('serial', '=', data.get('serial'))], limit=1)
            issuer = ''
            for ncc in data.get('issuer').split(','):
                if 'CN=' in ncc:
                    issuer = ncc.replace('CN=', '')
            cks_value = {
                'serial': data.get('serial'),
                'issuer': issuer,
                'subject': data.get('subject'),
                'valid_from': data.get('valid_from'),
                'valid_to': data.get('valid_to'),
                'registry_ids': [(4, self.id)],
            }
            if not old_cks:
                old_cks = CksObj.create(cks_value)
            else:
                old_cks.write(cks_value)
            self.set_xml_data()
        else:
            res = super(InvoiceRegistry, self).wg_handle_signed_data(data)
            if self.order_id:
                self.order_id.write({'inv_registry_signed': True})
            return res

    
    def tvan_prepare_json_data(self):
        data = {
            'MST': self.partner_vat,
            'MSo': self.document_name,
            'HThuc': self.type,
            'TNNT': self.partner_name,
            'CQTQLy': self.cqt_name,
            'MCQTQLy': self.cqt_code,
            'NLHe': self.partner_contact_name,
            'DCLHe': self.partner_address,
            'DTLHe': self.partner_phone,
            'DCTDTu': self.email,
            'DDanh': 'TP Hồ Chí Minh',
            'NLap': str(self.date)[:10],
            'CMa': self.CMa and 1 or 0,
            'KCMa': self.KCMa and 1 or 0,
            'CMTMTTien': self.CMTMTTien and '''<CMTMTTien>1</CMTMTTien>''' or '',
            'NNTDBKKhan': self.NNTDBKKhan and 1 or 0,
            'NNTKTDNUBND': self.NNTKTDNUBND and 1 or 0,
            'CDLTTDCQT': self.CDLTTDCQT and 1 or 0,
            'CDLQTCTN': self.CDLQTCTN and 1 or 0,
            'CDDu': self.CDDu and 1 or 0,
            'CBTHop': self.CBTHop and 1 or 0,
            'HDGTGT': self.HDGTGT and 1 or 0,
            'HDBHang': self.HDBHang and 1 or 0,
            'HDBTSCong': self.HDBTSCong and 1 or 0,
            'HDBHDTQGia': self.HDBHDTQGia and 1 or 0,
            'HDKhac': self.HDKhac and 1 or 0,
            'CTu': self.CTu and 1 or 0,
            'DSCTSSDung': [
                {
                    'STT': index+1,
                    'TTChuc': line.issuer,
                    'Seri': line.serial,
                    'TNgay': line.valid_from,
                    'DNgay': line.valid_to,
                    'HThuc': line.HThuc,
                } for index, line in enumerate(self.cks_ids)
            ]
        }
        return data        


    def init_01_data(self):
        data = self.tvan_prepare_json_data()
        route_url = self.env['ir.config_parameter'].sudo().get_param('tvan.route_01')
        res = self.tvan_call_api(route_url, data)        
        return res.get('data', False)

    def tvan_sign_with_hsm(self):
        headers = CaseInsensitiveDict()
        route_url = self.company_id.cts_hsm_link + '/hsm/xml-01'
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
                    # 'public': True,
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

    def tvan_search(self):
        res = self.tvan_call_api('/api/tvan/search', data={'MTDiep': self.MTDiep})
        json_data = res.get('json_data', [])
        for line in json_data:
            if line.get('type') == '102':
                if line.get('THop') == '3':
                    self.state = '3'
                if line.get('THop') == '2':
                    self.state = '4'
            if line.get('type') == '103':
                self.state = '5'
                break
            