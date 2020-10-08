{
    'name': 'Reporte Auxiliar de Inventario',
    'summary': 'Agrega el reporte auxiliar a la aplicación de inventario',
    'version': '12.0.1.0',
    'category': 'Warehouse',
    'website': 'https://sistemasgod.com',
    'author': 'Asesorías en Sistemas GOD S.A.S',
    'depends': [
        'stock'
    ],
    'data': [
        'reports/formato_reporte.xml',
        'reports/stock_aux_report.xml',
        'wizard/stock_aux_report_wizard.xml'
    ],
    'installable': True
}