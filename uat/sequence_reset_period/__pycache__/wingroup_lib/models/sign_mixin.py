# -*- coding: utf-8 -*-
import base64
import uuid
import json
import ast
from xml.dom import minidom
import xmltodict
from requests.structures import CaseInsensitiveDict
import requests

from num2words import num2words
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.tools.misc import formatLang, format_date
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError




class SignMixin(models.AbstractModel):
    _name = 'wg.sign.mixin'
    # _inherit = ['mail.thread']
    _table = 'wg_sign_mixin'
    _description = 'Dùng để kế thừa cho Model cần ký'

    
    sign_type = fields.Selection([('xml', 'XML'), ('pdf', 'PDF')], 'Định dạng file', default='xml')
    portal_token = fields.Char('Tracking code', index=1, size=120, copy=False)
    attachment_origin_id = fields.Many2one('ir.attachment', 'File chưa ký', copy=False)
    attachment_sign_id = fields.Many2one('ir.attachment', 'File đã ký', copy=False)
    MTDiep = fields.Char('Mã thông điệp', copy=False)

    def wg_get_sign_model_inherit(self):
        return []

    def wg_regen_portal_token(self):
        portal_token = '{}{}-{}'.format(self._table, self.id, str(uuid.uuid4()))
        self.write({
            'portal_token': portal_token,
        })

    @api.model 
    def create(self, vals):
        # vals['MTDiep'] = 'G0307633556' + str(uuid.uuid4()).upper().replace('-', '')
        res = super(SignMixin, self).create(vals)
        res.wg_regen_portal_token()
        return res


    def wg_open_digial_link_client(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/sign?portal_token={}'.format(self.portal_token),
            'target': 'new',
        }     

    def wg_get_digital_view_title(self):
        # TODO inherit
        return 'Hóa đơn điện tử'

    def wg_get_digital_socket_info(self):
        # TODO inherit
        return 'ws://127.0.0.1:8765/sign'


    def wg_open_digial_link_backend(self):
        return  {
            'type': 'ir.actions.client',
            'name': "Ký chứng từ",
            'tag': 'wg_digital_sign',
            'params': {
                'model': self._name,
                'record_id': self.id,
                'title': self.wg_get_digital_view_title(),
                'socket': self.wg_get_digital_socket_info(),
                'show_signed_file': False,
            },
        }   

    def wg_open_digial_sign_backend(self):
        res = self.wg_open_digial_link_backend()
        res['params']['show_signed_file'] = True
        return res

    def wg_delete_signed_file(self):
        if self.attachment_sign_id:
            self.write({
                'attachment_sign_id': False,
            })

    def wg_get_data_html_from_file(self, show_signed_file):
        str_data = self.attachment_origin_id.datas.decode('utf-8')
        if show_signed_file:
            str_data = self.attachment_sign_id.datas.decode('utf-8')
        xml_data = minidom.parseString(base64.b64decode(str_data)).toprettyxml()

        html_data =   "{}".format('<textarea rows="{}" cols="40">{}</textarea>'.format(
            xml_data.count('\n') + 1,
            xml_data
        ))
        return html_data

    def wg_get_data_to_show_sign(self, show_signed_file):    
        return {
            'portal_token': self.portal_token,
            'html_data': self.wg_get_data_html_from_file(show_signed_file),
            'html_link': False,
            'serialnumber': False,
        }        

    # TODO: 
    # 1 Tòa khai đăng ký sở dụng hóa đơn điện tử ['DLTKhai']
    # 2 Hóa đơn điện tử ['DLHDon']
    # 3 Thông báo sai sót ['DLTBao']
    def wg_get_id_content_to_sign(self):
        return ['DLTKhai']

    # TODO: 
    # 1 Tòa khai đăng ký sở dụng hóa đơn điện tử ['DLTKhai']
    # 2 Hóa đơn điện tử ['DSCKS', 'NNT']
    # 3 Thông báo sai sót ['DSCKS', 'NNT']
    def wg_get_tag_to_sign(self):
        return ['DSCKS', 'NNT']

    # Trả về XML data sẽ ký
    # TODO: phương thức này có thể bị thay thế trong trường hợp ký Hóa đơn để lấy lại file XML đã có mã
    def wg_get_xml_data_to_sign(self): 
        data = {
            'dataToSign': {
                'contentB64': self.attachment_origin_id.datas,
                'serialNumber': "",
                'params': {
                    'input_type': 'xml',
                    'pageNumToSign': 1,
                    'signPosition': {
                        'x': 380,
                        'y': 239,
                        'width': 18*10,
                        'height': 7*10,
                    },
                    'tagSignContent': self.wg_get_id_content_to_sign(),
                    'tagSignPosition': self.wg_get_tag_to_sign(),
                },
                'vat': '',
                'options': {
                    'type': 'no',
                    'datetime': '2023-02-08 08:00:00 GMT+7:00',
                }
            },
        }
        return data 

    # Xử lý data sau khi sign
    def wg_handle_signed_data(self, data):
        attachment_name = self.attachment_origin_id.name.split('.')
        value = {
            'name': '{}-signed.{}'.format(attachment_name[0], attachment_name[1]),
            'res_model': self._name,
            'res_id': self.id,
            'type': 'binary',
            'datas': data.get('content'),
            'public': True,
        }
        attachment_sign_id = self.attachment_sign_id
        if attachment_sign_id:
            attachment_sign_id.sudo().write(value)
        else:
            attachment_sign_id = self.env['ir.attachment'].create(value)
            self.write({
                'attachment_sign_id': attachment_sign_id.id,
            })
        message_content = """{title}<br></br>Serial: {serial}<br></br>Subject: 
        {subject}<br></br>valid_from: {valid_from}<br></br>valid_to: {valid_to}<br></br>issuer: {issuer}
        """.format(
            title=self._description + ' đã ký',
            serial=data.get('serial', 'Không xác định'),
            issuer=data.get('issuer'),
            subject=data.get('subject', 'Không xác định'),
            valid_from=data.get('valid_from', 'Không xác định'),
            valid_to=data.get('valid_to', 'Không xác định'),
        )
        self.sudo().message_post(body=message_content, attachment_ids=[attachment_sign_id.id])


    # Dữ liệu dể render trang client
    def wg_get_portal_sign_data(self):
        attachment = self.attachment_sign_id
        show_signed_file = True
        if not attachment:
            attachment = self.attachment_origin_id
            show_signed_file = False
        return {
            'title': 'Đăng ký/Thay đổi thông tin sử dụng hóa đơn điện tử',
            'url': '/web/content/{}'.format(attachment.id),
            # 'page': 1,
            # 'signalpage': self.get_signal_value().get('signalpage'),
            'input_type': 'xml',
            'vat': '',
            'content': attachment.datas,        
            'download_url': '/web/content/{}/{}?download=true'.format(attachment.id, attachment.name),        
            # 'link_apps': request.env['ir.config_parameter'].sudo().get_param('digital_self.apps'),
            # 'is_sign': (self.partner_is_sign if not is_so else self.self_state == 'to_approval') and 1 or 0,
            # 'position_x': self.get_signal_value().get('position_x'),
            # 'position_y': self.get_signal_value().get('position_y'),
            # 'position_width': self.get_signal_value().get('position_width'),
            # 'position_height': self.get_signal_value().get('position_height'),
            'html_link': False,
            'serialnumber': '',
            'portal_token': self.portal_token,
            'is_signed': show_signed_file,
            'html_data': self.wg_get_data_html_from_file(show_signed_file),
            'model': 'wg.inv.registry',
        }

    def wg_send_tct(self):
        pass

    def wg_xml_to_json(self):
        data_dict = xmltodict.parse(base64.b64decode(self.attachment_origin_id.datas.decode('utf-8')))
        print (data_dict, type(data_dict))
        print ('key: ', data_dict.keys())
        list_keys= ['TDiep', 'DLieu', 'TKhai', 'DLTKhai', 'NDTKhai', 'DSCTSSDung', 'CTS']
        message_content = data_dict
        for key in list_keys:
            message_content = message_content.get(key)
            if not message_content:
                raise ValidationError(key)
        raise ValidationError(str(message_content))


    @api.model
    def tvan_call_api(self, url, data):
        # print ('tvan_call_api 1', url, data, type(data))

        headers = CaseInsensitiveDict()
        base_url = self.env['ir.config_parameter'].sudo().get_param('tvan.main_url')
        token = self.env['ir.config_parameter'].sudo().get_param('tvan.client_key')
        headers['Accept'] = '*/*'
        headers['Authorization'] = 'Bearer ' + token
        headers['Accept-Encoding'] = 'gzip, deflate, br'
        headers['Connection'] = 'keep-alive'   

        try:
            result = requests.post(base_url + url, json=data, headers=headers)
            return json.loads(result.text).get('result')
        except Exception as e:
            return {
                'status': 'fail',
                'message': str(e),
            }
    @api.model 
    def tvan_get_selection_label(self, field_name):
        return dict(self._fields[field_name].selection).get(self[field_name])