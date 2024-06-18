# 3. Định dạng thông báo Mẫu số 01/TB-KTDL về việc kết quả kiểm tra dữ liệu hóa đơn điện tử
class InvoiceTB04(models.AbstractModel):
    _name = 'wg.tb04'
    _description = 'Thông báo Hóa đơn điện tử có sai sót'

    PBan = fields.Char('Phiên bản XML', size=6, default='2.0.1', help='Phiên bản XML (Trong Quy định này có giá trị là 2.0.1)')
    # DANH MỤC MẪU SỐ TỜ KHAI, THÔNG BÁO, ĐỀ NGHỊ
    # 01/ĐKTĐ-HĐĐT - Tờ khai đăng ký/thay đổi thông tin sử dụng hóa đơn điện tử theo quy định tại Nghị định 123/2020/NĐ-CP
    # 04/SS-HĐĐT - Thông báo hóa đơn điện tử có sai sót
    # 06/ĐN-PSĐT - Đơn đề nghị cấp hóa đơn điện tử có mã của CQT theo từng lần phát sinh theo quy định tại Nghị định 123/2020/NĐ-CP
    # 01/TH-HĐĐT - Bảng tổng hợp dữ liệu hóa đơn điện tử theo quy định tại Nghị định 123/2020/NĐ-CP
    # 03/DL-HĐĐT - Tờ khai dữ liệu hóa đơn, chứng từ hàng hóa, dịch vụ bán ra theo quy định tại Nghị định 123/2020/NĐ-CP
    # 01/TB-TNĐT - Về việc tiếp nhận/không tiếp nhận tờ khai đăng ký/thay đổi thông tin sử dụng HĐĐT theo quy định tại Nghị định 123/2020/NĐ-CP
    # 01/TB-ĐKĐT - Thông báo về việc chấp nhận/không chấp nhận đăng ký/thay đổi thông tin sử dụng HĐĐT theo quy định tại Nghị định 123/2020/NĐ-CP
    # 01/TB-SSĐT - Thông báo về việc tiếp nhận và kết quả xử lý về việc hóa đơn điện tử đã lập có sai sót theo quy định tại Nghị định 123/2020/NĐ-CP
    # 01/TB-RSĐT - Thông báo về hóa đơn điện tử cần rà soát theo quy định tại Nghị định 123/2020/NĐ-CP
    # 01/TB-KTDL - Thông báo về việc kết quả kiểm tra dữ liệu hóa đơn điện tử theo quy định tại Nghị định 123/2020/NĐ-CP
    # 01/TB-KTT - Thông báo về việc hết thời gian sử dụng hóa đơn điện tử có mã của cơ quan thuế không thu tiền và chuyển sang thông qua 
    #   Cổng thông tin điện tử Tổng cục Thuế/qua ủy thác tổ chức cung cấp dịch vụ về hóa đơn điện tử; không thuộc trường hợp 
    #   sử dụng hóa đơn điện tử không có mã của cơ quan thuế theo quy định tại Nghị định 123/2020/NĐ-CP
    # 01-1/QTr-HĐĐT - Thông báo phản hồi về hồ sơ đề nghị cấp hóa đơn điện tử có mã của cơ quan thuế theo từng lần phát sinh theo quy định tại Quy trình quản lý hóa đơn điện tử
    MSo = fields.Char('Mẫu số thông báo', size=15, default='04/SS-HĐĐT')
    Ten = fields.Char('Tên thông báo', size=255)
    So = fields.Char('Số thông báo', size=30)
    DDanh = fields.Char('Địa danh', size=50)
    NTBao = fields.Date('Ngày thông báo')
    MST = fields.Char('Mã số thuế', size=14, string='Bắt buộc (Trừ trường hợp là đơn vị bán tài sản công không có mã số thuế)')
    MDVQHNSach = fields.Char('Mã số đơn vị có quan hệ với ngân sách của đơn vị bán tài sản công', size=7, help='Bắt buộc (Đối với trường hợp đơn vị bán tài sản công không có Mã số thuế)')
    TNNT = fields.Char('Tên NNT', size=400)
    TGGui = fields.Date('Thời gian NNT gửi tới CQT')
    LTBao = fields.Char('Loại thông báo', size=1, default='1')
    CCu = fields.Char('Căn cứ (Tên loại thông điệp nhận)', size=255, help='Bắt buộc')
    MGDDTu = fields.Char('Căn Mã giao dịch điện tử', size=46, help='Không Bắt buộc')
    SLuong = fields.Char('Số lượng ', size=255, help='Số lượng (Số lượng dữ liệu trong gói)')


