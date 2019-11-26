# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError,Warning, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as dt

###############################################################################
#    License, author and contributors information in:                         
#       __manifest__.py file at the root folder of this module.  
#        ERP ODOO por defecto crea la siguiente estructura  de base de datos                          
#           create_date : timestamp
#           create_uid : Integer
#           write_date : timestamp
#           write_uid : Integer
#           __last_update : timestamp
#           active : Boolean
#       Creation date: Abril 1 del 2019
#       Author: Asesorias en Sistemas G.O.D S.A.S
#       Developers: Luis David Ortiz Restrepo
#       Project Director: Arnaldo Franco, Ing. Marta Restrepo
###############################################################################

class MotgamaSucursal(models.Model):#ok
#    Fields:SUCURSAL: Cada una de las sedes (Moteles).                                                      #P7.0.4R
    _name = 'motgama.sucursal'
    _description = u'Motgama Sucursal'
    _rec_name = 'nombre'
    _order = 'nombre ASC'
    _sql_constraints = [('codigo_uniq', 'unique (codigo)', "El Código ya Existe, Verifique!")]
    codigo = fields.Char(string=u'Código',)
    nombre = fields.Char(string=u'Nombre Sucursal',required=True,)
    telefono = fields.Char(string=u'Teléfono',)
    direccion = fields.Text(string=u'Dirección',)
    ciudad = fields.Char(string=u'Ciudad',)
    email = fields.Char(string=u'Correo Electronico')
    razonsocial_id = fields.Many2one(string=u'Razón Social',comodel_name='res.company',ondelete='set null')
    nit = fields.Char(string=u'Nit')# 11 julio 2019
    active = fields.Boolean(string=u'Activo?', default=True)
    #RECEPCIONES EN ESTA SUCURSAL
    recepcion_ids = fields.One2many(string=u'Recepciones en esta sucursal',comodel_name='motgama.recepcion', inverse_name='sucursal_id')
 

#Inmotica por parte de Jonny
class MotgamaInmotica(models.Model):#ok
    #Fields:Inmotica: Conexion interna entre base de datos.    
    _name = 'motgama.inmotica'
    _description = u'Inmotica'
#    _rec_name = 'habitacion_id'
    sucursal_id = fields.Many2one(string=u'Sucursal',comodel_name='motgama.sucursal',ondelete='set null')
    habitacion = fields.Char(string=u'Habitacion')
    parametro = fields.Char(string=u'parametro',required=True,)
    control_accion = fields.Char(string=u'String Control Accion',required=True,)
    fecha = fields.Datetime ()
    usuario_uid = fields.Integer(string=u'Usuario',)
    active = fields.Boolean(string=u'Activo?',default=True,)
    
class MotgamaParametros(models.Model):#ok
#   Fields: PARAMETROS: se deben de definir todos los parametros que se necesitan por sucursal.
    _name = 'motgama.parametros'
    _description = u'parametros'
    sucursal_id = fields.Many2one(string=u'Sucursal',comodel_name='motgama.sucursal',ondelete='set null')
    codigo = fields.Char(string=u'Codigo',)
    nombre = fields.Char(string=u'Nombre',)
    valor = fields.Char(string=u'Valor',)
    active = fields.Boolean(string=u'Activo?',default=True,)

class MotgamaCalendario(models.Model):#ok
#    Fields:CALENDARIO: Listas de precios a aplicar por cada dia de la semana, diurno y nocturno
    _name = 'motgama.calendario'
    _description = u'Calendario'
    _rec_name = 'diasemana'
    _order = 'diasemana ASC'
    _sql_constraints = [('codigo_uniq', 'unique (diasemana)', "El dia ya Existe, Verifique!")]
    diasemana = fields.Selection(string=u'Día Semana',selection=[('0', 'Lunes'), ('1', 'Martes'), ('2', 'Miércoles'), ('3', 'Jueves'), ('4', 'Viernes'), ('5', 'Sábado'), ('6', 'Domingo')])
    listapreciodia = fields.Selection(string=u'Lista precio Día ',selection=[('1', 'L1'),('2', 'L2'),('3', 'L3'),('4', 'L4'),('5', 'L5')],required=True)    
    listaprecionoche = fields.Selection(string=u'Lista precio Noche',selection=[ ('1', 'L1'),('2', 'L2'),('3', 'L3'),('4', 'L4'),('5', 'L5')],required=True)
    listaprecioproducto = fields.Many2one(string=u'Lista precio Productos',comodel_name='product.pricelist',required=True) #Toma listas de odoo
    horainicioamanecida=fields.Char(string='H inic.Amanec.(hh:mm)')
    horafinamanecida=fields.Char(string='H Fin.Amanec.(hh:mm)')
    tiemponormalocasional = fields.Integer(string=u'Tiempo ocasional normal')
    flagignoretiempo = fields.Boolean(string=u'Ignore Tiempo',default=False,)
    sucursal_id = fields.Many2one(string=u'Sucursal',comodel_name='motgama.sucursal',ondelete='set null',)
    active = fields.Boolean(string=u'Activo?',default=True)

