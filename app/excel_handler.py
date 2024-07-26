from RPA.Excel.Files import Files
import logging

logger = logging.getLogger(__name__)

class ExcelHandler():
    def __init__(self, filename):
        self.filename = filename
        self.HEADERS = False
        self.excel = Files()

    
    def _create_workbook_and_header(self, headers:list):
        logging.debug('Creating Excel and Headers')
        self.excel.create_workbook(f'{self.filename}')
        self.excel.append_rows_to_worksheet([headers], "Sheet")
        self.HEADERS = True

    def _update_row(self, items:dict):
        if not self.HEADERS:
            self._create_workbook_and_header(list(items.keys()))
        self.excel.append_rows_to_worksheet([list(items.values())], "Sheet")
        self.excel.save_workbook(self.filename)

    def _save_and_close_workbook(self):
        self.excel.save_workbook(self.filename)
        self.excel.close_workbook()