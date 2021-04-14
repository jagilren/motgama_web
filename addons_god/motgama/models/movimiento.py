from odoo import models, fields, api

class MotgamaMovimiento(models.Model):#ok
#    Fields: MOVIMIENTO: .Modification date:  Mayo 9 del 2019: 
#        - res.users = Se ingresa codigo para obtener la informacion de usuario logeado y en es cual va a realizar los diferentes movimientos.
#        - asignatipo = Se selecciona que tipo de asignacion tiene la habitacion.
    _name = 'motgama.movimiento'
    _description = 'Movimiento'
    habitacion_id = fields.Many2one(string='Habitación',comodel_name='motgama.habitacion',ondelete='set null')
    tipovehiculo = fields.Selection(string='Tipo de vehiculo',selection=[('particular', 'Particular'), ('moto', 'Moto'), ('peaton', 'Peatón'),('taxi','Taxi')])
    placa_vehiculo = fields.Char(string='Placa del Vehiculo')
    asignatipo = fields.Selection(string='Tipo de Asignación',selection=[('OO', 'Ocasional'), ('OA', 'Amanecida')]) # (09/05/2019) 
   # asignafecha = fields.Date(string=u'Asignación de Fecha')
    asignafecha = fields.Datetime(string='Fecha de Movimiento',readonly=True, required=True,index=True,default=(lambda *a: time.strftime(dt)))
    asigna_uid = fields.Many2one(comodel_name='res.users',string='Usuario que asigna')
   # liquidafecha = fields.Date(string=u'Liquida Fecha')
    liquidafecha= fields.Datetime(string='Fecha y hora Liquidacion')
    liquida_uid = fields.Many2one(comodel_name='res.users',string='Usuario que liquida')
   # recaudafecha = fields.Date(string=u'Fecha de recaudo')
    recaudafecha = fields.Datetime(string='Fecha y hora de recaudo')
    recauda_uid = fields.Many2one(comodel_name='res.users',string='Usuario que recauda')
    factura = fields.Many2one(string='Factura',comodel_name='account.invoice')
   # aseofecha = fields.Date(string=u'Fecha de aseo')
    aseofecha = fields.Datetime(string='Fecha y hora aseo')
    aseo_uid = fields.Many2one(comodel_name='res.users',string='Usuario que cambia al estado aseo')
   # habilitafecha = fields.Date(string=u'Fecha de habilitación')
    habilitafecha = fields.Datetime(string='Fecha y hora en que se habilita')
    habilita_uid = fields.Many2one(comodel_name='res.users',string='Usuario que habilita la habitación')
   # reasignafecha = fields.Date(string=u'Fecha de reasignación')
    # reasignafecha = fields.Datetime(string=u'Fecha y Hora de reasignación')
    # reasigna_uid = fields.Many2one(comodel_name='res.users',string='Usuario responsable',default=lambda self: self.env.user.id)
    # reasignanueva_id = fields.Char(string=u'Reasignacion Nueva') # Este es un Integer Many2One de donde sale *
    # reasignaanterior_uid = fields.Char(string=u'Reasignacion Anterior') # Este es un Integer Many2One de donde sale *
    flagreasignada = fields.Boolean(string='Reasignada')
    reasignaciones = fields.One2many(string='Reasignaciones',comodel_name='motgama.reasignacion',inverse_name='movimiento_id')
   # reservafecha = fields.Date(string=u'Fecha de la reserva')
    reserva = fields.Many2one(string="Reserva",comodel_name="motgama.reserva")
   # desasignafecha = fields.Date(string=u'Fecha de la desasigna')
    desasignafecha = fields.Datetime(string='Fecha y Hora de la desasigna')
    desasigna_uid = fields.Many2one(comodel_name='res.users',string='Usuario que desasigna')
    incluyedecora = fields.Boolean(string='Incluye decoración')    
    tarifaocasional = fields.Float(string='Tarifa ocasional')
    tarifamanecida = fields.Float(string='Tarifa amanecida')
    tarifahoradicional = fields.Float(string='Tarifa hora adicional')    
    # tarifapersonadicional = fields.Float(string=u'Tarifa persona adicional') # REVISAR YA NO VA PORQUE ES UN PRODUCTO MAS
    tiemponormalocasional = fields.Integer(string='Tiempo ocasional normal')
    active = fields.Boolean(string='Activo?',default=True)
    anticipo = fields.Float(string='Valor anticipo')
    formapagoanticipo = fields.Char(string='Forma pago anticipo')
    reciboanticipo = fields.Float(string='Nro recibo caja anticipo')
    ordenVenta = fields.Many2one(string='Estado de cuenta',comodel_name='sale.order')
    # Proceso de Fuera de servicio
    fueradeserviciohora = fields.Datetime(string='Fecha fuera de servicio')
    fueradeservicio_uid = fields.Many2one(comodel_name='res.users',string='Usuario que cambia de estado a fuera de servicio')
    # Proceso de Fuera de uso
    fueradeusohora = fields.Datetime(string='Fecha fuera de uso')
    fueradeuso_uid = fields.Many2one(comodel_name='res.users',string='Usuario que cambia de estado a fuera de uso')
    fueradeuso_usuarioorden = fields.Char(string='Persona que dio la orden')
    # Se agrega lista de precios traida del calendario según el día de la semana
    listaprecioproducto = fields.Many2one(string='Lista precio Productos',comodel_name='product.pricelist')
    observacion = fields.Text(string='Observación')
    horainicioamanecida = fields.Datetime(string='Hora Inicio Amanecida')
    horafinamanecida = fields.Datetime(string='Hora Fin Amanecida')
    hubocambioplan = fields.Boolean(string='¿Hubo cambio de plan en el movmiento?',default=False)
    cambiosplan = fields.One2many(string="Cambios de plan",comodel_name='motgama.cambioplan',inverse_name='movimiento')
    prestados = fields.One2many(string="Objetos Prestados",comodel_name='motgama.objprestados',inverse_name='movimiento_id')
    recaudo_ids = fields.One2many(string="Recaudos",comodel_name="motgama.recaudo",inverse_name='movimiento_id')
    bono_id = fields.Many2one(string='Bono aplicado',comodel_name='motgama.bonos')
    factura_ids = fields.One2many(string='Facturas y rectificativas',comodel_name='account.invoice',inverse_name='movimiento_id')

class MotgamaHistoricoMovimiento(models.Model):#ok
#    Fields:  PENDIENTE REVISAR
# HISTORICO DE MOVIMIENTO:  Este movimiento tiene la replica exacta de motgama.movimiento y se escoje el año que se quiere trasladar
    _name = 'motgama.hcomov' #Historico Movimiento
    _description = 'MotgamaHistoricoMovimiento' 
    _rec_name = 'anio'
    _order = 'anio ASC'
    anio = fields.Char(string='Año')
    active = fields.Boolean(string='Activo?',default=True)