class MotgamaRecepcion(models.Model):#ok
#    Fields: RECEPCION: Aca estaran las diferentes recepciones por lo general sera RECEPCION A y RECEPCION B.
    _name = 'motgama.recepcion'
    _description = u'Recepción'
    _rec_name = 'nombre'
    _order = 'nombre ASC'
    _sql_constraints = [('codigo_uniq', 'unique (codigo)', "El Código ya Existe, Verifique!")]
    sucursal_id = fields.Many2one(string=u'Sucursal',comodel_name='motgama.sucursal',ondelete='set null',)
    codigo = fields.Char(string=u'Código',) 
    nombre = fields.Char(string=u'Recepción',required=True)
    active = fields.Boolean(string=u'Activo?',default=True)
    zonas_ids = fields.One2many(string=u'Zonas en esta recepción',comodel_name='motgama.zona',inverse_name='recepcion_id') #LAS ZONAS EN ESTA RECEPCION

    @api.model
    def create(self,values):
        record = super().create(values)

        parent = self.env['stock.location'].search([('name','=','MOTGAMA')],limit=1)
        if not parent:
            valores = {
                'name' : 'MOTGAMA',
                'usage' : 'internal',
                'permite_consumo' : False
            }
            parent = self.env['stock.location'].create(valores)
            if not parent:
                raise Warning('No existe ni se pudo crear el lugar de inventario "MOTGAMA", contacte al administrador')

        valoresLugar = {
            'name' : record.nombre,
            'recepcion' : record.id,
            'usage' : 'internal',
            'location_id' : parent.id,
            'permite_consumo' : True
        }
        nuevoLugar = self.env['stock.location'].create(valoresLugar)
        if not nuevoLugar:
            raise Warning('Error al crear recepción: No se pudo crear el lugar de inventario para la nueva recepción')

        return record
    
    @api.multi
    def write(self,values):
        creado = super(MotgamaRecepcion, self).write(values)

        lugar = self.env['stock.location'].search([('recepcion','=',self.id)],limit=1)
        if not lugar:
            parent = self.env['stock.location'].search([('name','=','MOTGAMA')],limit=1)
            if not parent:
                valores = {
                    'name' : 'MOTGAMA',
                    'usage' : 'internal',
                    'permite_consumo' : False
                }
                parent = self.env['stock.location'].create(valores)
                if not parent:
                    raise Warning('No existe ni se pudo crear el lugar de inventario "MOTGAMA", contacte al administrador')

            valoresLugar = {
                'name' : self.nombre,
                'recepcion' : self.id,
                'usage' : 'internal',
                'location_id' : parent.id,
                'permite_consumo' : True
            }
            lugar = self.env['stock.location'].create(valoresLugar)
            if not lugar:
                raise Warning('Error al crear el lugar de inventario para la recepción')
        else:
            lugar.write({'name':self.nombre})
        
        return creado
        

class MotgamaLugares(models.Model):#ok OJO
#    Fields: LUGARES: esta tiene una similitud con el modulo de inventarios de ERP ODOO
#     TODO: ESTA EN ESPERA YA QUE SE PUEDE CONECTAR CON EL MODULO DE INVENTARIOS QUE TRAE ODOO
    _name = 'motgama.lugares'
    _description = u'Bodega'
    sucursal_id = fields.Many2one(string=u'Sucursal',comodel_name='motgama.sucursal',ondelete='set null')
    recepcion_id = fields.Many2one(string=u'Recepción',comodel_name='motgama.recepcion',ondelete='set null')

class MotgamaZona(models.Model):#ok
#    Fields: ZONA: Zona equivale a pisos que tiene los moteles.                                                     #P7.0.4R
    _name = 'motgama.zona'
    _description = u'Zona'
    _sql_constraints = [('codigo_uniq', 'unique (codigo)', "El Código ya Existe, Verifique!")]
    _rec_name = 'nombre'
    _order = 'nombre ASC'
    sucursal_id = fields.Many2one(string=u'Sucursal',comodel_name='motgama.sucursal',ondelete='set null')
    recepcion_id = fields.Many2one(string=u'Recepción',comodel_name='motgama.recepcion',ondelete='set null')
    codigo = fields.Char(string=u'Código') 
    nombre = fields.Char(string=u'Nombre de la zona',required=True,)
    active = fields.Boolean(string=u'Activo?',default=True)
    habitacion_ids = fields.One2many(string=u'Habitaciones en esta zona',comodel_name='motgama.habitacion',inverse_name='zona_id',) # HABITACION EN ESTA ZONA

class MotgamaTipo(models.Model):#ok Tipo de habitaciones
#    Fields: TIPO DE HABITACION: Caracteristicas de las habitaciones y datos generales para el mismo tipo
    _name = 'motgama.tipo'
    _description = u'Tipo de habitación'
    _rec_name = 'nombre'
    _order = 'nombre ASC'
    _sql_constraints = [('codigo_uniq', 'unique (codigo)', "El Código ya Existe, Verifique!")]
    codigo = fields.Char(string=u'Código') 
    nombre = fields.Char(string=u'Nombre',required=True,)
    tiemponormalocasional = fields.Integer(string=u'Tiempo normal')
    minibar = fields.Boolean(string=u'Minibar',)
    turco = fields.Boolean(string=u'Turco',)
    jacuzzi = fields.Boolean(string=u'Jacuzzi',)
    camamov = fields.Boolean(string=u'Cama Movil',)
    smartv = fields.Boolean(string=u'Smart TV',)
    barrasonido = fields.Boolean(string=u'Barra Sonido',)
    hometheater = fields.Boolean(string=u'Home Theater')
    poledance = fields.Boolean(string=u'Pole Dance',)
    sillatantra = fields.Boolean(string=u'Silla Tantra')
    columpio = fields.Boolean(string=u'Columpio')
    aireacond = fields.Boolean(string=u'Aire Acond')
    garajecarro = fields.Boolean(string=u'Garaje Carro')
    garajemoto = fields.Boolean(string=u'Garaje Moto')
    piscina = fields.Boolean(string=u'Piscina')
    miniteca = fields.Boolean(string=u'Miniteca')
    sauna = fields.Boolean(string=u'Sauna')
    balcon = fields.Boolean(string=u'Balcon')
    active = fields.Boolean(string=u'Activo?',default=True)
    # Habitaciones con este tipo 
    habitacion_ids = fields.One2many(string=u'Habitaciones con este tipo',comodel_name='motgama.habitacion',inverse_name='tipo_id')
    # Enlaza las listas de precios por tipo
    listapreciotipo_ids = fields.One2many('motgama.listapreciotipo', 'tipo_id', string='Listas de precios')

