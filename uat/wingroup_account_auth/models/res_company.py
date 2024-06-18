# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    def kt_database_request_create_user(self, account_name, account_email):
        user = self.env['res.users'].sudo().create({
            'name': account_name, 
            'login': account_email, 
        })
        self.env['change.password.wizard'].create({
            'user_ids': [(0, 0, {
                'user_id': user.id,
                'user_login': account_email,
                'new_passwd': account_email,
            })]
        }).change_password_button()
        try:
            self.env['users.change.role.wiz'].create({
                'user_id': user.id,
                'role_id': 1,
            }).action_confirm()
        except Exception as e:
            self.env['users.change.role.wiz'].create({
                'user_id': user.id,
                'role_id': 5,
            }).action_confirm()
        return user

    @api.model
    def kt_database_request(self, data):
        print ('kt_database_request 444444444444444444444444', data)
        CompanyObj = self.env['res.company'].sudo()
        UserObj = self.env['res.users'].sudo()

        mst = str(data.get('Mã số thuế')).replace('.0', '')
        company_name = data.get('Tên công ty')
        account_email = data.get('NV Kế toán/Email') and data.get('NV Kế toán/Email').strip() or ''
        account_name = data.get('NV Kế toán') and data.get('NV Kế toán').strip() or ''
        service_state = data.get('Tình trạng dịch vụ')
        address = data.get('Địa chỉ')

        if not account_email or service_state != 'Đang hoạt động':
            return {
                'status': 'Fail',
                'message': 'Công ty phải Đang hoạt động!',
            } 
        if account_email in ('dailyalpc@wgroup.vn', 'ketoanquangnhat01@gmail.com'):
            return {
                'status': 'Fail',
                'message': 'Không tạo DB cho Nhân sự kế toán này!',
            } 

        old_company = CompanyObj.search([('vat', '=', mst)], limit=1)
        if not old_company:
            if service_state == 'Đang hoạt động':
                try:
                    old_company = CompanyObj.create({
                      'name': company_name,
                      'vat': mst,
                      'street': address,
                      'short_name': '{} - {}'.format(mst, company_name),
                      'x_nvkt': account_name,
                      'x_kt_email': account_email,
                    })
                except Exception as e:
                    return {
                        'status': 'Fail',
                        'message': str(r) + ' ' + str(e),
                    } 

        old_company.write({
            'x_note': service_state,
            'x_nvkt': account_name,
            'x_kt_email': account_email,
            'street': address,
        })

        user = UserObj.search([('login', 'in', (account_email, account_email.lower()))], limit=1)
        if not user:
            try:
                user = self.kt_database_request_create_user(account_name, account_email)
            except Exception as e:
                return {
                    'status': 'Fail',
                    'message': service_state + ' ' + mst + ' ' + company_name + ' ' + account_email + ' ' + str(e),
                } 
        if service_state == 'Đang hoạt động':
            try:
                old_company.write({
                  'user_ids': [(4, 2), (4, user.id), (4, 7), (4, 6), (4, 781)]
                })
            except Exception as e:
                old_company.write({
                  'user_ids': [(4, 2)]
                })
        else:
            old_company.write({
              'user_ids': [(4, 2)]
            })
        return {
            'status': 'Success',
            'message': '',
        }