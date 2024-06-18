# -*- coding: utf-8 -*-
import json
import requests

from num2words import num2words
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.tools.misc import formatLang, format_date
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError

# Số 1:   Phản ánh loại hóa đơn điện tử giá trị gia tăng
# Số 2:   Phản ánh loại hóa đơn điện tử bán hàng
# Số 3:   Phản ánh loại hóa đơn điện tử bán tài sản công
# Số 4:   Phản ánh loại hóa đơn điện tử bán hàng dự trữ quốc gia
# Số 5:   Phản ánh các loại hóa đơn điện tử khác là tem điện tử, vé điện tử, thẻ điện tử, phiếu thu điện tử hoặc các chứng từ điện tử có tên gọi khác nhưng có nội dung của hóa đơn điện tử theo quy định tại Nghị định 123/2020/NĐ-CP
# Số 6:   Phản ánh các chứng từ điện tử được sử dụng và quản lý như hóa đơn bao gồm: phiếu xuất kho kiêm vận chuyển nội bộ điện tử, phiếu xuất kho hàng gửi bán đại lý điện tử.

# Chữ T:  Áp dụng đối với hóa đơn điện tử do các doanh nghiệp, tổ chức, hộ, cá nhân kinh doanh đăng ký sử dụng với cơ quan thuế;
# Chữ D:  Áp dụng đối với hóa đơn bán tài sản công và hóa đơn bán hàng dự trữ quốc gia hoặc hóa đơn điện tử đặc thù không nhất thiết phải có một số tiêu thức do các doanh nghiệp, tổ chức đăng ký sử dụng;
# Chữ L:  Áp dụng đối với hóa đơn điện tử của cơ quan thuế cấp theo từng lần phát sinh;
# Chữ M:  Áp dụng đối với hóa đơn điện tử được khởi tạo từ máy tính tiền;
# Chữ N:  Áp dụng đối với phiếu xuất kho kiêm vận chuyển nội bộ điện tử;
# Chữ B:  Áp dụng đối với phiếu xuất kho hàng gửi bán đại lý điện tử,
# Chữ G:  Áp dụng đối với tem, vé, thẻ điện tử là hóa đơn giá trị gia tăng;
# Chữ H:  Áp dụng đối với tem, vé, thẻ điện tử là hóa đơn bán hàng.

# PHỤ LỤC I - DANH SÁCH CÁC LOẠI THÔNG ĐIỆP

# Nhóm thông điệp đáp ứng nghiệp vụ đăng ký, thay đổi thông tin sử dụng hóa đơn điện tử, đề nghị cấp hóa đơn điện tử có mã theo từng lần phát sinh
# 100 - Thông điệp gửi tờ khai đăng ký/thay đổi thông tin sử dụng hóa đơn điện tử
# 101 - Thông điệp gửi tờ khai đăng ký thay đổi thông tin đăng ký sử dụng HĐĐT khi ủy nhiệm/nhận ủy nhiệm lập hóa đơn
# 102 - Thông điệp thông báo về việc tiếp nhận/không tiếp nhận tờ khai đăng ký/thay đổi thông tin sử dụng HĐĐT, tờ khai đăng ký thay đổi thông tin đăng ký sử dụng HĐĐT khi ủy nhiệm/nhận ủy nhiệm lập hóa đơn
# 103 - Thông điệp thông báo về việc chấp nhận/không chấp nhận đăng ký/thay đổi thông tin sử dụng hóa đơn điện tử
# 104 - Thông điệp thông báo về việc chấp nhận/không chấp nhận đăng ký thay đổi thông tin đăng ký sử dụng HĐĐT khi ủy nhiệm/nhận ủy nhiệm lập hóa đơn
# 105 - Thông điệp thông báo về việc hết thời gian sử dụng hóa đơn điện tử có mã qua cổng thông tin điện tử Tổng cục Thuế/qua ủy thác tổ chức cung cấp dịch vụ về hóa đơn điện tử; không thuộc trường hợp sử dụng hóa đơn điện tử không có mã
# 106 - Thông điệp gửi Đơn đề nghị cấp hóa đơn điện tử có mã của CQT theo từng lần phát sinh

# Nhóm thông điệp đáp ứng nghiệp vụ lập và gửi hóa đơn điện tử đến cơ quan thuế
# 200 - Thông điệp gửi hóa đơn điện tử tới cơ quan thuế để cấp mã
# 201 - Thông điệp gửi hóa đơn điện tử tới cơ quan thuế để cấp mã theo từng lần phát sinh
# 202 - Thông điệp thông báo kết quả cấp mã hóa đơn điện tử của cơ quan thuế
# 203 - Thông điệp chuyển dữ liệu hóa đơn điện tử không mã đến cơ quan thuế
# 204 - Thông điệp thông báo mẫu số 01/TB-KTDL về việc kết quả kiểm tra dữ liệu hóa đơn điện tử
# 205 - Thông điệp phản hồi về hồ sơ đề nghị cấp hóa đơn điện tử có mã của cơ quan thuế theo từng lần pháp sinh.