class MotgamaFlujoHabitacion(models.Model):#adicionada por Gabriel sep 10
    _name = 'motgama.flujohabitacion'
    _description = u'Flujo Habitación'
    _rec_name = 'codigo'
    _sql_constraints = [('codigo_uniq', 'unique (codigo)', "El código habitación ya Existe, Verifique!")]

    _inherit = 'base'

    codigo = fields.Char(string=u'Código')
    estado = fields.Selection(string=u'Estado',selection=[('D', 'Disponible'), ('OO', 'Ocupado Ocasional'), ('OA', 'Ocupado Amanecida'), ('LQ', 'Liquidada'),  ('RC', 'Camarera'), ('R', 'Reservada'), ('FS', 'Fuera de Servicio'), ('FU', 'Fuera de Uso')],default='D')
    ultmovimiento = fields.Many2one(string='Ultimo movimiento',comodel_name='motgama.movimiento',ondelete='set null')
    recepcion = fields.Many2one(string=u'Recepcion',comodel_name='motgama.recepcion',ondelete='restrict')
    active = fields.Boolean(string=u'Activo?',default=True)
    tipo = fields.Many2one(string='Tipo de Habitación',comodel_name='motgama.tipo',compute='_compute_habitacion',store=True)
    tema = fields.Many2one(string='Tema',comodel_name='motgama.tema',compute='_compute_habitacion',store=True)

    # Cuenta de cobro:
    orden_venta = fields.Many2one(string='Cuenta de Cobro',comodel_name='sale.order',ondelete='set null')

    #Función para abrir la información de la habitación cuando el usuario le de click
    @api.multi 
    def open_record(self):
        return {
            'type': 'ir.actions.act_window', 
            'res_model': 'motgama.flujohabitacion', 
            'name': 'boton', 
            'view_type': 'form', 
            'view_mode': 'form', 
            'res_id': self.id, 
            'target': 'current' 
        }
    
    @api.multi
    def write(self, values):
        record = super(MotgamaFlujoHabitacion, self).write(values)
        self.refresh_views()
        return record

    @api.model
    def create(self, values):
        record = super(MotgamaFlujoHabitacion, self).create(values)
        self.refresh_views()
        return record
    
    @api.depends('codigo')
    def _compute_habitacion(self):
        for record in self:
            if not record.codigo:
                break
            habitacion = self.env['motgama.habitacion'].search([('codigo','=',record.codigo)], limit=1)
            record.tipo = habitacion.tipo_id.id
            record.tema = habitacion.tema_id.id

class MotgamaHabitacion(models.Model):#ok
    _name = 'motgama.habitacion'
    _description = u'Habitación'
    _rec_name = 'codigo'
    _sql_constraints = [('codigo_uniq', 'unique (codigo)', "El Código ya Existe, Verifique!")]
    codigo = fields.Char(string=u'Código')
    nombre = fields.Char(string=u'Nombre') 
    zona_id = fields.Many2one(string=u'Zona',comodel_name='motgama.zona',ondelete='set null')
    tipo_id = fields.Many2one(string=u'Tipo de Habitación',comodel_name='motgama.tipo',ondelete='set null') #Tipo de Habitación
    tema_id = fields.Many2one(string=u'Tema',comodel_name='motgama.tema',ondelete='set null')
    inmotica = fields.Boolean(string=u'¿La habitacion es controlada con inmotica?',) 
    #estado = fields.Selection(string=u'Estado',selection=[('D', 'Disponible'), ('OO', 'Ocupado Ocasional'), ('OA', 'Ocupado Amanecida'), ('LQ', 'Liquidada'),  ('RC', 'Recaudada'), ('LM', 'Limpieza'), ('R', 'Reservada'), ('FS', 'Fuera de Servicio'), ('FU', 'Fuera de Uso'), ('HB', 'Habilitar')],default='D')
    #ultmovimiento = fields.Many2one(string='Ultimo movimiento',comodel_name='motgama.movimiento',ondelete='set null')
    tiemponormalocasional = fields.Integer(string=u'Tiempo ocasional normal')
    active = fields.Boolean(string=u'Activo?',default=True)
    estado_tree = fields.Char(string=u'Estado -',)
    # Enlaza las listas de precios por habitacion
    listapreciohabitacion_ids = fields.One2many('motgama.listapreciohabitacion', 'habitacion_id', string='Listas de precios')
    
    @api.model
    def create(self,values):
        record = super().create(values)
        recepcion = record.zona_id.recepcion_id
        flujo = {
            'codigo' : record.codigo,
            'estado' : 'D',
            'recepcion' : recepcion.id
        }
        self.env['motgama.flujohabitacion'].create(flujo)
        return record

    @api.multi
    def write(self,values):
        flujo = self.env['motgama.flujohabitacion'].search([('codigo','=',self.codigo)])
        super().write(values)
        flujo.write(values)
        return True

    @api.multi
    def unlink(self):
        for record in self:
            flujo = self.env['motgama.flujohabitacion'].search([('codigo','=',record.codigo)])
            flujo.unlink()
            return super().unlink()
        

