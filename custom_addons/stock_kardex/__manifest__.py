# Copyright 2020 Asesorías en Sistemas GOD S.A.S (http://sistemasgod.com)

{
    'name': 'Reporte de Inventario: Kardex',
    'summary': 'Agrega el informe tipo Kardex de inventario',
    'version': '1.0',
    'category': 'Warehouse',
    'website': 'https://sistemasgod.com',
    'author': 'Asesorías en Sistemas GOD S.A.S',
    'depends': [
        'stock',
        'date_range',
        'report_xlsx_helper',
    ],
    'data': [
        'data/paper_format.xml',
        'data/report_data.xml',
        'reports/stock_card_report.xml',
        'wizard/stock_card_report_wizard_view.xml',
    ],
    'installable': True,
}