# Nhóm thông điệp đáp ứng nghiệp vụ xử lý hóa đơn có sai sót
# 300 - Thông điệp thông báo về hóa đơn điện tử đã lập có sai sót
# 301 - Thông điệp gửi thông báo về việc tiếp nhận và kết quả xử lý về việc hóa đơn điện tử đã lập có sai sót
# 302 - Thông điệp thông báo về hóa đơn điện tử cần rà soát

# Nhóm thông điệp chuyển bảng tổng hợp dữ liệu hóa đơn điện tử đến cơ quan thuế
# 400 - Thông điệp chuyển bảng tổng hợp dữ liệu hóa đơn điện tử đến cơ quan thuế

# Nhóm thông điệp chuyển dữ liệu hóa đơn điện tử do TCTN ủy quyền cấp mã đến cơ quan thuế
# 500 - Thông điệp chuyển dữ liệu hóa đơn điện tử do TCTN ủy quyền cấp mã đến cơ quan thuế

# Nhóm thông điệp khác
# 999 - Thông điệp phản hồi kỹ thuật


# PHỤ LỤC VI DANH MỤC HÌNH THỨC HÓA ĐƠN BỊ THAY THẾ/LOẠI ÁP DỤNG HÓA ĐƠN
# 1 - Hóa đơn điện tử theo Nghị định 123/2020/NĐ-CP
# 2 - Hóa đơn điện tử có mã xác thực của cơ quan thuế theo Quyết định số 1209/QĐ-BTC ngày 23 tháng 6 năm 2015 và Quyết định số 2660/QĐ-BTC 
    # ngày 14 tháng 12 năm 2016 của Bộ Tài chính (Hóa đơn có mã xác thực của CQT theo Nghị định số 51/2010/NĐ-CP và Nghị định số 04/2014/NĐ-CP)
# 3 - Các loại hóa đơn theo Nghị định số 51/2010/NĐ-CP và Nghị định số 04/2014/NĐ-CP (Trừ hóa đơn điện tử có mã xác thực của cơ quan thuế theo Quyết định số 1209/QĐ-BTC và Quyết định số 2660/QĐ-BTC)
# 4 - Hóa đơn đặt in theo Nghị định 123/2020/NĐ-CP

# PHỤ LỤC VII - DANH MỤC LOẠI KỲ TÍNH THUẾ/ KỲ DỮ LIỆU VÀ KỲ TÍNH THUẾ/ KỲ DỮ LIỆU
# T - Kỳ theo tháng
# Q - Kỳ theo quý
# N - Kỳ theo ngày


# PHỤ LỤC IX - DANH MỤC TÍNH CHẤT THÔNG BÁO
# 0 - Mới
# 1 - Hủy
# 2 - Điều chỉnh
# 3 - Thay thế
# 4 - Giải trình
# 5 - Sai sót do tổng hợp

# PHỤ LỤC X - DANH MỤC TRẠNG THÁI XÁC NHẬN CỦA CƠ QUAN THUẾ VỀ VIỆC CHẤP NHẬN/KHÔNG CHẤP NHẬN ĐĂNG KÝ/THAY ĐỔI THÔNG TIN SỬ DỤNG HÓA ĐƠN ĐIỆN TỬ
# 1 - Trường hợp chấp nhận đăng ký/thay đổi thông tin sử dụng hóa đơn điện tử.
# 2 - Trường hợp không chấp nhận đăng ký/thay đổi thông tin sử dụng hóa đơn điện tử.


# PHỤ LỤC XI - DANH MỤC LOẠI THÔNG BÁO KẾT QUẢ ĐỐI CHIẾU DỮ LIỆU HÓA ĐƠN ĐIỆN TỬ
# 1 - Thông báo hóa đơn không đủ điều kiện cấp mã
# 2 - Thông báo kết quả đối chiếu thông tin gói dữ liệu hợp lệ
# 3 - Thông báo kết quả đối chiếu thông tin sơ bộ từng hóa đơn không mã không hợp lệ
# 4 - Thông báo kết quả đối chiếu sơ bộ thông tin của Bảng tổng hợp khác xăng dầu, Tờ khai dữ liệu hóa đơn, chứng từ hàng hóa, dịch vụ bán ra không hợp lệ
# 5 - Thông báo kết quả đối chiếu sơ bộ thông tin của Bảng tổng hợp xăng dầu không hợp lệ
# 6 - Thông báo kết quả đối chiếu sơ bộ thông tin Đơn đề nghị cấp hóa đơn điện tử có mã của CQT theo từng lần phát sinh với trường hợp NNT gửi đơn qua Cổng thông tin điện tử của TCT
# 9 - Thông báo kết quả đối chiếu thông tin gói dữ liệu không hợp lệ các trường hợp khác