class MotgamaListaPrecioTipo(models.Model): #Lista de precios por tipo de habitacion
    _name = 'motgama.listapreciotipo'
    _description = 'Listas de Precios por tipo de habitación'
    nombrelista = fields.Selection([('1', 'L1'),('2', 'L2'),('3', 'L3'),('4', 'L4'),('5', 'L5')], string='Lista')
    tipo_id = fields.Many2one('motgama.tipo','Tipo habitación')
    tarifaocasional = fields.Float(string=u'Precio Ocasional')
    tarifamanecida = fields.Float(string=u'Precio Amanecida')
    tarifahoradicional = fields.Float(string=u'Precio hora adicional')
    active = fields.Boolean(string=u'Activo?',default=True)    
    #tipo_id = fields.Many2one(string=u'Tipo',comodel_name='motgama.habitacion',ondelete='set null',)

class MotgamaListaPrecioHabitacion(models.Model): #Lista de precios por habitacion                                          #P7.0.4R
    _name = 'motgama.listapreciohabitacion'
    _description = 'Listas de Precios para esta habitacion'
    nombrelista = fields.Selection([('1', 'L1'),('2', 'L2'),('3', 'L3'),('4', 'L4'),('5', 'L5')], string='Lista')
    tarifaocasional = fields.Float(string=u'Precio Ocasional')
    tarifamanecida = fields.Float(string=u'Precio Amanecida')
    tarifahoradicional = fields.Float(string=u'Precio hora adicional')
    active = fields.Boolean(string=u'Activo?',default=True)
    habitacion_id = fields.Many2one(string=u'Habitacion',comodel_name='motgama.habitacion',ondelete='set null',)

class MotgamaWizardHabitacion(models.TransientModel):
    _name = 'motgama.wizardhabitacion'
    _description = 'Asignacion de habitacion'
    placa = fields.Char(string=u'Ingrese Placa',)
    tipovehiculo = fields.Selection(string=u'Tipo de vehiculo',selection=[('particular', 'Particular'), ('moto', 'Moto'), ('peaton', 'Peatón'),('taxi','Taxi')])
    asignatipo = fields.Selection(string=u'La Asignacion es Amanecida?',selection=[('OO', 'No'), ('OA', 'Si')])
    codigohabitacion = fields.Char(string=u'Código habitación')

    def _compute_codigohab(self):
        self.ensure_one()
        # Sacar el id que trae por debajo el contexto del Wizard
        habitacion = self.env.context['active_id']

# Se añade el historico de Placas para que tener registro si esta tuvo algun problema o tiene un acceso prioritario
class MotgamaPlaca(models.Model):#10 julio
    _name = 'motgama.placa'
    _description = u'Placas'
    _sql_constraints = [('placa_uniq', 'unique (placa)', "La placa ya Existe, Verifique!")]
    placa = fields.Char(string=u'Placa del Vehiculo') 
    descripcion = fields.Text(string=u'Descripción del Evento',) # Descripción del evento
    # Se agrega nuevos campos al models 11 julio 2019
    tipovehiculo = fields.Selection(string=u'Tipo de vehiculo',selection=[('particular', 'Particular'), ('moto', 'Moto'), ('peaton', 'Peatón'),('taxi','Taxi')])    
    tipovinculo = fields.Text(string=u'Tipo de vinculo',)
    descvinculo = fields.Text(string=u'Descripción del vínculo',)    

class MotgamaTema(models.Model):#ok                                                                                 #P7.0.4R
#   Fields: TEMA: .
    _name = 'motgama.tema'
    _description = u'Tema'
    _rec_name = 'nombre'
    _order = 'nombre ASC'
    _sql_constraints = [('codigo_uniq', 'unique (codigo)', "El Código ya Existe, Verifique!")]
    codigo = fields.Char(string=u'Código') 
    nombre = fields.Char(string=u'Nombre',required=True,)
    descripcion = fields.Text(string=u'Descripción')
    fotografia = fields.Binary(string=u'Foto')
    active = fields.Boolean(string=u'Activo?',default=True)
    habitacion_ids = fields.One2many(string=u'Habitaciones con este tema',comodel_name='motgama.habitacion',inverse_name='tema_id')  #HABITACIONES CON ESTE TEMA