class InvoiceTB04Line(models.AbstractModel):
    _name = 'wg.tb04.line'
    _description = 'Chi tiết thông báo Hóa đơn điện tử có sai sót'


    # Thẻ TBao\DLTBao\LCMa chứa thông tin, danh sách lý do hóa đơn không đủ điều kiện cấp mã 
    # (Loại thông báo là “1- Thông báo hóa đơn không đủ điều kiện cấp mã)
    KHMSHDon = fields.Char('Ký hiệu mẫu số hóa đơn', size=11)
    KHHDon = fields.Char('Ký hiệu hóa đơn', size=6)
    SHDon = fields.Char('Số hóa đơn', size=8)
    NLap = fields.Date('Ngày lập')


    # Thẻ TBao\DLTBao\LCMa\DSLDo chứa danh sách lý do hóa đơn không đủ điều kiện cấp mã
    # Thẻ TBao\DLTBao\LCMa\DSLDo\LDo chứa lý do hóa đơn không đủ điều kiện cấp mã
    STT = fields.Integer('Số thứ tự', help='Không bắt buộc')
    MLoi = fields.Char('Mã lỗi', size=4, help='Bắt buộc')
    MTLoi = fields.Char('Mô tả lỗi', size=255, help='Bắt buộc')
    HDXLy = fields.Char('Hướng dẫn xử lý', size=255, help='Bắt buộc')
    GChu = fields.Char('Ghi chú', size=255, help='Không bắt buộc')

    # Thẻ TBao\DLTBao\LHDKMa chứa thông tin, danh sách các hóa đơn không mã không hợp lệ cùng danh sách lý do tương ứng 
    # (trường hợp Loại thông báo là “3- Thông báo kết quả đối chiếu sơ bộ thông tin từng hóa đơn không mã không hợp lệ)
    # Thẻ TBao\DLTBao\LHDKMa\DSHDon chứa danh sách các hóa đơn không mã không hợp lệ cùng danh sách lý do
    # Thẻ TBao\DLTBao\LHDKMa\DSHDon\HDon chứa thông tin từng hóa đơn không mã không hợp lệ cùng danh sách lý do
    KHMSHDon = fields.Char('Ký hiệu mẫu số hóa đơn', size=11)
    KHHDon = fields.Char('Ký hiệu hóa đơn', size=8)
    SHDon = fields.Char('Số hóa đơn', size=8)
    NLap = fields.Date('Ngày lập')

    # Thẻ TBao\DLTBao\LHDKMa\DSHDon\HDon\DSLDo chứa danh sách lý do không hợp lệ của từng hóa đơn
    # Thẻ TBao\DLTBao\LHDKMa\DSHDon\HDon\DSLDo\LDo chứa từng lý do không hợp lệ của từng hóa đơn
    MLoi = fields.Char('Mã lỗi', size=4, help='Bắt buộc')
    MTLoi = fields.Char('Mô tả lỗi', size=255, help='Bắt buộc')
    HDXLy = fields.Char('Hướng dẫn xử lý', size=255, help='Bắt buộc')
    GChu = fields.Char('Ghi chú', size=255, help='Không bắt buộc')

    # Thẻ TBao\DLTBao\LBTHKXDau chứa thông tin Bảng tổng hợp khác trường hợp bán xăng dầu, Tờ khai dữ liệu hóa đơn, chứng từ hàng hóa, dịch vụ bán ra không hợp lệ cùng lý do tương ứng 
    # (Loại thông báo là “4- Thông báo kết quả đối chiếu sơ bộ thông tin của Bảng tổng hợp khác xăng dầu, Tờ khai dữ liệu hóa đơn, chứng từ hàng hóa, dịch vụ bán ra không hợp lệ”)
    # Thẻ TBao\DLTBao\LBTHKXDau\DSBTHop chứa danh sách các Bảng tổng hợp khác trường hợp bán xăng dầu, Tờ khai dữ liệu hóa đơn, chứng từ hàng hóa, dịch vụ bán ra không hợp lệ cùng danh sách lý do tương ứng
    # Thẻ TBao\DLTBao\LBTHKXDau\DSBTHop\BTHop chứa thông tin từng Bảng tổng hợp khác trường hợp bán xăng dầu, Tờ khai dữ liệu hóa đơn, chứng từ hàng hóa, dịch vụ bán ra không hợp lệ cùng danh sách các lý do tương ứng
    STT = fields.Integer('Số thứ tự', help='Không bắt buộc')
    KDLieu = fields.Char('Kỳ dữ liệu ', size=10, help='Kỳ dữ liệu (Kỳ dữ liệu Bảng tổng hợp, Tờ khai dữ liệu)')
    LDau = fields.Integer('Lần đầu', help='Số (1: lần đầu, 0: bổ sung) - bắt buộc')
    BSLThu = fields.Integer('Bổ sung lần thứ', help='Bắt buộc (Đối với trường hợp LDau = 0)')
    SBTHDLieu = fields.Integer('Số thứ tự bảng tổng hợp dữ liệu', help='Số bảng tổng hợp dữ liệu (Số thứ tự bảng tổng hợp dữ liệu)')

    # Thẻ TBao\DLTBao\LBTHKXDau\DSBTHop\BTHop\DSLDTTChung chứa danh sách lý do không hợp lệ (nếu có) của thông tin chung Bảng tổng hợp, tờ khai dữ liệu
    # Thẻ TBao\DLTBao\LBTHKXDau\DSBTHop\BTHop\DSLDTTChung\ LDTTChung chứa từng lý do không hợp lệ của thông tin chung Bảng tổng hợp, tờ khai dữ liệu
    MLoi = fields.Char('Mã lỗi', size=4, help='Bắt buộc')
    MTLoi = fields.Char('Mô tả lỗi', size=255, help='Bắt buộc')
    HDXLy = fields.Char('Hướng dẫn xử lý', size=255, help='Bắt buộc')
    GChu = fields.Char('Ghi chú', size=255, help='Không bắt buộc')

    # Thẻ TBao\DLTBao\LBTHKXDau\DSBTHop\BTHop\DSLHDon chứa danh sách các hóa đơn thuộc Bảng tổng hợp, Tờ khai dữ liệu không hợp lệ (nếu có) cùng danh sách lý do
    # Thẻ TBao\DLTBao\LBTHKXDau\DSBTHop\BTHop\DSLHDon\HDon chứa từng hóa đơn thuộc Bảng tổng hợp, Tờ khai dữ liệu không hợp lệ cùng danh sách lý do
    STT = fields.Integer('Số thứ tự', help='Không bắt buộc')
    KHMSHDon = fields.Char('Ký hiệu mẫu số hóa đơn', size=11)
    KHHDon = fields.Char('Ký hiệu hóa đơn', size=8)
    SHDon = fields.Char('Số hóa đơn', size=8)
    NLap = fields.Date('Ngày lập')
    # Điều 10, Điều 22 Nghị định 123/2020/NĐ-CP
    TNMua = fields.Char('Tên người mua', size=400, help='Bắt buộc (Nếu có)')


    # Thẻ TBao\DLTBao\LBTHKXDau\DSBTHop\BTHop\DSLHDon\HDon\DSLDo chứa danh sách các lý do không hợp lệ của từng hóa đơn trong Bảng tổng hợp, Tờ khai dữ liệu không hợp lệ
    # Thẻ TBao\DLTBao\LBTHKXDau\DSBTHop\BTHop\DSLHDon\HDon\DSLDo\LDo chứa từng lý do không hợp lệ của từng hóa đơn trong Bảng tổng hợp, Tờ khai dữ liệu không hợp lệ
    MLoi = fields.Char('Mã lỗi', size=4, help='Bắt buộc')
    MTLoi = fields.Char('Mô tả lỗi', size=255, help='Bắt buộc')
    HDXLy = fields.Char('Hướng dẫn xử lý', size=255, help='Bắt buộc')
    GChu = fields.Char('Ghi chú', size=255, help='Không bắt buộc')

    # Thẻ TBao\DLTBao\LBTHXDau chứa thông tin Bảng tổng hợp trường hợp bán xăng dầu không hợp lệ cùng lý do tương ứng 
    # (Loại thông báo là “5- Thông báo kết quả đối chiếu sơ bộ thông tin của Bảng tổng hợp xăng dầu không hợp lệ”)
    # Thẻ TBao\DLTBao\LBTHXDau\DSBTHop chứa danh sách các Bảng tổng hợp trường hợp bán xăng dầu không hợp lệ cùng danh sách lý do tương ứng
    # Thẻ TBao\DLTBao\LBTHXDau\DSBTHop\BTHop chứa thông tin từng Bảng tổng hợp trường hợp bán xăng dầu không hợp lệ cùng danh sách các lý do tương ứng
    STT = fields.Integer('Số thứ tự', help='Không bắt buộc')
    KDLieu = fields.Char('Kỳ dữ liệu ', size=10, help='Kỳ dữ liệu (Kỳ dữ liệu Bảng tổng hợp, Tờ khai dữ liệu)')
    LDau = fields.Integer('Lần đầu', help='Số (1: lần đầu, 0: bổ sung) - bắt buộc')
    BSLThu = fields.Integer('Bổ sung lần thứ', help='Bắt buộc (Đối với trường hợp LDau = 0)')
    SBTHDLieu = fields.Integer('Số thứ tự bảng tổng hợp dữ liệu', help='Số bảng tổng hợp dữ liệu (Số thứ tự bảng tổng hợp dữ liệu)')

    # Thẻ TBao\DLTBao\LBTHXDau\DSBTHop\BTHop\DSLDTTChung chứa danh sách lý do không hợp lệ (nếu có) của thông tin chung Bảng tổng hợp, tờ khai dữ liệu
    # Thẻ TBao\DLTBao\LBTHXDau\DSBTHop\BTHop\DSLDTTChung\LDTTChung chứa từng lý do không hợp lệ của thông tin chung Bảng tổng hợp, tờ khai dữ liệu
    MLoi = fields.Char('Mã lỗi', size=4, help='Bắt buộc')
    MTLoi = fields.Char('Mô tả lỗi', size=255, help='Bắt buộc')
    HDXLy = fields.Char('Hướng dẫn xử lý', size=255, help='Bắt buộc')
    GChu = fields.Char('Ghi chú', size=255, help='Không bắt buộc')


    # Thẻ TBao\DLTBao\LBTHXDau\DSBTHop\BTHop\DSLMHang chứa danh sách các mặt hàng không hợp lệ (nếu có) cùng danh sách lý do tương ứng 
    # Thẻ TBao\DLTBao\LBTHXDau\DSBTHop\BTHop\DSLMHang\MHang chứa từng mặt hàng không hợp lệ thuộc Bảng tổng hợp cùng danh sách lý do tương ứng
    STT = fields.Integer('Số thứ tự', help='Không bắt buộc')
    MHHDVu = fields.Char('Mã hàng hóa, dịch vụ', size=50)
    THHDVu = fields.Char('Tên hàng hóa, dịch vụ', size=500)
    KDChinh = fields.Char('Kỳ điều chỉnh', size=10)

    # Thẻ TBao\DLTBao\LBTHXDau\DSBTHop\BTHop\DSLMHang\LMHang\DSLDo chứa danh sách các lý do không hợp lệ của từng mặt hàng trong Bảng tổng hợp
    # Thẻ TBao\DLTBao\LBTHXDau\DSBTHop\BTHop\DSLMHang\LMHang\DSLDo\LDo chứa từng lý do không hợp lệ của từng mặt hàng trong Bảng tổng hợp
    MLoi = fields.Char('Mã lỗi', size=4, help='Bắt buộc')
    MTLoi = fields.Char('Mô tả lỗi', size=255, help='Bắt buộc')
    HDXLy = fields.Char('Hướng dẫn xử lý', size=255, help='Bắt buộc')
    GChu = fields.Char('Ghi chú', size=255, help='Không bắt buộc')

    # Thẻ TBao\DLTBao\LDNCLe\DSLDo chứa danh sách các lý do không hợp lệ của đơn đề nghị cấp hóa đơn có mã theo từng lần phát sinh 
    # (Loại thông báo là “6- Thông báo kết quả đối chiếu sơ bộ thông tin Đơn đề nghị cấp hóa đơn điện tử có mã của CQT theo từng lần 
    # phát sinh với trường hợp NNT gửi đơn qua cổng thông tin điện tử của TCT”)
    # Thẻ TBao\DLTBao\LDNCLe\DSLDo\LDo chứa lý do không hợp lệ
    MLoi = fields.Char('Mã lỗi', size=4, help='Bắt buộc')
    MTLoi = fields.Char('Mô tả lỗi', size=255, help='Bắt buộc')
    HDXLy = fields.Char('Hướng dẫn xử lý', size=255, help='Bắt buộc')
    GChu = fields.Char('Ghi chú', size=255, help='Không bắt buộc')

    # Thẻ TBao\DLTBao\KHLKhac\DSLDo chứa thông tin, danh sách lý do không hợp lệ (Loại thông báo là “9- Thông báo kết quả đối chiếu thông tin gói dữ liệu không hợp lệ các trường hợp khác”)
    # Thẻ TBao\DLTBao\KHLKhac\DSLDo\LDo chứa lý do không hợp lệ
    STT = fields.Integer('Số thứ tự', help='Không bắt buộc')
    MLoi = fields.Char('Mã lỗi', size=4, help='Bắt buộc')
    MTLoi = fields.Char('Mô tả lỗi', size=255, help='Bắt buộc')
    HDXLy = fields.Char('Hướng dẫn xử lý', size=255, help='Bắt buộc')
    GChu = fields.Char('Ghi chú', size=255, help='Không bắt buộc')
    