# PHỤ LỤC XII - DANH MỤC TRẠNG THÁI TIẾP NHẬN TỜ KHAI ĐĂNG KÝ/THAY ĐỔI THÔNG TIN SỬ DỤNG HÓA ĐƠN ĐIỆN TỬ CỦA CQT
# 1 - Trường hợp 1: Trường hợp tiếp nhận Tờ khai đăng ký sử dụng hóa đơn điện tử
# 2 - Trường hợp 2: Trường hợp không tiếp nhận Tờ khai đăng ký sử dụng hóa đơn điện tử
# 3 - Trường hợp 3: Trường hợp tiếp nhận Tờ khai đăng ký thay đổi thông tin sử dụng hóa đơn điện tử
# 4 - Trường hợp 4: Trường hợp không tiếp nhận Tờ khai đăng ký thay đổi thông tin sử dụng hóa đơn điện tử


class InvoiceMixin(models.AbstractModel):
    _name = 'wg.invoice.mixin'
    _description = 'Hóa đơn điện tử'


    @api.depends('name', 'SHDon', 'MSTNMua')
    def name_get(self):
        return [(r.id, '{}_{}'.format(
            # r.MSTNMua or '', 
            r.name or '', 
            r.SHDon or 'Mới',
        )) for r in self]

    @api.model 
    def tvan_get_selection_label(self, field_name):
        return dict(self._fields[field_name].selection).get(self[field_name])

    @api.onchange('KHMSHDonTT78')
    def onchange_KHMSHDonTT78(self):
        if self.KHMSHDonTT78:
            self.KHMSHDon = self.KHMSHDonTT78
            self.THDon = str(self.tvan_get_selection_label('KHMSHDonTT78'))

    @api.depends('KHMSHDon', 'KHHDon')
    def _compute_name_inv(self):
        for record in self:
            record.name = '{}{}'.format(
                record.KHMSHDon or '', 
                record.KHHDon or ''
            )

    @api.depends('TenNMua', 'HVTNMHang')
    def _compute_buyer_name(self):
        for record in self:
            record.partner_buyer_name = record.HVTNMHang + ', ' + record.TenNMua if record.TenNMua \
                and record.HVTNMHang else record.TenNMua if record.TenNMua else record.HVTNMHang \
                if record.HVTNMHang else ''

    state = fields.Selection([
        ('0', 'HĐ mới khởi tạo'),
        ('1', 'HĐ có đủ chữ ký'),
        ('3', 'HĐ sai sót bị thay thế'),
        ('4', 'HĐ sai sót bị điều chỉnh'),
        ('5', 'HĐ huỷ'),
    ], string='Trạng thái phát hành', default='0', copy=False)
    company_id = fields.Many2one('res.company', string='Công ty', default=lambda self: self.env.company, readonly=True,
        states={'0': [('readonly', False)]})
    partner_buyer_name = fields.Char(string='Người mua hàng', compute='_compute_buyer_name', store=True)

    # Thẻ HDon\DLHDon\TTChung chứa thông tin chung của hóa đơn
    # QĐ1450 PBan 2.0.0, QĐ1510 PBan 2.0.1
    PBan = fields.Char('Phiên bản XML', size=6, default='2.0.1', help='Phiên bản XML (Trong Quy định này có giá trị là 2.0.1)')
    # Khoản 1 Điều 4 Thông tư 78/2021/TT- BTC
    THDon = fields.Char('Tên hóa đơn', size=100)
    # PHỤ LỤC II - DANH MỤC KÝ HIỆU MẪU SỐ HÓA ĐƠN
    KHMSHDonTT78 = fields.Selection([
        ('1', 'HĐĐT giá trị gia tăng'),
        ('2', 'HĐĐT bán hàng'),
        ('3', 'HĐĐT bán tài sản công'),
        ('4', 'HĐĐT bán hàng dự trữ quốc gia'),
        ('5', 'Tem/Vé/Thẻ/Phiếu thu/Chứng từ điện tử'),
        ('6', 'PXK kiêm VC nội bộ'),
        ], 'Ký hiệu mẫu số hóa đơn TT78', default='1', readonly=True,
        states={'0': [('readonly', False)]})
    KHMSHDon = fields.Char('Ký hiệu mẫu số hóa đơn', size=11, readonly=True,
        states={'0': [('readonly', False)]})
    KHHDon = fields.Char('Ký hiệu hóa đơn', size=8, readonly=True,
        states={'0': [('readonly', False)]})
    name = fields.Char('Ký hiệu', compute='_compute_name_inv', store=True)
    SHDon = fields.Char('Số hóa đơn', size=8, copy=False, readonly=True,
        states={'0': [('readonly', False)]})
    MHSo = fields.Char('Mã hồ sơ', size=20, readonly=True,
        states={'0': [('readonly', False)]}, help='Bắt buộc (Đối với trường hợp là hóa đơn đề nghị cấp mã của cơ quan thuế theo từng lần phát sinh)', )
    NLap = fields.Date('Ngày lập', default=fields.Date.today, readonly=True,
        states={'0': [('readonly', False)]})
    # Điểm a, khoản 6, Điều 10 Nghị định 123/2020/NĐ-CP
    SBKe = fields.Char('Số bảng kê', copy=False, size=50, readonly=True,
        states={'0': [('readonly', False)]}, help='Số bảng kê (Số của bảng kê các loại hàng hóa, dịch vụ đã bán kèm theo hóa đơn)')
    NBKe = fields.Date('Ngày bảng kê', copy=False, readonly=True,
        states={'0': [('readonly', False)]}, help='Ngày bảng kê (Ngày của bảng kê các loại hàng hóa, dịch vụ đã bán kèm theo hóa đơn)')

    DVTTe = fields.Char('Đơn vị tiền tệ', size=3, default='VND', readonly=True,
        states={'0': [('readonly', False)]})
    TGia = fields.Float('Tỷ giá', digits=(7,2), default=1, readonly=True,
        states={'0': [('readonly', False)]})

    HTTToan = fields.Char('Hình thức thanh toán', size=50, readonly=True,
        states={'0': [('readonly', False)]}, default='Tiền mặt/chuyển khoản')
    MSTTCGP = fields.Char('MST TCGP', size=14, help='Mã số thuế tổ chức cung cấp giải pháp hóa đơn điện tử')
    MSTDVNUNLHDon = fields.Char('MST đơn vị nhận ủy nhiệm', size=14, help='Mã số thuế đơn vị nhận ủy nhiệm lập hóa đơn')
    TDVNUNLHDon = fields.Char('Tên đơn vị nhận ủy nhiệm', size=400, help='Tên đơn vị nhận ủy nhiệm lập hóa đơn')
    DCDVNUNLDon = fields.Char('Địa chỉ đơn vị nhận ủy nhiệm', size=400, help='Địa chỉ đơn vị nhận ủy nhiệm lập hóa đơn')

    # Trường dành cho Hóa đơn thay thế / điều chỉnh thông tin
    # Thẻ HDon\DLHDon\TTChung\TTHDLQuan chứa thông tin hóa đơn liên quan trong trường hợp là hóa đơn điều chỉnh hoặc thay thế
    TCHDon = fields.Selection([
        ('0', 'Hóa đơn gốc'),
        ('1', 'Điều chỉnh'),
        ('2', 'Thay thế'),
    ], 'Tính chất hóa đơn', default='0', readonly=True,
        states={'0': [('readonly', False)]})
    LHDCLQuan = fields.Char('Loại hóa đơn có liên quan', size=1, help='Loại hóa đơn có liên quan (Loại hóa đơn bị thay thế/điều chỉnh)')
    KHMSHDCLQuan = fields.Char('Ký hiệu mẫu số HĐ có liên quan', size=11, help='Ký hiệu mẫu số hóa đơn có liên quan (Ký hiệu mẫu số hóa đơn bị thay thế/điều chỉnh)')
    KHHDCLQuan = fields.Char('Ký hiệu hóa đơn có liên quan', size=8, help='Ký hiệu hóa đơn có liên quan (Ký hiệu hóa đơn bị thay thế/điều chỉnh)')
    SHDCLQuan = fields.Char('Số hóa đơn có liên quan', size=8, help='Số hóa đơn có liên quan (Số hóa đơn bị thay thế/điều chỉnh)')
    NLHDCLQuan = fields.Date('Ngày lập hóa đơn có liên quan', help='Ngày lập hóa đơn có liên quan (Ngày lập hóa đơn bị thay thế/điều chỉnh)')
    GChu = fields.Char('Ghi chú', size=255)

    # Thẻ HDon\DLHDon\TTChung\TTKhac chứa thông tin khác (Chi tiết được mô tả tại Khoản 1, Mục II, Phần II quy định này)
    # TODO
    # Thẻ HDon\DLHDon\NDHDon chứa nội dung hóa đơn, bao gồm: Thông tin người bán, người mua, danh sách hàng hóa, dịch vụ và thông tin thanh toán của hóa đơn
    # TODO

    # Thẻ HDonVDLHDon\NDHDon\NBan chứa tên, địa chỉ, MST của người bán
    TenNBan = fields.Char('Tên người bán', size=400, help='Thẻ trong XMl là HDonVDLHDon/NDHDon/NBan/Ten')
    MSTNBan = fields.Char('MST người bán', size=14, help='Thẻ trong XMl là HDonVDLHDon/NDHDon/NBan/MST')
    DChiNBan = fields.Char('Địa chỉ người bán', size=400, help='Thẻ trong XMl là HDonVDLHDon/NDHDon/NBan/DChi')
    SDThoaiNBan = fields.Char('SĐT người bán', size=20, help='Thẻ trong XMl là HDonVDLHDon/NDHDon/NBan/SDThoai')
    DCTDTuNBan = fields.Char('Email người bán', size=50, help='Thẻ trong XMl là HDonVDLHDon/NDHDon/NBan/DCTDTu')
    STKNHangNBan = fields.Char('STK ngân hàng người bán', size=30, help='Thẻ trong XMl là HDonVDLHDon/NDHDon/NBan/STKNHang')
    TNHangNBan = fields.Char('Tên ngân hàng người bán', size=400, help='Thẻ trong XMl là HDonVDLHDon/NDHDon/NBan/TNHang')
    FaxNBan = fields.Char('Fax người bán', size=20, help='Thẻ trong XMl là HDonVDLHDon/NDHDon/NBan/Fax')
    WebsiteNBan = fields.Char('Website người bán', size=100, help='Thẻ trong XMl là HDonVDLHDon/NDHDon/NBan/Website')
    # Trường bổ sung của Hóa đơn bán tài sản công 
    MDVQHNSachNBan = fields.Char('Mã đơn vị quan hệ ngân sách (bán)', size=7, help='Mã đơn vị quan hệ ngân sách (Mã số đơn vị có quan hệ với ngân sách của đơn vị bán tài sản công). Thẻ trong XMl là HDonVDLHDon/NDHDon/NBan/MDVQHNSach')
    SQDinhNBan = fields.Char('Mã Số quyết định bán tài sản công', size=50, help='Thẻ trong XMl là HDonVDLHDon/NDHDon/NBan/SQDinh')
    NQDinhNBan = fields.Date('Ngày quyết định bán tài sản công', help='Thẻ trong XMl là HDonVDLHDon/NDHDon/NBan/NQDinh')
    CQBHQDinhNBan = fields.Char('Cơ quan ban hành quyết định bán tài sản công', size=200, help='Thẻ trong XMl là HDonVDLHDon/NDHDon/NBan/CQBHQDinh')
    HTBanNBan = fields.Char('Hình thức bán tài sản công', size=200, help='Thẻ trong XMl là HDonVDLHDon/NDHDon/NBan/HTBan')
    LDDNBo = fields.Char('Lệnh điều động nội bộ', size=255, help='Thẻ trong XMl là HDonVDLHDon/NDHDon/NBan/LDDNBo - Bắt buộc')
    # DChi = fields.Char('Địa chỉ kho xuất hàng', size=400, help='Thẻ trong XMl là HDonVDLHDon/NDHDon/NBan/DChi')
    HDSo = fields.Char('Hợp đồng vận chuyển số', size=255, help='Thẻ trong XMl là HDonVDLHDon/NDHDon/NBan/HDSo - Không bắt buộc')
    HVTNXHang = fields.Char('Họ và tên người xuất hàng', size=100, help='Thẻ trong XMl là HDonVDLHDon/NDHDon/NBan/HVTNXHang - Không bắt buộc')
    TNVChuyen = fields.Char('Tên người vận chuyển', size=100, help='Thẻ trong XMl là HDonVDLHDon/NDHDon/NBan/TNVChuyen - Không bắt buộc')
    PTVChuyen = fields.Char('Phương tiện vận chuyển', size=50, help='Thẻ trong XMl là HDonVDLHDon/NDHDon/NBan/PTVChuyen - Bắt buộc')
    # Các trường bổ sung của Phiếu xuất kho hàng gửi bán đại lý
    HDKTSo = fields.Char('Hợp đồng kinh tế số', size=255, help='Thẻ trong XMl là HDonVDLHDon/NDHDon/NBan/HDKTSo - Bắt buộc')
    HDKTNgay = fields.Date('Hợp đồng kinh tế ngày', help='Thẻ trong XMl là HDonVDLHDon/NDHDon/NBan/HDKTNgay - Bắt buộc')
    HVTNXHang = fields.Char('Họ và tên người xuất hàng', size=100, help='Thẻ trong XMl là HDonVDLHDon/NDHDon/NBan/HVTNXHang - Không bắt buộc')
    TNVChuyen = fields.Char('Tên người vận chuyển', size=100, help='Thẻ trong XMl là HDonVDLHDon/NDHDon/NBan/TNVChuyen - Không bắt buộc')
    HDSo = fields.Char('Hợp đồng vận chuyển số', size=255, help='Thẻ trong XMl là HDonVDLHDon/NDHDon/NBan/HDSo - Không bắt buộc')
    PTVChuyen = fields.Char('Phương tiện vận chuyển', size=50, help='Thẻ trong XMl là HDonVDLHDon/NDHDon/NBan/PTVChuyen - Bắt buộc')
    # Các trường bổ sung của Các loại hóa đơn khác
    # Bao gồm tem điện tử, vé điện tử, thẻ điện tử, phiếu thu điện tử hoặc các chứng từ điện tử có tên gọi khác theo quy định tại Khoản 5, Điều 8 Nghị định 123/2020/NĐ-CP.


    # Thẻ HDon\DLHDon\NDHDon\NBan\TTKhac chứa thông tin khác (Chi tiết được mô tả tại Khoản 1, Mục II, Phần II quy định này)
    # TODO

    # Thẻ HDon\DLHDon\NDHDon\NMua chứa tên, địa chỉ, MST của người mua
    TenNMua = fields.Char('Tên người mua', size=400, readonly=True,
        states={'0': [('readonly', False)]}, help='Thẻ trong XMl là HDonVDLHDon/NDHDon/NMua/Ten')
    MSTNMua = fields.Char('MST người mua', size=14, readonly=True,
        states={'0': [('readonly', False)]}, help='Thẻ trong XMl là HDonVDLHDon/NDHDon/NMua/MST')
    DChiNMua = fields.Char('Địa chỉ người mua', size=400, readonly=True,
        states={'0': [('readonly', False)]}, help='Thẻ trong XMl là HDonVDLHDon/NDHDon/NMua/DChi')
    MKHang = fields.Char('Mã khách hàng', size=50, readonly=True,
        states={'0': [('readonly', False)]}, help='Thẻ trong XMl là HDonVDLHDon/NDHDon/NMua/MKHang')
    SDThoaiNMua = fields.Char('SĐT người mua', size=20, readonly=True,
        states={'0': [('readonly', False)]}, help='Thẻ trong XMl là HDonVDLHDon/NDHDon/NMua/SDThoai')
    DCTDTuNMua = fields.Char('Email người mua', size=50, readonly=True,
        states={'0': [('readonly', False)]}, help='Thẻ trong XMl là HDonVDLHDon/NDHDon/NMua/DCTDTu')
    HVTNMHang = fields.Char('Họ và tên người mua hàng', size=100, readonly=True,
        states={'0': [('readonly', False)]}, help='Thẻ trong XMl là HDonVDLHDon/NDHDon/NMua/HVTNMHang')
    STKNHangNMua = fields.Char('STK ngân hàng người mua', size=30, readonly=True,
        states={'0': [('readonly', False)]}, help='Thẻ trong XMl là HDonVDLHDon/NDHDon/NMua/STKNHang')
    TNHangNMua = fields.Char('Tên ngân hàng người mua', size=400, readonly=True,
        states={'0': [('readonly', False)]}, help='Thẻ trong XMl là HDonVDLHDon/NDHDon/NMua/TNHang')
    # Trường bổ sung của Hóa đơn bán tài sản công 
    MDVQHNSachNMua = fields.Char('Mã đơn vị quan hệ ngân sách (mua)', size=7, help='Bắt buộc (Đối với trường hợp người mua là cơ quan, tổ chức, đơn vị, doanh nghiệp không có Mã số thuế). Thẻ trong XMl là HDonVDLHDon/NDHDon/NMua/MDVQHNSach')
    DDVCHDen = fields.Char('Địa điểm vận chuyển hàng đến', size=400, help='Bắt buộc (Đối với trường hợp tài sản là hàng hóa nhập khẩu bị tịch thu). Thẻ trong XMl là HDonVDLHDon/NDHDon/NMua/DDVCHDen')
    TGVCHDTu = fields.Date('Thời gian vận chuyển hàng đến từ', help='Bắt buộc (Đối với trường hợp tài sản là hàng hóa nhập khẩu bị tịch thu). Thẻ trong XMl là HDonVDLHDon/NDHDon/NMua/TGVCHDTu')
    TGVCHDDen = fields.Date('Thời gian vận chuyển hàng đến đến', help='Đối với trường hợp tài sản là hàng hóa nhập khẩu bị tịch thu. Thẻ trong XMl là HDonVDLHDon/NDHDon/NMua/TGVCHDDen')
    # Các trường bổ sung của Hóa đơn bán hàng dự trữ quốc gia
    CMND = fields.Char('Số CMND/CCCD/ Hộ chiếu', size=20, help='Bắt buộc (Đối với trường hợp người mua không có Mã số thuế). Thẻ trong XMl là HDonVDLHDon/NDHDon/NMua/CMND')
    # Các trường bổ sung của Phiếu xuất kho kiêm vận chuyển nội bộ
    HVTNNHang = fields.Char('Họ và tên người nhận hàng', size=100, help='Thẻ trong XMl là HDonVDLHDon/NDHDon/NMua/HVTNNHang - không bắt buộc')
    # Các trường bổ sung của Phiếu xuất kho hàng gửi bán đại lý
    HVTNNHang = fields.Char('Họ và tên người nhận hàng', size=100, help='Thẻ trong XMl là HDonVDLHDon/NDHDon/NMua/HVTNNHang - không bắt buộc')
    

    # Thẻ HDon\DLHDon\NDHDon\NMua\TTKhac chứa thông tin khác (Chi tiết được mô tả tại Khoản 1, Mục II, Phần II quy định này)
    # TODO

    # Thẻ HDon\DLHDon\NDHDon\TToan chứa thông tin về số tiền thanh toán, số tiền thuế trên hóa đơn
    TgTCThue = fields.Float('Tổng tiền chưa thuế', digits=(21, 6), help='Tổng tiền chưa thuế (Tổng cộng thành tiền chưa có thuế GTGT)')
    TgTThue = fields.Float('Tổng tiền thuế', digits=(21, 6), help='Tổng tiền thuế (Tổng cộng tiền thuế GTGT)')

    # Các chỉ tiêu sau được đặt bên trong thẻ HDon\DLHDon\NDHDon\TToan
    TTCKTMai = fields.Float('Tổng CK', digits=(21, 6), help='Tổng tiền chiết khấu thương mại')
    TgTTTBSo = fields.Float('Tổng tiền thanh toán bằng số', digits=(21, 6))
    TgTTTBChu = fields.Char('Tổng tiền thanh toán bằng chữ', size=255)

    # Thẻ HDon\DLHDon\NDHDon\TToan\TTKhac chứa thông tin khác (Chi tiết được mô tả tại Khoản 1, Mục II, Phần II quy định này)
    # Thẻ HDon\DLHDon\TTKhac chứa thông tin khác (Chi tiết được mô tả tại Khoản 1, Mục II, Phần II quy định này)

    # Thẻ HDon\DLQRCode chứa dữ liệu QR Code
    # TODO QR Code - TGL

    # Với hóa đơn điện tử có mã, nếu đủ điều kiện cấp mã, hệ thống của cơ quan thuế trả về chỉ tiêu Mã của cơ quan thuế trên hóa đơn điện tử (Thẻ MCCQT, đặt bên trong thẻ HDon)
    MCCQT = fields.Char('Mã của cơ quan thuế', copy=False, size=34, help='Mã của cơ quan thuế (Mã của cơ quan thuế trên hóa đơn điện tử)')

    # Các trường bổ sung của Hóa đơn bán hàng
    HDDCKPTQuan = fields.Char('Hóa đơn dành cho khu phi thuế quan', size=1, 
        default='0', help='Hóa đơn dành cho khu phi thuế quan (Hóa đơn dành cho tổ chức, cá nhân trong khu phi thuế quan)')