class MotgamaMovimiento(models.Model):#ok
#    Fields: MOVIMIENTO: .Modification date:  Mayo 9 del 2019: 
#        - res.users = Se ingresa codigo para obtener la informacion de usuario logeado y en es cual va a realizar los diferentes movimientos.
#        - asignatipo = Se selecciona que tipo de asignacion tiene la habitacion.
    _name = 'motgama.movimiento'
    _description = u'Movimiento'
    habitacion_id = fields.Many2one(string=u'Habitación',comodel_name='motgama.habitacion',ondelete='set null')
    tipovehiculo = fields.Selection(string=u'Tipo de vehiculo',selection=[('particular', 'Particular'), ('moto', 'Moto'), ('peaton', 'Peatón'),('taxi','Taxi')])
    placa_vehiculo = fields.Char(string=u'Placa del Vehiculo')
    asignatipo = fields.Selection(string=u'Tipo de Asignación',selection=[('OO', 'Ocasional'), ('OA', 'Amanecida')]) # (09/05/2019) 
   # asignafecha = fields.Date(string=u'Asignación de Fecha')
    asignafecha = fields.Datetime(string=u'Fecha de Asignación',readonly=True, required=True,index=True,default=(lambda *a: time.strftime(dt)))
    asigna_uid = fields.Many2one(comodel_name='res.users',string='Usuario que asigna')
   # liquidafecha = fields.Date(string=u'Liquida Fecha')
    liquidafecha= fields.Datetime(string=u'Fecha y hora Liquidacion')
    liquida_uid = fields.Many2one(comodel_name='res.users',string='Usuario que liquida')
   # recaudafecha = fields.Date(string=u'Fecha de recaudo')
    recaudafecha = fields.Datetime(string=u'Fecha y hora de recaudo')
    recauda_uid = fields.Many2one(comodel_name='res.users',string='Usuario que recauda')
    factura = fields.Many2one(string='Factura',comodel_name='account.invoice')
   # aseofecha = fields.Date(string=u'Fecha de aseo')
    aseofecha = fields.Datetime(string=u'Fecha y hora aseo')
    aseo_uid = fields.Many2one(comodel_name='res.users',string='Usuario que cambia al estado aseo')
   # habilitafecha = fields.Date(string=u'Fecha de habilitación')
    habilitafecha = fields.Datetime(string=u'Fecha y hora de habilitación')
    habilita_uid = fields.Many2one(comodel_name='res.users',string='Usuario que habilita la habitación')
   # reasignafecha = fields.Date(string=u'Fecha de reasignación')
    # reasignafecha = fields.Datetime(string=u'Fecha y Hora de reasignación')
    # reasigna_uid = fields.Many2one(comodel_name='res.users',string='Usuario responsable',default=lambda self: self.env.user.id)
    # reasignanueva_id = fields.Char(string=u'Reasignacion Nueva') # Este es un Integer Many2One de donde sale *
    # reasignaanterior_uid = fields.Char(string=u'Reasignacion Anterior') # Este es un Integer Many2One de donde sale *
    flagreasignada = fields.Boolean(string=u'Reasignada')
   # reservafecha = fields.Date(string=u'Fecha de la reserva')
    reservafecha = fields.Datetime(string=u'Fecha y Hora de la reserva')
    reserva_uid = fields.Many2one(comodel_name='res.users',string='Usuario que reserva')
   # desasignafecha = fields.Date(string=u'Fecha de la desasigna')
    desasignafecha = fields.Datetime(string=u'Fecha y Hora de la desasigna')
    desasigna_uid = fields.Many2one(comodel_name='res.users',string='Usuario que desasigna')
    incluyedecora = fields.Boolean(string=u'Incluye decoración')    
    tarifaocasional = fields.Float(string=u'Tarifa ocasional')
    tarifamanecida = fields.Float(string=u'Tarifa amanecida')
    tarifahoradicional = fields.Float(string=u'Tarifa hora adicional')    
    # tarifapersonadicional = fields.Float(string=u'Tarifa persona adicional') # REVISAR YA NO VA PORQUE ES UN PRODUCTO MAS
    tiemponormalocasional = fields.Integer(string=u'Tiempo ocasional normal')
    active = fields.Boolean(string=u'Activo?',default=True)
    anticipo = fields.Float(string=u'Valor anticipo')
    formapagoanticipo = fields.Char(string=u'Forma pago anticipo')
    reciboanticipo = fields.Float(string=u'Nro recibo caja anticipo')
    nroestadocuenta = fields.Char(string=u'Nro estado de cuenta') # Se añade 11 de Julio
    nrofactura = fields.Char(string=u'Nro de factura') # Se añade 11 de Julio
    # Proceso de Fuera de servicio
    fueradeserviciohora = fields.Datetime(string='Fecha fuera de servicio')
    fueradeservicio_uid = fields.Many2one(comodel_name='res.users',string='Usuario que cambia de estado a fuera de servicio')
    # Proceso de Fuera de uso
    fueradeusohora = fields.Datetime(string='Fecha fuera de uso')
    fueradeuso_uid = fields.Many2one(comodel_name='res.users',string='Usuario que cambia de estado a fuera de uso')
    fueradeuso_usuarioorden = fields.Char(string='Persona que dio la orden')
    # Se agrega lista de precios traida del calendario según el día de la semana
    listaprecioproducto = fields.Many2one(string=u'Lista precio Productos',comodel_name='product.pricelist')
    observacion = fields.Char(string='Observación')
    horainicioamanecida = fields.Datetime(string='Hora Inicio Amanecida')
    horafinamanecida = fields.Datetime(string='Hora Fin Amanecida')


class MotgamaHistoricoMovimiento(models.Model):#ok
#    Fields:  PENDIENTE REVISAR
# HISTORICO DE MOVIMIENTO:  Este movimiento tiene la replica exacta de motgama.movimiento y se escoje el año que se quiere trasladar
    _name = 'motgama.hcomov' #Historico Movimiento
    _description = u'MotgamaHistoricoMovimiento' 
    _rec_name = 'anio'
    _order = 'anio ASC'
    anio = fields.Char(string=u'Año')
    active = fields.Boolean(string=u'Activo?',default=True)

