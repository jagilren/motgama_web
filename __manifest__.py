# -*- coding: utf-8 -*-
{
    'name':'MOTGAMA',
    'version':'0.0.1',
    'summary':'Gestión de Moteles (MOTGAMA)',
    'description':'Aplicación para la gestión del motel.',
    'category':'',
    'website':'https://www.sistemasgod.com',
    'author':'Asesorias en Sistemas GOD S.A.S.',
    'images':['static/src/img/estado_amarillo.png','static/src/img/estado_azul.png','static/src/img/estado_azulclaro.png','static/src/img/estado_fucsia.png','static/src/img/img/estado_naranjado.png','static/src/img/estado_rojo.png','static/src/img/estado_verde.png','static/src/img/estado_cafe.png'],
    'depends':['base','sale_management','stock','muk_web_client_refresh'],
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
        'views/motgama_flujohabitacion.xml',
        'views/motgama_listapreciotipo.xml',
        'views/motgama_listapreciohabitacion.xml',
        'views/motgama_calendario.xml',
        'views/motgama_movimiento.xml',
        'views/motgama_consumo.xml',
        'views/motgama_placa.xml',
        'views/motgama_cambioprecios.xml',
        # 'views/motgama_pago.xml',
        'views/motgama_bonos.xml',
        # 'views/motgama_wizard_recepcion.xml',
        # 'views/motgama_cierreturno.xml',
        'views/motgama_menu.xml',],
}