class InvoiceLineMixin(models.AbstractModel):
    _name = 'wg.invoice.line.mixin'
    _description = 'Chi tiết sản phẩm/dịch vụ'


    # Thẻ HDon\DLHDon\NDHDon\DSHHDVu\HHDVu chứa chi tiết 01 dòng hàng hóa dịch vụ (Thẻ này có thể lặp lại nhiều lần tương ứng với số lượng hàng hóa, dịch vụ)
    TChat = fields.Selection([
        ('1', 'HH, DV'),
        ('2', 'KM'),
        ('3', 'CK'),
        ('4', 'Ghi chú'),
        ], 'Tính chất', default='1')
    STT = fields.Integer('Số thứ tự')
    # Điểm a, khoản 6, Điều 10 Nghị định 123/2020/NĐ-CP
    MHHDVu = fields.Char('Mã hàng hóa, dịch vụ', size=50)
    THHDVu = fields.Char('Tên hàng hóa, dịch vụ', size=500)
    # Khoản 6, khoản 14, Điều 10 Nghị định 123/2020/NĐ-CP
    DVTinh = fields.Char('Đơn vị tính', size=50)
    # Khoản 6, khoản 14, Điều 10 Nghị định 123/2020/NĐ-CP
    SLuong = fields.Float('Số lượng', digits=(21, 6), default=1)
    # Khoản 6, khoản 14, Điều 10 Nghị định 123/2020/NĐ-CP
    DGia = fields.Float('Đơn giá', digits=(21, 6), default=0)
    TLCKhau = fields.Float('% CK', digits=(6, 4), help='''Tỷ lệ % chiết khấu (Trong trường hợp thể hiện thông tin chiết khấu cho từng hàng hóa, dịch vụ)''')
    STCKhau = fields.Float('Tiền CK', digits=(21, 6), help='(Trong trường hợp thể hiện thông tin chiết khấu cho từng hàng hóa, dịch vụ)')
    ThTien = fields.Float('Thành tiền chưa VAT', digits=(21, 6), help='Thành tiền (Thành tiền chưa có thuế GTGT)')
    # 0% 5% 10% KCT KKKNT KHAC:AB.CD% Trường hợp khác, với “:AB.CD” là bắt buộc trong trường hợp xác định được giá trị thuế suất. A, B, C, D là các số nguyên từ 0 đến 9. Ví dụ: KHAC:AB.CD%
    TSuat = fields.Char('Thuế suất', size=11, default='10%')


