# -*- coding: utf-8 -*-
# hola
{
    'name':'MOTGAMA',
    'version':'0.0.1',
    'summary':'Gestión de Moteles (MOTGAMA)',
    'description':'Aplicación para la gestión del motel.',
    'category':'',
    'website':'https://www.sistemasgod.com',
    'author':'Asesorias en Sistemas GOD S.A.S.',
    'images':['static/src/img/estado_amarillo.png','static/src/img/estado_azul.png','static/src/img/estado_azulclaro.png','static/src/img/estado_fucsia.png','static/src/img/img/estado_naranjado.png','static/src/img/estado_rojo.png','static/src/img/estado_verde.png','static/src/img/estado_cafe.png'],
    'depends':['base','sale_management','stock','muk_web_client_refresh','contacts'],
    'installable':True,
    'application': True,
    'data':['security/groups.xml',
        'security/ir.model.access.csv',       
        'views/motgama_sucursal.xml',        
        'views/motgama_parametros.xml',
        'views/motgama_recepcion.xml',
        'views/motgama_habitacion.xml',
        'views/motgama_zona.xml', 
        'views/motgama_tema.xml',
        'views/motgama_tipo.xml',
        'views/motgama_wizard_fueradeservicio.xml',
        'views/motgama_wizard_fueradeuso.xml',              
        'views/motgama_wizard_desasigna.xml',
        'views/motgama_wizard_cambiodeplan.xml',
        'views/motgama_wizard_cambiohabitacion.xml',
        'views/motgama_wizard_recaudo.xml',
        'views/motgama_flujohabitacion.xml',
        'views/motgama_listapreciotipo.xml',
        'views/motgama_listapreciohabitacion.xml',
        'views/motgama_calendario.xml',
        'views/motgama_movimiento.xml',
        'views/motgama_comanda.xml',
        'views/motgama_consumo.xml',
        'views/motgama_reasignacion.xml',
        'views/motgama_wizardentregaolvidados.xml',
        'views/motgama_wizard_entregaprestados.xml',
        'views/motgama_objetosolvidados.xml',
        'views/motgama_objetosprestados.xml',
        'views/motgama_reserva.xml',
        'views/motgama_placa.xml',
        'views/motgama_inmotica.xml',
        'views/motgama_utilidades.xml',
        'views/motgama_prenda.xml',
        # 'views/motgama_pago.xml',
        'views/motgama_bonos.xml',
        # 'views/motgama_cierreturno.xml',
        'views/motgama_menu.xml',
        'views/res_users.xml',
        'views/product_category.xml',
        'views/motgama_reporte_consumo.xml',
        'reports/reporte_consumos.xml',
        'views/motgama_reporte_hospedaje.xml',
        'views/motgama_cambioplan.xml',
        'views/motgama_comodidades.xml',
        'views/motgama_confirm_prestados.xml',
        'views/motgama_wizard_prenda.xml']
}
