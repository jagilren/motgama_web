from odoo import models, fields, api, _

class Users(models.Model):
    _inherit = "res.users"

    # Flujo de habitaciones
    motgama_asigna = fields.Boolean(string='Puede asignar habitaciones',default=False)
    motgama_desasigna = fields.Boolean(string='Puede desasignar habitaciones',default=False)
    motgama_reasigna_mayor = fields.Boolean(string='Puede reasignar habitaciones de mayor o igual valor',default=False)
    motgama_reasigna_menor = fields.Boolean(string='Puede reasignar habitaciones de menor valor',default=False)
    motgama_liquida_habitacion = fields.Boolean(string='Puede liquidar habitaciones',default=False)
    motgama_recauda_habitacion = fields.Boolean(string='Puede recaudar habitaciones',default=False)
    motgama_habilita_habitacion = fields.Boolean(string='Puede habilitar habitaciones',default=False)
    motgama_fuera_uso = fields.Boolean(string='Puede cambiar de estado las habitaciones a fuera de uso',default=False)
    motgama_fuera_servicio = fields.Boolean(string='Puede cambiar de estado las habitaciones a fuera de servicio',default=False)
    motgama_cambio_plan = fields.Boolean(string='Puede cambiar ocupación de habitaciones',default=False)

    # Consumos
    motgama_consumo_negativo = fields.Boolean(string='Puede agregar consumos negativos',default=False)

    # Descuentos y bonos
    motgama_descuento_servicio = fields.Boolean(string='Puede agregar descuentos por mal servicio',default=False)
    motgama_pase_cortesia = fields.Boolean(string='Puede habilitar habitaciones',default=False)

    # Prendas
    motgama_recauda_prenda = fields.Boolean(string='Puede recaudar prendas',default=False)

    # Anticipos
    motgama_ingreso_anticipo = fields.Boolean(string='Puede ingresar anticipos a habitaciones sin liquidar',default=False)
    
    # Objetos prestados
    motgama_devuelve_prestados = fields.Boolean(string='Puede registrar devolución de objetos prestados',default=False)

    # Facturación
    motgama_factura_extemporanea = fields.Boolean(string='Puede generar estados y facturas no asociadas a hospedaje',default=False)
    
    # Objetos olvidados
    motgama_entregar_olvidados = fields.Boolean(string='Puede entregar y dar de baja a objetos olvidados',default=False)
    
    # Informes
    motgama_informe_consumos = fields.Boolean(string='Puede generar informe de consumos',default=False)
    motgama_informe_ocupaciones = fields.Boolean(string='Puede generar informe de ocupaciones',default=False)
    motgama_informe_recaudos = fields.Boolean(string='Puede generar informe de recaudos',default=False)
    motgama_informe_diariovtas = fields.Boolean(string='Puede generar informe diario de ventas',default=False)
    motgama_informe_movimientos = fields.Boolean(string='Puede generar informe de movimientos',default=False)

    # Administración
    motgama_cambia_precios = fields.Boolean(string='Puede actualizar precios de habitaciones',default=False)