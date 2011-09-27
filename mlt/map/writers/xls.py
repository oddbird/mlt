import xlwt

from .base import AddressWriter



class XLSWriter(AddressWriter):
    mimetype = "application/vnd.ms-excel"
    extension = "xls"


    def save(self, stream):
        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet("Addresses")

        for col, fn in enumerate(self.field_names):
            sheet.write(0, col, fn)

        for row, row_data in enumerate(self.serialized(), 1):
            for col, fn in enumerate(self.field_names):
                sheet.write(row, col, row_data[fn])

        workbook.save(stream)