class MotgamaReservas(models.Model):#ok
#    Fields: Reserva: se hereda res.partner para ingresar el usuario cuando realiza la reservacion
    _name = 'motgama.reserva'
    _description = u'Reservas'
    cliente_id = fields.Many2one(comodel_name='res.partner', string='Cliente')
    fecha = fields.Datetime(string=u'fecha')
    condecoracion = fields.Boolean(string=u'Con decoración?')
    notadecoracion = fields.Text(string=u'Nota para la decoración')
    habitacion_id = fields.Many2one(string=u'Habitación',comodel_name='motgama.habitacion',ondelete='set null')
    anticipo = fields.Float(string=u'Anticipo $:')
    modificada = fields.Boolean(string=u'Reserva Modificada',default=False)
    modificada_uid = fields.Many2one(comodel_name='res.users',string='Usuario modifica',default=lambda self: self.env.user.id)
    fecha_original = fields.Datetime(string=u'F.Anterior')
    cancelada = fields.Boolean(string=u'Reserva Cancelada',default=False)
    cancelada_uid = fields.Many2one(comodel_name='res.users',string='Usuario cancela',default=lambda self: self.env.user.id)
    fecha_cancela = fields.Datetime(string=u'F.Cancela')
    active = fields.Boolean(string=u'Activo?',default=True)

class MotgamaObjetosOlvidados(models.Model):
#    Fields:Objetos Olvidados: elementos que el cliente olvido en una habitacion.
    _name = 'motgama.objolv' #Objetos Olvidados
    _description = u'MotgamaObjetosOlvidados'
    habitacion_id = fields.Many2one(string=u'Habitacion',comodel_name='motgama.habitacion',ondelete='set null')
    fecha = fields.Datetime(string=u'Fecha')
    descripcion = fields.Text(string=u'Descripción')
    valor = fields.Float(string=u'Valor Estimado')
    encontradopor = fields.Text(string=u'Encontrado por')
    entregado = fields.Boolean(string=u'Entregado?')
    entregadofecha = fields.Datetime(string=u'Fecha de entrega') 
    cliente_id = fields.Many2one(comodel_name='res.partner', string='Cliente')
    entregado_uid = fields.Many2one(comodel_name='res.users',string='Usuario responsable',default=lambda self: self.env.user.id)
    entregadonota = fields.Text(string=u'Nota')
    baja = fields.Boolean(string=u'Artículo dado de baja?')
    active = fields.Boolean(string=u'Activo?', default=True)

class MotgamaPrendas(models.Model):
#    Fields: Prenda: el cliente deja elementos en forma de pago Creado: Mayo 10 del 2019                                        
    _name = 'motgama.prendas'
    _description = u'Registro de prendas'
    habitacion_id = fields.Many2one(string='Habitación',comodel_name='motgama.flujohabitacion') # Habitacion del cliente que dejo la prende como pago                                 #P7.0.4R
    movimiento_id = fields.Integer('Movimiento',)
    factura = fields.Many2one(string='Factura',comodel_name='account.invoice')
    tipovehiculo = fields.Selection(string=u'Tipo de vehiculo',selection=[('particular', 'Particular'), ('moto', 'Moto'), ('peaton', 'Peatón'),('taxi','Taxi')])
    placa = fields.Char(string=u'Placa')
    fecha = fields.Datetime(string=u'Fecha', default=lambda self: fields.Datetime().now())
    cliente_id = fields.Many2one(comodel_name='res.partner', string='Cliente')
    descripcion = fields.Text(string=u'Descripción')
    valorprenda = fields.Float(string=u'Valor de la prenda',) # Actualmente no se utiliza
    valordeuda = fields.Float(string=u'Valor de la deuda',) # Actualmente no se utiliza
    pagado = fields.Boolean(string=u'pagado',)
    pagodofecha = fields.Datetime(string=u'fecha del pago')
    pagadoforma = fields.Char('Medio de pago') # PENDIENTE DE CONECTAR
    pago_uid = fields.Many2one(comodel_name='res.users',string='Usuario responsable',default=lambda self: self.env.user.id)
    active = fields.Boolean(string=u'Activo?',default=True)

class MotgamaBonos(models.Model):
#    Fields: Bonos: el cliente tiene una forma de pago por medio de bonos Creado: Mayo 16 del 2019
    _name = 'motgama.bonos'
    _description = u'MotgamaBonos'
    _sql_constraints = [('codigo_uniq', 'unique (codigo)', "El Código ya Existe, Verifique!")]
    codigo = fields.Char(string=u'Código: ',)
    multiple = fields.Boolean(string=u'Multiple ', ) #Lo pueden utilizar muchas personas
    validodesde = fields.Date(string=u'Valido Desde?',)
    validohasta = fields.Date(string=u'Valido Hasta?',)
    descuentavalor = fields.Float(string=u'Descontar valor $',)
    porcpagoefectivo = fields.Float(string=u'Porc. descto. en efectivo $ ',)
    porcpagotromedio = fields.Float(string=u'Porc. descto. por otro medio $',)
    # El descuento se lo puede aplicar a :
    aplicahospedaje = fields.Boolean(string=u'Aplicar descuento en hospedaje',default=True)
    aplicarestaurante = fields.Boolean(string=u'Aplicar descuento en restaurante',)
    aplicaconsumos = fields.Boolean(string=u'Aplicar descuento en otros productos',)    
    active = fields.Boolean(string=u'Activo?',default=True)