class InvoiceTaxMixin(models.AbstractModel):
    _name = 'wg.invoice.tax.mixin'
    _description = 'Chi tiết thuế suất'

    # Thẻ HDonVDLHDon\NDHDon\TToan\THTTLTSuat\LTSuat chứa chi tiết thông tin tổng hợp của mỗi loại thuế suất (Thẻ này có thể lặp lại nhiều lần tương ứng với số lượng các mức thuế suất khác nhau)
    TSuat = fields.Char('Thuế suất', size=11, help='Thuế suất (Thuế suất thuế GTGT)')
    ThTien = fields.Float('Thành tiền', digits=(21, 6), help='Thành tiền (Thành tiền chưa có thuế GTGT)')
    TThue = fields.Float('Tiền thuế', digits=(21, 6), help='Tiền thuế (Tiền thuế GTGT)')

    
class InvoiceExpenseMixin(models.AbstractModel):
    _name = 'wg.invoice.expense.mixin'
    _description = 'Chi tiết phí, lệ phí'
    # Thẻ HDon\DLHDon\NDHDon\TToan\DSLPhi\LPhi chứa chi tiết từng loại tiền phí, lệ phí (Thẻ này có thể lặp lại nhiều lần tương ứng với số loại phí, lệ phí)

    # Khoản 11, Điều 10, Nghị định 123/2020/NĐ-CP
    TLPhi = fields.Char('Tên loại phí', size=100)
    # Khoản 11, Điều 10, Nghị định 123/2020/NĐ-CP
    TPhi = fields.Float('Tiền phí', digits=(21, 6))

    

