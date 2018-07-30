#!/usr/bin/env python  
# _#_ coding:utf-8 _*_ 
import xlwt


class CellWriter(object):
    def __init__(self, name):
        self.file_name = name
        self.workbook = xlwt.Workbook(encoding='utf-8')

    #         for sh in args:
    #             self.worksheet = self.workbook.add_sheet(sh)

    def fontStyle(self, bold=False):
        font = xlwt.Font()
        font.name = u"微软雅黑"
        font.bold = bold
        #         font.height = 20 * 12
        return font

    def borderStyle(self):
        borders = xlwt.Borders()
        borders.left = 1
        borders.right = 1
        borders.top = 1
        borders.bottom = 1
        return borders

    def writeBanner(self, sheetName, bList):
        for ds in bList:
            sheetName.write(0, bList.index(ds), ds, self.bodySttle(pattern=5,bold=True))

    def bodySttle(self, pattern=None,bold=False):
        style = xlwt.XFStyle()
        style.alignment.horz = 2
        style.alignment.vert = 1
        style.alignment.wrap = 1
        if pattern:
            pat = xlwt.Pattern()
            pat.pattern = xlwt.Pattern.SOLID_PATTERN
            pat.pattern_fore_colour = pattern
            style.pattern = pat
        style.font = self.fontStyle(bold=bold)
        style.borders = self.borderStyle()
        return style

    def save(self):
        self.workbook.save(self.file_name)