class MotgamaConsumo(models.Model):
#    Fields: Consumos del Bar en cualquiera de las recepciones: Creado: Junio 07 del 2019
    _name = 'motgama.consumo'
    _description = 'Consumos'
    # 19 jun se cambia por habitacion para despues realizar un autoguardado
    recepcion = fields.Many2one(comodel_name='motgama.recepcion',default=lambda self: self.env.user.recepcion_id.id)
    consecutivo =  fields.Float(string=u'Total $')
    llevaComanda = fields.Boolean(string='¿Lleva Comanda?',default=False)
    textoComanda = fields.Text(string='Comanda')
    comanda = fields.Many2one(string='Comanda',comodel_name='motgama.comanda')
    habitacion = fields.Many2one(string=u'habitacion_id',comodel_name='motgama.flujohabitacion',ondelete='set null',required=True)
    movimiento_id = fields.Many2one(string='Movimiento',comodel_name='motgama.movimiento',compute='_compute_movimiento',store=True)
    producto_id = fields.Many2one(string=u'producto_id',comodel_name='product.template',ondelete='set null',required=True)   
    cantidad = fields.Float(string=u'Cantidad',required=True)
    vlrUnitario = fields.Float(string='Vlr Unitario',compute='_compute_vlrunitario',store=True)                                                                                     #P7.0.4R
    vlrSubtotal = fields.Float(string=u'Subtotal $',compute="_compute_vlrsubtotal",store = True)
    lugar_id = fields.Many2one(string='Bodega de Inventario',comodel_name='stock.location',ondelete='set null',store=True)
    estado = fields.Char(string=u'estado')
    active = fields.Boolean(string=u'Activo?',default=True)    
    asigna_uid = fields.Many2one(comodel_name='res.users',string='Usuario responsable',default=lambda self: self.env.user.id)

    @api.onchange('producto_id')
    def onchange_producto(self):
        for record in self:
            if record.producto_id:
                record.llevaComanda = record.producto_id.categ_id.llevaComanda

    @api.depends('habitacion')
    def _compute_movimiento(self):
        for record in self:
            record.movimiento_id = record['habitacion'].ultmovimiento

    @api.onchange('habitacion')
    def onchange_habitacion(self):
        for record in self:
            if record.habitacion:
                lugar = self.env['stock.location'].search(['&',('recepcion','=',record.habitacion.recepcion.id),('permite_consumo','=',True)],limit=1)
                if not lugar:
                    raise Warning('No existe lugar de inventario para la recepción: ' + record.habitacion.recepcion.nombre)
                record.lugar_id = lugar.id

    @api.depends('habitacion','producto_id')
    def _compute_vlrunitario(self):
        for record in self:
            if record.producto_id:
                movimiento = self.env['motgama.movimiento'].search([('id','=',record.movimiento_id.id)], limit=1)
                lista = movimiento.listaprecioproducto
                precioLista = self.env['product.pricelist.item'].search(['&',('pricelist_id','=',lista.id),('product_tmpl_id','=',record.producto_id.id)], limit=1)
                record['vlrUnitario'] = precioLista.fixed_price

    @api.depends('vlrUnitario')
    def _compute_vlrsubtotal(self):
        for record in self:
            record['vlrSubtotal'] = record.vlrUnitario * record.cantidad

class MotgamaComanda(models.Model):
#    Fields: Comandas
    _name = 'motgama.comanda'
    _description = 'Comanda'
    # 19 jun se cambia por habitacion para despues realizar un autoguardado
    nrocomanda = fields.Integer('Nro. Comanda')
    fecha = fields.Datetime ('Fecha')
    habitacion = fields.Many2one(string=u'habitacion_id',comodel_name='motgama.flujohabitacion',ondelete='set null',required=True)
    movimiento_id = fields.Integer(string='Movimiento')
    producto_id = fields.Many2one(string=u'producto_id',comodel_name='product.template',ondelete='set null',required=True)   
    cantidad = fields.Float(string=u'Cantidad',required=True)
    vlrUnitario = fields.Float(string='Vlr Unitario')                                                                                     #P7.0.4R
    descripcion = fields.Text(string=u'descripción')
    active = fields.Boolean(string=u'Activo?',default=True)    

#Añade a la tabla de usuarios el campo de recepción asociada.
class Users(models.Model):
    _inherit = "res.users"
    recepcion_id = fields.Many2one(string=u'Recepción',comodel_name='motgama.recepcion',ondelete='set null')

#REVISAR    
class MotgamaWizardRecepcion(models.TransientModel):
    _name = 'motgama.wizardrecepcion'
    _description = 'Recepción'
    recepcion_id = fields.Many2one(string=u'Con Cual recepcion trabajaras hoy?',comodel_name='motgama.recepcion',ondelete='set null')
    def button_asignar_wizard(self):
        for record in self:
            qryactualizarusers = "UPDATE res_users SET recepcion_id = " + str(record.recepcion_id.id) + " WHERE id = " + str(self.env.uid) + ";"
            self.env.cr.execute(qryactualizarusers)
            return True