class InvoiceTB04Mixin(models.AbstractModel):
    _name = 'wg.tb04.mixin'
    _description = 'Thông báo Hóa đơn điện tử có sai sót'


    state = fields.Selection([
        ('0', 'Tạo mới'), 
        ('1', 'Gủi thành công'),
        ('2', 'Gủi lỗi'),
        ('3', 'Đã tiếp nhận'),
        ('4', 'Không tiếp nhận'),
        ('5', 'Được chấp nhận'),
        ('6', 'Không chấp nhận'),
    ], 'Trạng thái', default='0')
    company_id = fields.Many2one('res.company', string='Công ty', default=lambda self: self.env.company, readonly=True,
        states={'0': [('readonly', False)]})
    PBan = fields.Char('Phiên bản XML', size=6, readonly=True,
        states={'0': [('readonly', False)]}, default='2.0.1', help='Phiên bản XML (Trong Quy định này có giá trị là 2.0.1)')
    MSo = fields.Char('Mẫu số thông báo', size=15, readonly=True,
        states={'0': [('readonly', False)]}, default='04/SS-HĐĐT')
    Ten = fields.Char('Tên thông báo', size=255, readonly=True,
        states={'0': [('readonly', False)]}, default='THÔNG BÁO HÓA ĐƠN ĐIỆN TỬ CÓ SAI SÓT')
    Loai = fields.Selection([
            ('1', 'Thông báo hủy/giải trình của NNT'),
            ('2', 'Thông báo hủy/giải trình của NNT theo thông báo của CQT'),
        ], 'Loại thông báo', readonly=True,
        states={'0': [('readonly', False)]}, default='1')
    So = fields.Char('Số thông báo của CQT', size=30, readonly=True,
        states={'0': [('readonly', False)]}, help='Bắt buộc (Đối với Loại=2: Thông báo hủy/giải trình của NNT theo thông báo của CQT)')
    NTBCCQT = fields.Date('Ngày thông báo của CQT', readonly=True,
        states={'0': [('readonly', False)]}, help='Bắt buộc (Đối với Loại=2: Thông báo hủy/giải trình của NNT theo thông báo của CQT)')
    MCQT = fields.Char('Mã CQT quản lý', readonly=True,
        states={'0': [('readonly', False)]}, size=5)
    TCQT = fields.Char('Tên CQT', size=100)
    TNNT = fields.Char('Tên NNT', size=400, readonly=True,
        states={'0': [('readonly', False)]})
    MST = fields.Char('Mã số thuế', size=14, readonly=True,
        states={'0': [('readonly', False)]}, help='Bắt buộc (Trừ trường hợp là đơn vị bán tài sản công không có mã số thuế)')
    MDVQHNSach = fields.Char('Mã đơn vị quan hệ ngân sách', size=7, readonly=True,
        states={'0': [('readonly', False)]}, help='Mã số đơn vị có quan hệ với ngân sách của đơn vị bán tài sản công. Bắt buộc (Đối với đơn vị bán tài sản công không có Mã số thuế)', )
    DDanh = fields.Char('Địa danh', size=50, readonly=True,
        states={'0': [('readonly', False)]})
    NTBao = fields.Date('Ngày thông báo', default=fields.Date.today)


