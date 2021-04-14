# -*- coding: utf-8 -*-
{
    'name': 'MOTGAMA',
    'version': '1.0',
    'summary': 'Gestión de Moteles (MOTGAMA)',
    'description': 'Aplicación para la gestión del motel.',
    'category': '',
    'website': 'https://www.sistemasgod.com',
    'author': 'Asesorias en Sistemas GOD S.A.S.',
    'images': [
        'static/src/img/estado_amarillo.png',
        'static/src/img/estado_azul.png',
        'static/src/img/estado_azulclaro.png',
        'static/src/img/estado_fucsia.png',
        'static/src/img/img/estado_naranjado.png',
        'static/src/img/estado_rojo.png',
        'static/src/img/estado_verde.png',
        'static/src/img/estado_cafe.png'
    ],
    'depends': [
        'base',
        'sale_management',
        'stock',
        'muk_web_client_refresh',
        'contacts',
        'mail',
        'web_notify',
        'account_cancel',
        'sh_message',
        'mrp',
        'stock_aux_report',
        'l10n_co'
    ],
    'installable': True,
    'application': True,
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'data/secuencia_docto.xml',
        'views/sucursal.xml',        
        'views/parametros.xml',
        'views/recepcion.xml',
        'views/habitacion.xml',
        'views/zona.xml', 
        'views/tema.xml',
        'views/tipo.xml',
        'wizard/wizard_fueradeservicio.xml',
        'wizard/wizard_fueradeuso.xml',              
        'wizard/wizard_desasigna.xml',
        'wizard/wizard_cambiodeplan.xml',
        'wizard/wizard_cambiohabitacion.xml',
        'wizard/wizard_recaudo.xml',
        'views/flujohabitacion.xml',
        'views/listapreciotipo.xml',
        'views/listapreciohabitacion.xml',
        'views/calendario.xml',
        'views/movimiento.xml',
        'views/comanda.xml',
        'views/consumo.xml',
        'views/reasignacion.xml',
        'wizard/wizardentregaolvidados.xml',
        'wizard/wizard_entregaprestados.xml',
        'views/objetosolvidados.xml',
        'views/objetosprestados.xml',
        'views/reserva.xml',
        'views/placa.xml',
        'views/inmotica.xml',
        'views/utilidades.xml',
        'views/prenda.xml',
        'views/bonos.xml',
        'views/menu.xml',
        'views/res_users.xml',
        'views/product_category.xml',
        'views/reporte_consumo.xml',
        'views/reporte_hospedaje.xml',
        'views/reporte_recaudos.xml',
        'views/reporte_documentos.xml',
        'views/cambioplan.xml',
        'views/comodidades.xml',
        'views/confirm_prestados.xml',
        'wizard/wizard_prenda.xml',
        'views/sale_order.xml',
        'views/account_invoice.xml',
        'views/res_company.xml',
        'wizard/wizard_precuenta.xml',
        'views/consumo_adicional.xml',
        'wizard/wizard_modificareservas.xml',
        'views/mediopago.xml',
        'views/recaudo.xml',
        'views/log.xml',
        'wizard/wizard_recaudoreserva.xml',
        'wizard/wizard_abonos.xml',
        'views/interfazcontable.xml',
        'views/product_template.xml',
        'wizard/wizard_descuento.xml',
        'views/reporte_ventas.xml',
        'wizard/wizard_anomalia.xml',
        'wizard/wizard_editarecaudo.xml',
        'wizard/wizard_docto.xml',
        'views/account.xml',
        'wizard/wizard_payment.xml',
        'templates/formato_papel_tirilla.xml',
        'templates/formato_estadocuenta.xml',
        'templates/formato_factura.xml',
        'templates/formato_prenda_pagare.xml',
        'templates/formato_recaudo.xml',
        'automation/accion_reservas.xml',
        'automation/accion_flujohabitacion.xml',
        'automation/accion_interfazcontable.xml',
        'data/secuencia_prenda.xml',
        'data/secuencia_recaudo.xml',
        'data/cliente_contado.xml',
        'data/medios_pago.xml',
        'data/permisos.xml',
        'reports/formato_reporte.xml',
        'reports/reporte_consumos.xml',
        'reports/reporte_documentos.xml',
        'reports/reporte_hospedaje.xml',
        'reports/reporte_recaudo.xml',
        'reports/reporte_ventas.xml',
        'reports/reporte_anomalias.xml',
        'reports/reporte_saldos.xml']
}