class MotgamaPagos(models.Model):
    _name = 'motgama.pago'
    _description = 'Pago'
    movimiento_id = fields.Integer('Nro. Movimiento')
    cliente_id = fields.Many2one(comodel_name='res.partner', string='Cliente',required=True)   
    fecha = fields.Datetime(string=u'Fecha',default=lambda self: fields.Datetime().now())   
    mediopago = fields.Many2one(string='Medio de Pago',comodel_name='motgama.mediopago',required=True)
    banco = fields.Char('Banco') # PENDIENTE PARA TRAER DE TABLA DE BANCOS DE ODOO
    valor =  fields.Float(string=u'Valor a pagar',required=True)
    # Se debe hacer la condicional que si el usuario va a pagar con prenda entonces se debe agregar el contacto que nos aparece desde odoo    
    descripcion = fields.Text(string=u'Descripcion')
    usuario_uid = fields.Integer(string=u'responsable',default=lambda self: self.env.user.id)
    recaudo = fields.Many2one(string='Recaudo',comodel_name='motgama.recaudo',ondelete='restrict')

class MotgamaRecaudo(models.Model):
    _name = 'motgama.recaudo'
    _description = 'Recaudo de hospedaje'
    _rec_name = 'create_date'

    movimiento_id = fields.Integer(string='Nro. Movimiento')
    habitacion = fields.Many2one(string='Habitación',comodel_name='motgama.flujohabitacion')
    cliente = fields.Many2one(string='Cliente',comodel_name='res.partner')
    factura = fields.Many2one(string='Factura',comodel_name='account.invoice')
    total_pagado = fields.Float(string='Total pagado')
    pagos = fields.One2many(string='Pagos',comodel_name='motgama.pago',inverse_name='recaudo')
    prenda = fields.Many2one(string='Prenda asociada',comodel_name='motgama.prendas')
    usuario_uid = fields.Many2one(string='Usuario responsable',comodel_name='res.users', default=lambda self: self.env.user.id)

class MotgamaCierreTurno(models.TransientModel):
    _name = 'motgama.cierreturno'
    _description = 'Cierre Turno'
    usuarioturno_uid = fields.Integer(string=u'responsable',) # OJO ENLAZAR AL USUARIO LOGUEADO EN EL TURNO
    ultmovimiento_id = fields.Integer('Ultimo Movimiento')
    ultctacobro = fields.Integer('Ultima Cta. Cobro')
    ultfactura = fields.Char('Ultima Factura')
    fecha = fields.Date(string=u'Fecha')
    hora = fields.Datetime(string=u'Hora')

class MotgamaReasignacion(models.Model):
    _name = 'motgama.reasignacion'
    _description = 'Reasignacion Habitacion'
    # _rec_name = 'codigo'
    habitacion_id = fields.Char(string=u'Habitación')
    movimiento_id = fields.Many2one(string='Movimiento (Asignación)',comodel_name='motgama.movimiento',ondelete='set null')
    fechareasigna = fields.Datetime(string='Fecha Reasigna')
    habitacion_nueva = fields.Char(string=u'Habitación Nueva')
    descripcion = fields.Char(string=u'Descripción')
    active = fields.Boolean(string=u'Activo?',default=True)

class MotgamaUtilidades(models.TransientModel):
    _name = 'motgama.utilidades'   # sobreescribe en cada habitacion el precio del tipo                    #P7.0.4R
    _description = 'Menú de utilidades'
    nueva_recepcion = fields.Many2one(string="Nueva recepción", comodel_name="motgama.recepcion")

class MotgamaMedioPago(models.Model):
    _name = 'motgama.mediopago'
    _description = 'Medios de Pago'
    _rec_name = 'nombre'

    nombre = fields.Char(string='Nombre',required=True)
    tipo = fields.Selection(string='Tipo de pago',required=True,selection=[('electro','Electrónico'),('efectivo','Efectivo'),('bono','Bono/Descuento'),('prenda','Prenda')])
    lleva_prenda = fields.Boolean(string='¿Lleva Prenda?',compute='_compute_prenda')

    @api.depends('tipo')
    def _compute_prenda(self):
        for record in self:
            record.lleva_prenda = record.tipo == 'prenda'

class MotgamaWizardFueradeservicio(models.TransientModel):
    _name = 'motgama.wizardfueradeservicio'
    _description = 'Habitación fuera de servicio'
    observacion = fields.Char(string='Observaciones')

class MotgamaWizardFueradeuso(models.TransientModel):
    _name = 'motgama.wizardfueradeuso'
    _description = 'Habitación fuera de uso'
    observacion = fields.Char(string='Observaciones')
    usuario_orden = fields.Char(string='Nombre de quien autoriza')

class MotgamaWizardDesasigna(models.TransientModel):
    _name = 'motgama.wizarddesasigna'
    _description = 'Desasigna Habitación'
    observacion = fields.Char(string='Observaciones')

class MotgamaWizardCambiodeplan(models.TransientModel):
    _name = 'motgama.wizardcambiodeplan'
    _description = 'Cambio de Plan'
    observacion = fields.Char(string='Observaciones')

class MotgamaWizardCambiohabitacion(models.TransientModel):
    _name = 'motgama.wizardcambiohabitacion'
    _description = 'Cambio de Habitacion'
    flujoNuevo = fields.Many2one(string=u'habitacion_id',comodel_name='motgama.flujohabitacion',ondelete='set null',required=True)
    observacion = fields.Char(string='Observaciones')

class MotgamaWizardEntregaolvidados(models.TransientModel):
    _name = 'motgama.wizardentregaolvidados'
    _description = 'Entrega Objetos Olvidados'
    cliente_id = fields.Many2one(comodel_name='res.partner', string='Cliente')
    fecha = fields.Datetime(string=u'fecha entrega')
    observacion = fields.Char(string='Observaciones')
    dardebaja = fields.Boolean(string=u'Activo?',default=False)