class InvoiceTB04LineMixin(models.AbstractModel):
    _name = 'wg.tb04.line.mixin'
    _description = 'Chi tiết thông báo Hóa đơn điện tử có sai sót'    


    STT = fields.Integer('Số thứ tự', help='Không bắt buộc')
    MCQTCap = fields.Char('Mã CQT cấp', size=34)
    KHMSHDon = fields.Char('Ký hiệu mẫu số hóa đơn', size=11)
    KHHDon = fields.Char('Ký hiệu hóa đơn', size=8)
    SHDon = fields.Char('Số hóa đơn', size=8)
    Ngay = fields.Date('Ngày lập')
    LADHDDT = fields.Selection([
        ('1', 'HĐĐT theo NĐ 123/2020/NĐ-CP'),
        ('2', 'HĐĐT có mã CQT theo NĐ 1209/QĐ-BTC và QĐ 2660/QĐ-BTC'),
        ('3', 'Các loại HĐ theo NĐ 51/2010/NĐ-CP, 04/2014/NĐ-CP trừ HĐ có mã CQT'),
        ('4', 'Hóa đơn đặt in theo Nghị định 123/2020/NĐ-CP'),
        ],'Loại áp dụng hóa đơn điện tử', default='1', help='HelpAboutField', )
    TCTBao = fields.Selection([
        ('0', 'Mới'),
        ('1', 'Hủy'),
        ('2', 'Điều chỉnh'),
        ('3', 'Thay thế'),
        ('4', 'Giải trình'),
        ('5', 'Sai sót do tổng hợp'),
        ], string='Tính chất thông báo', default='1')
    LDo = fields.Char('Lý do', size=255, help='Không bắt buộc')
