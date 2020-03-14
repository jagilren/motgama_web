# -*- coding: utf-8 -*-
import time
import pytz
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

    codigo = fields.Char(string='Código')
    nombre = fields.Char(string='Nombre Sucursal',required=True)
    telefono = fields.Char(string='Teléfono')
    direccion = fields.Text(string='Dirección')
    ciudad = fields.Char(string='Ciudad')
    email = fields.Char(string='Correo Electronico')
    razonsocial_id = fields.Many2one(string='Razón Social',comodel_name='res.company',ondelete='set null')
    nit = fields.Char(string='Nit')# 11 julio 2019
    active = fields.Boolean(string='Activo?', default=True)
    #RECEPCIONES EN ESTA SUCURSAL
    recepcion_ids = fields.One2many(string=u'Recepciones en esta sucursal',comodel_name='motgama.recepcion', inverse_name='sucursal_id')
 

#Inmotica por parte de Jonny
class MotgamaInmotica(models.Model):#ok
    #Fields:Inmotica: Conexion interna entre base de datos.    
    _name = 'motgama.inmotica'
    _description = 'Inmotica'

    habitacion = fields.Char(string='Habitación',required=True)
    parametro = fields.Char(string='Parámetro',required=True)
    evento = fields.Char(string="Evento",required=True)
    fecha = fields.Datetime(string='Fecha',default=lambda self: fields.Datetime().now())
    usuario_id = fields.Many2one(string='Usuario',comodel_name='res.users',default=lambda self: self.env.user.id)
    mensaje = fields.Selection(string='Tipo de mensaje',selection=[('entrada','Entrada'),('salida','Salida'),('evento','Evento')])

    @api.model
    def create(self,values):
        if values['mensaje'] == 'entrada':
            cod = 'STRINMENT'
        elif values['mensaje'] == 'salida':
            cod = 'STRINMSAL'
        elif values['mensaje'] == 'evento':
            cod = 'STRINMEVEN'
        else:
            raise Warning('Error, el parámetro "' + cod + '" está mal definido, contacte al administrador')
        param = self.env['motgama.parametros'].search([('codigo','=',cod)],limit=1)
        if not param:
            raise Warning('No existe el parámetro con código: "' + cod + '", contacte al administrador')
        values['parametro'] = param.valor
        return super().create(values)
    
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
    horainicioamanecida = fields.Char(string='H. inicio amanecida (hh:mm)')
    horafinamanecida = fields.Char(string='H. fin amanecida (hh:mm)')
    horafininicioamanecida = fields.Char(string='H. fin entrada amanecida (hh:mm)')
    tiemponormalocasional = fields.Integer(string=u'Tiempo ocasional normal')
    flagignoretiempo = fields.Boolean(string=u'Ignorar tiempo del calendario y usar el de la habitación',help="Se ignorará el tiempo normal ocasional del calendario y se utilizará el definido en cada habitación",default=False,)
    sucursal_id = fields.Many2one(string=u'Sucursal',comodel_name='motgama.sucursal',ondelete='set null',)
    active = fields.Boolean(string=u'Activo?',default=True)

    @api.model
    def create(self,values):
        try:
            datetime.strptime(str(values['horainicioamanecida']),"%H:%M")
        except ValueError:
            raise ValidationError('El campo "Hora inicio amanecida" está mal definido, por favor usar el formato HH:MM de 24 horas')
        try:
            datetime.strptime(str(values['horafinamanecida']),"%H:%M")
        except ValueError:
            raise ValidationError('El campo "Hora fin amanecida" está mal definido, por favor usar el formato HH:MM de 24 horas')
        try:
            datetime.strptime(str(values['horafininicioamanecida']),'%H:%M')
        except ValueError:
            raise ValidationError('El campo "Hora fin entrada amanecida" está mal definido, por favor usar el formato HH:MM de 24 horas')
        return super().create(values)
    
    @api.multi
    def write(self,values):
        try:
            inicioamanecida = values['horainicioamanecida']
        except KeyError:
            inicioamanecida = False
        try:
            finamanecida = values['horafinamanecida']
        except KeyError:
            finamanecida = False
        if inicioamanecida:
            try:
                datetime.strptime(str(values['horainicioamanecida']),"%H:%M")
            except ValueError:
                raise ValidationError('El campo "Hora Inicio Amanecida" está mal definido, por favor usar el formato HH:MM de 24 horas')
        if finamanecida:
            try:
                datetime.strptime(str(values['horafinamanecida']),"%H:%M")
            except ValueError:
                raise ValidationError('El campo "Hora Fin Amanecida" está mal definido, por favor usar el formato HH:MM de 24 horas')
        return super().write(values)

class MotgamaRecepcion(models.Model):#ok
#    Fields: RECEPCION: Aca estaran las diferentes recepciones por lo general sera RECEPCION A y RECEPCION B.
    _name = 'motgama.recepcion'
    _description = u'Recepción'
    _rec_name = 'nombre'
    _order = 'nombre ASC'
    _sql_constraints = [('codigo_uniq', 'unique (codigo)', "El Código ya Existe, Verifique!")]
    sucursal_id = fields.Many2one(string=u'Sucursal',comodel_name='motgama.sucursal',ondelete='set null',)
    codigo = fields.Char(string=u'Código',) 
    nombre = fields.Char(string=u'Nombre de recepción',required=True)
    active = fields.Boolean(string=u'Activo?',default=True)
    zonas_ids = fields.One2many(string=u'Zonas en esta recepción',comodel_name='motgama.zona',inverse_name='recepcion_id') #LAS ZONAS EN ESTA RECEPCION
    canal_id = fields.Many2one(string='Canal',comodel_name='mail.channel')

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
    estado = fields.Selection(string='Estado de la zona',selection=[('H','Habilitada'),('FU','Fuera de uso')],default='H')
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
    # minibar = fields.Boolean(string=u'Minibar',)
    # turco = fields.Boolean(string=u'Turco',)
    # jacuzzi = fields.Boolean(string=u'Jacuzzi',)
    # camamov = fields.Boolean(string=u'Cama Movil',)
    # smartv = fields.Boolean(string=u'Smart TV',)
    # barrasonido = fields.Boolean(string=u'Barra Sonido',)
    # hometheater = fields.Boolean(string=u'Home Theater')
    # poledance = fields.Boolean(string=u'Pole Dance',)
    # sillatantra = fields.Boolean(string=u'Silla Tantra')
    # columpio = fields.Boolean(string=u'Columpio')
    # aireacond = fields.Boolean(string=u'Aire Acond')
    # garajecarro = fields.Boolean(string=u'Garaje Carro')
    # garajemoto = fields.Boolean(string=u'Garaje Moto')
    # piscina = fields.Boolean(string=u'Piscina')
    # miniteca = fields.Boolean(string=u'Miniteca')
    # sauna = fields.Boolean(string=u'Sauna')
    # balcon = fields.Boolean(string=u'Balcon')
    active = fields.Boolean(string=u'Activo?',default=True)
    # Comodidades del tipo de habitación
    comodidades = fields.Many2many(string='Comodidades',comodel_name='motgama.comodidad')
    # Habitaciones con este tipo 
    habitacion_ids = fields.One2many(string=u'Habitaciones con este tipo',comodel_name='motgama.habitacion',inverse_name='tipo_id')
    # Enlaza las listas de precios por tipo
    listapreciotipo_ids = fields.One2many('motgama.listapreciotipo', 'tipo_id', string='Listas de precios')

class MotgamaComodidad(models.Model):
    _name = 'motgama.comodidad'
    _description = 'Comodidades de la habitación'
    _rec_name = 'nombre'

    nombre = fields.Char(string='Nombre')

class MotgamaFlujoHabitacion(models.Model):#adicionada por Gabriel sep 10
    _name = 'motgama.flujohabitacion'
    _description = 'Flujo Habitación'
    _rec_name = 'codigo'
    _sql_constraints = [('codigo_uniq', 'unique (codigo)', "El código habitación ya Existe, Verifique!")]

    _inherit = 'base'

    codigo = fields.Char(string='Código')
    estado = fields.Selection(string='Estado',selection=[('D', 'Disponible'), ('OO', 'Ocupado Ocasional'), ('OA', 'Ocupado Amanecida'), ('LQ', 'Liquidada'),  ('RC', 'Aseo'), ('R', 'Reservada'), ('FS', 'Fuera de Servicio'), ('FU', 'Fuera de Uso')],default='D')
    ultmovimiento = fields.Many2one(string='Ultimo movimiento',comodel_name='motgama.movimiento',ondelete='set null')
    recepcion = fields.Many2one(string='Recepcion',comodel_name='motgama.recepcion',ondelete='restrict')
    active = fields.Boolean(string='Activo?',default=True)
    tipo = fields.Many2one(string='Tipo de Habitación',comodel_name='motgama.tipo')
    tema = fields.Many2one(string='Tema',comodel_name='motgama.tema')
    # Liquidación
    orden_venta = fields.Many2one(string='Estado de cuenta',comodel_name='sale.order',ondelete='set null')
    # Consumos
    consumos = fields.One2many(string='Consumos',comodel_name='motgama.consumo',inverse_name='habitacion')
    # Comodidades
    comodidades = fields.Many2many(string='Comodidades',comodel_name='motgama.comodidad',ondelete='set null',compute='_compute_comodidades')
    # Objetos prestados
    prestados = fields.One2many(string='Objetos prestados',comodel_name='motgama.objprestados',inverse_name='habitacion_id')
    # Recaudo
    factura = fields.Many2one(string='Factura',comodel_name='account.invoice')
    # Reservas
    reserva_ids = fields.One2many(string='Reservas',comodel_name='motgama.reserva',inverse_name='habitacion_id',readonly=True)
    prox_reserva = fields.Many2one(string='Próxima reserva',comodel_name='motgama.reserva')
    puede_liquidar = fields.Boolean(default=False)
    puede_recaudar = fields.Boolean(default=False)
    notificar = fields.Boolean(default=False)
    lq = fields.Boolean(default=False)
    inmotica = fields.Boolean(default=False)

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

    @api.depends('tipo')
    def _compute_comodidades(self):
        for record in self:
            if record.tipo:
                ids = []
                for comodidad in record.tipo.comodidades:
                    ids.append(comodidad.id)
                if len(ids) > 0:
                    record.comodidades = [(6,0,ids)]

    @api.multi
    def button_inmotica(self):
        self.ensure_one()
        if self.inmotica:
            valoresInmotica = {
                'habitacion': self.codigo,
                'mensaje': 'evento',
                'evento': 'Botón de inmótica presionado'
            }
            mensajeInmotica = self.env['motgama.inmotica'].create(valoresInmotica)
            if not mensajeInmotica:
                raise Warning('Error al registrar inmótica')

class MotgamaHabitacion(models.Model):#ok
    _name = 'motgama.habitacion'
    _description = 'Habitación'
    _rec_name = 'codigo'
    _sql_constraints = [('codigo_uniq', 'unique (codigo)', "El Código ya Existe, Verifique!")]
    codigo = fields.Char(string='Código')
    nombre = fields.Char(string='Nombre') 
    zona_id = fields.Many2one(string='Zona',comodel_name='motgama.zona',ondelete='set null')
    tipo_id = fields.Many2one(string='Tipo de Habitación',comodel_name='motgama.tipo',ondelete='set null') #Tipo de Habitación
    tema_id = fields.Many2one(string='Tema',comodel_name='motgama.tema',ondelete='set null')
    inmotica = fields.Boolean(string='¿La habitación es controlada con inmótica?')
    #estado = fields.Selection(string=u'Estado',selection=[('D', 'Disponible'), ('OO', 'Ocupado Ocasional'), ('OA', 'Ocupado Amanecida'), ('LQ', 'Liquidada'),  ('RC', 'Recaudada'), ('LM', 'Limpieza'), ('R', 'Reservada'), ('FS', 'Fuera de Servicio'), ('FU', 'Fuera de Uso'), ('HB', 'Habilitar')],default='D')
    #ultmovimiento = fields.Many2one(string='Ultimo movimiento',comodel_name='motgama.movimiento',ondelete='set null')
    tiemponormalocasional = fields.Integer(string='Tiempo ocasional normal')
    active = fields.Boolean(string='Activo?',default=True)
    estado_tree = fields.Char(string='Estado')
    # Enlaza las listas de precios por habitacion
    listapreciohabitacion_ids = fields.One2many('motgama.listapreciohabitacion', 'habitacion_id', string='Listas de precios')
    
    @api.model
    def create(self,values):
        record = super().create(values)
        recepcion = record.zona_id.recepcion_id
        flujo = {
            'codigo' : record.codigo,
            'estado' : 'D',
            'recepcion' : recepcion.id,
            'tipo' : record.tipo_id.id,
            'tema' : record.tema_id.id,
            'inmotica' : record.inmotica,
            'active' : record.active
        }
        self.env['motgama.flujohabitacion'].create(flujo)
        return record

    @api.multi
    def write(self,values):
        flujo = self.env['motgama.flujohabitacion'].search([('codigo','=',self.codigo)])
        if 'tipo_id' in values:
            values['tipo'] = values['tipo_id']
        if 'tema_id' in values:
            values['tema'] = values['tema_id']
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
    placa = fields.Char(string='Ingrese Placa',)
    tipovehiculo = fields.Selection(string='Tipo de vehiculo',selection=[('particular', 'Particular'), ('moto', 'Moto'), ('peaton', 'Peatón'),('taxi','Taxi')],default='peaton',required=True)
    asignatipo = fields.Selection(string='La Asignacion es Amanecida?',selection=[('OO', 'No'), ('OA', 'Si')],required=True,default='OO')
    
    valorocasional = fields.Float(string='Valor Hospedaje Ocasional',readonly=True,compute='_compute_valores')
    valoramanecida = fields.Float(string='Valor Hospedaje Amanecida',readonly=True,compute='_compute_valores')
    valoradicional = fields.Float(string='Valor Hora Adicional',readonly=True,compute='_compute_valores')
    horainicioamanecida = fields.Datetime(string='Hora Inicio Amanecida',readonly=True,compute='_compute_valores')
    tiemponormal = fields.Char(string='Tiempo normal ocasional',readonly=True)
    fecha = fields.Datetime(string='Fecha y hora del sistema',default=lambda self: fields.Datetime().now(),readonly=True)

    codigohab = fields.Char(compute='_compute_valores')

    @api.depends('tipovehiculo')
    def _compute_valores(self):
        for record in self:
            flujo_id = self.env.context['active_id']
            flujo = self.env['motgama.flujohabitacion'].search([('id','=',flujo_id)], limit=1)
            Habitacion = flujo['codigo']
            fullHabitacion = self.env['motgama.habitacion'].search([('codigo','=',Habitacion)], limit=1) # Trae todos los datos de la habitacion actual
            fechaActual = datetime.now()
            if not self.env.user.tz:
                tz = pytz.timezone('America/Bogota')
            else:
                tz = pytz.timezone(self.env.user.tz)
            fechaActualTz = pytz.utc.localize(fechaActual).astimezone(tz)
            nroDia = fechaActualTz.weekday()
            calendario = self.env['motgama.calendario'].search([('diasemana','=',nroDia)], limit=1)
            if not calendario:
                raise Warning('Error: No existe calendario para el día actual')
            
            record.codigohab = Habitacion

            horaInicioAmanecida = datetime.strptime(str(calendario.horainicioamanecida),"%H:%M") + timedelta(hours=5)
            fechaInicioAmanecida = datetime(year=fechaActualTz.year,month=fechaActualTz.month,day=fechaActualTz.day,hour=horaInicioAmanecida.hour,minute=horaInicioAmanecida.minute)
            record.horainicioamanecida = fechaInicioAmanecida
            record.tiemponormal = str(calendario.tiemponormalocasional) + ' horas'

            flagInicioDia = self.env['motgama.parametros'].search([('codigo','=','HINICIODIA')], limit=1)
            if not flagInicioDia:
                raise Warning('Error: No se ha definido el parámetro "Hora Inicio Día"')
            flagInicioNoche = self.env['motgama.parametros'].search([('codigo','=','HINICIONOCHE')], limit=1)
            if not flagInicioNoche:
                raise Warning('Error: No se ha definido el parámetro "Hora Inicio Noche"')
            inicioDiaTz = datetime.strptime(str(flagInicioDia['valor']),"%H:%M")
            inicioNocheTz = datetime.strptime(str(flagInicioNoche['valor']),"%H:%M")
            fechaActualTz = pytz.utc.localize(fechaActual).astimezone(tz)
            if (inicioDiaTz.time() < fechaActualTz.time() < inicioNocheTz.time()):
                Lista = calendario['listapreciodia']
            else:
                Lista = calendario['listaprecionoche']
            tarifaHabitacion = self.env['motgama.listapreciohabitacion'].search(['&',('habitacion_id','=',fullHabitacion.id),('nombrelista','=',Lista)], limit=1)
            if tarifaHabitacion:
                valorocasional = tarifaHabitacion.tarifaocasional
                valoramanecida = tarifaHabitacion.tarifamanecida
                valoradicional = tarifaHabitacion.tarifahoradicional
            else:
                tarifaTipoHabitacion = self.env['motgama.listapreciotipo'].search(['&',('tipo_id','=',fullHabitacion.tipo_id.id),('nombrelista','=',Lista)], limit=1)
                if tarifaTipoHabitacion:
                    valorocasional = tarifaTipoHabitacion.tarifaocasional
                    valoramanecida = tarifaTipoHabitacion.tarifamanecida
                    valoradicional = tarifaTipoHabitacion.tarifahoradicional
                else:
                    raise Warning('Error: No hay tarifas definidas ni para la habitación ni para el tipo de habitación')
            
            record.valorocasional = valorocasional
            record.valoramanecida = valoramanecida
            record.valoradicional = valoradicional


# Se añade el historico de Placas para que tener registro si esta tuvo algun problema o tiene un acceso prioritario
class MotgamaPlaca(models.Model):#10 julio
    _name = 'motgama.placa'
    _description = 'Placas'
    _sql_constraints = [('placa_uniq','unique (placa)',"La placa ya Existe, Puede modificar el registro en el menú Procesos -> Placas Registradas")]
    _rec_name = 'placa'
    
    placa = fields.Char(string='Placa del Vehiculo',placeholder='AAA111',required=True) 
    descripcion = fields.Text(string='Descripción del evento') # Descripción del evento
    # Se agrega nuevos campos al models 11 julio 2019
    tipovehiculo = fields.Selection(string='Tipo de vehiculo',selection=[('moto','Moto'),('particular','Particular'),('taxi','Taxi')],required=True)    
    tiporeporte = fields.Selection(string='Tipo de reporte',selection=[('positivo','Positivo'),('negativo','Negativo')],default='positivo',required=True)
    vinculo = fields.Char(string='Vínculo del vehículo')

    @api.model
    def create(self,values):
        values['placa'] = values['placa'].upper()
        record = super().create(values)
        if len(record.placa) not in [5,6] or ' ' in record.placa or '-' in record.placa:
            raise Warning('Formato de placa no válido, escriba la placa sin espacios o guiones, use solo letras y números. Ejemplos: Vehículos particulares y taxis: "ABC123", motos: "ABC12" o "ABC12D"')
        return record
    
    def write(self,values):
        if 'placa' in values:
            values['placa'] = values['placa'].upper()
            if len(values['placa']) not in [5,6] or ' ' in values['placa'] or '-' in values['placa']:
                raise Warning('Formato de placa no válido, escriba la placa sin espacios o guiones, use solo letras y números. Ejemplos: Vehículos particulares y taxis: "ABC123", motos: "ABC12" o "ABC12D"')
        return super().write(values)

class MotgamaTema(models.Model):#ok                                                                                 #P7.0.4R
#   Fields: TEMA: .
    _name = 'motgama.tema'
    _description = 'Tema'
    _rec_name = 'nombre'
    _order = 'nombre ASC'
    _sql_constraints = [('codigo_uniq', 'unique (codigo)', "El Código ya Existe, Verifique!")]
    codigo = fields.Char(string='Código') 
    nombre = fields.Char(string='Nombre',required=True,)
    descripcion = fields.Text(string='Descripción')
    fotografia = fields.Binary(string='Foto')
    active = fields.Boolean(string='Activo?',default=True)
    habitacion_ids = fields.One2many(string='Habitaciones con este tema',comodel_name='motgama.habitacion',inverse_name='tema_id')  #HABITACIONES CON ESTE TEMA

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

class MotgamaHistoricoMovimiento(models.Model):#ok
#    Fields:  PENDIENTE REVISAR
# HISTORICO DE MOVIMIENTO:  Este movimiento tiene la replica exacta de motgama.movimiento y se escoje el año que se quiere trasladar
    _name = 'motgama.hcomov' #Historico Movimiento
    _description = 'MotgamaHistoricoMovimiento' 
    _rec_name = 'anio'
    _order = 'anio ASC'
    anio = fields.Char(string='Año')
    active = fields.Boolean(string='Activo?',default=True)

class MotgamaReservas(models.Model):#ok
#    Fields: Reserva: se hereda res.partner para ingresar el usuario cuando realiza la reservacion
    _name = 'motgama.reserva'
    _description = 'Reservas'
    _rec_name = 'cod'
    cod = fields.Char(string='Código')
    cliente_id = fields.Many2one(comodel_name='res.partner', string='Cliente',domain=[('customer','=',True),('vat','!=','1')],required=True)
    fecha = fields.Datetime(string='Fecha de reserva',required=True)
    condecoracion = fields.Boolean(string='¿Con decoración?')
    notadecoracion = fields.Text(string='Nota para la decoración')
    tipohabitacion_id = fields.Many2one(string='Tipo de Habitación',comodel_name='motgama.tipo',ondelete='restrict',required=True)
    habitacion_id = fields.Many2one(string='Habitación',comodel_name='motgama.flujohabitacion',ondelete='restrict',required=True)
    anticipo = fields.Float(string='Anticipo')
    recaudo_id = fields.Many2one(string="Recaudo",comodel_name="motgama.recaudo",ondelete="restrict")
    pago_ids = fields.Many2many(string="Pagos",comodel_name="account.payment")
    modificada = fields.Boolean(string='Reserva Modificada',default=False)
    modificada_uid = fields.Many2one(comodel_name='res.users',string='Usuario que modifica')
    fecha_original = fields.Datetime(string='Fecha de reserva anterior')
    cancelada = fields.Boolean(string='Reserva Cancelada',default=False)
    cancelada_uid = fields.Many2one(comodel_name='res.users',string='Usuario que cancela')
    fecha_cancela = fields.Datetime(string='Fecha de cancelación')
    active = fields.Boolean(string='Activo?',default=True)
    esNueva = fields.Boolean(default=True)

class MotgamaObjetosOlvidados(models.Model):
#    Fields:Objetos Olvidados: elementos que el cliente olvido en una habitacion.
    _name = 'motgama.objolv' #Objetos Olvidados
    _description = 'MotgamaObjetosOlvidados'
    habitacion_id = fields.Many2one(string='Habitacion',comodel_name='motgama.habitacion',ondelete='set null')
    fecha = fields.Datetime(string='Fecha',default=lambda self: fields.Datetime().now())
    descripcion = fields.Text(string='Descripción')
    valor = fields.Float(string='Valor Estimado')
    encontradopor = fields.Text(string='Encontrado por')
    entregado = fields.Boolean(string='Entregado')
    entregadofecha = fields.Datetime(string='Fecha de entrega') 
    cliente_id = fields.Many2one(comodel_name='res.partner', string='Cliente')
    entregado_uid = fields.Many2one(comodel_name='res.users',string='Usuario que entrega',default=lambda self: self.env.user.id)
    entregadonota = fields.Text(string='Nota')
    baja = fields.Boolean(string='Artículo dado de baja?')
    active = fields.Boolean(string='Activo?', default=True)
    esNuevo = fields.Boolean(default=True)

    @api.model
    def create(self, values):
        record = super().create(values)
        record.esNuevo = False
        return record

class MotgamaObjetosPrestados(models.Model):
#    Fields:Objetos Prestados: elementos que el cliente solicita prestados en su estadia en una habitacion.
    _name = 'motgama.objprestados' #Objetos Prestados
    _description = 'MotgamaObjetosPrestados'
    habitacion_id = fields.Many2one(string='Habitacion',comodel_name='motgama.flujohabitacion',ondelete='set null',required=True)
    movimiento_id = fields.Many2one(string='Movimiento',comodel_name='motgama.movimiento',ondelete='restrict')
    fecha = fields.Datetime(string='Fecha',default=lambda self: fields.Datetime().now())
    objeto = fields.Selection(string='Objeto',selection=[('hielera','Hielera (Con pinza)'),('cobija','Cobija'),('toalla','Toalla'),('utensilios','Utensilios de cocina (Vaso, cuchara, tenedor, cuchillo)'),('almohada','Almohada'),('otro','Otro')])
    descripcion = fields.Text(string='Descripción del objeto')
    prestadopor_uid = fields.Many2one(comodel_name='res.users',string='Usuario que presta',default=lambda self: self.env.user.id)
    estado_devolucion = fields.Selection(string='Estado devolución',selection=[('ok','Devuelto en buen estado'),('mal','Devuelto en mal estado'),('no','No devuelto')])
    devueltofecha = fields.Datetime(string='Fecha de devolución') 
    devuelto_uid = fields.Many2one(comodel_name='res.users',string='Usuario que entrega',default=lambda self: self.env.user.id)
    entregadonota = fields.Text(string='Observaciones')
    active = fields.Boolean(string='Activo?', default=True)
    esNuevo = fields.Boolean(default=True)

    @api.model
    def create(self, values):
        record = super().create(values)
        record.esNuevo = False
        return record
    
    @api.onchange('habitacion_id')
    def _onchange_habitacion(self):
        if self.habitacion_id:
            self.movimiento_id = self.habitacion_id.ultmovimiento

class MotgamaPrendas(models.Model):
#    Fields: Prenda: el cliente deja elementos en forma de pago Creado: Mayo 10 del 2019                                        
    _name = 'motgama.prendas'
    _description = 'Registro de prendas'
    _rec_name = 'nroprenda'

    nroprenda = fields.Char(string='Nro.', readonly=True,required=True,copy=False,default='Nuevo')
    habitacion_id = fields.Many2one(string='Habitación',comodel_name='motgama.flujohabitacion') # Habitacion del cliente que dejo la prende como pago                                 #P7.0.4R
    movimiento_id = fields.Integer('Movimiento')
    factura = fields.Many2one(string='Factura',comodel_name='account.invoice')
    creado_uid = fields.Many2one(string='Usuario que recibe la prenda',comodel_name='res.users',default=lambda self: self.env.user.id)
    tipovehiculo = fields.Selection(string='Tipo de vehiculo',selection=[('particular', 'Particular'), ('moto', 'Moto'), ('peaton', 'Peatón'),('taxi','Taxi')])
    placa = fields.Char(string='Placa')
    fecha = fields.Datetime(string='Fecha', default=lambda self: fields.Datetime().now())
    cliente_id = fields.Many2one(comodel_name='res.partner', string='Cliente')
    descripcion = fields.Text(string='Descripción')
    valorprenda = fields.Float(string='Valor estimado de la prenda')
    valordeuda = fields.Float(string='Valor de la deuda')
    pagado = fields.Boolean(string='Pagado')
    pagadofecha = fields.Datetime(string='Fecha del pago')
    pago_uid = fields.Many2one(comodel_name='res.users',string='Usuario que recauda la prenda')
    recaudo = fields.Many2one(comodel_name='motgama.recaudo',readonly=True,string='Recaudo')
    active = fields.Boolean(string=u'Activo?',default=True)

class MotgamaBonos(models.Model):
#    Fields: Bonos: el cliente tiene una forma de pago por medio de bonos Creado: Mayo 16 del 2019
    _name = 'motgama.bonos'
    _description = 'Bonos'
    _sql_constraints = [('codigo_uniq', 'unique (codigo)', "El Código ya Existe, Verifique!")]
    codigo = fields.Char(string='Código')
    multiple = fields.Boolean(string='Múltiple') #Lo pueden utilizar muchas personas
    validodesde = fields.Date(string='Válido Desde')
    validohasta = fields.Date(string='Válido Hasta')
    descuentavalor = fields.Float(string='Descontar valor')
    porcpagoefectivo = fields.Float(string='Porc. descto. en efectivo')
    porcpagotromedio = fields.Float(string='Porc. descto. por otro medio',)
    # El descuento se lo puede aplicar a :
    aplicahospedaje = fields.Boolean(string='Aplicar descuento en hospedaje',default=True)
    aplicarestaurante = fields.Boolean(string='Aplicar descuento en restaurante')
    aplicaconsumos = fields.Boolean(string='Aplicar descuento en otros productos')    
    active = fields.Boolean(string='Activo',default=True)

class MotgamaConsumo(models.Model):
#    Fields: Consumos del Bar en cualquiera de las recepciones: Creado: Junio 07 del 2019
    _name = 'motgama.consumo' 
    _description = 'Consumos'
    _inherit = 'base'
    # 19 jun se cambia por habitacion para despues realizar un autoguardado
    recepcion = fields.Many2one(comodel_name='motgama.recepcion',default=lambda self: self.env.user.recepcion_id.id)
    consecutivo =  fields.Float(string='Total $')
    llevaComanda = fields.Boolean(string='¿Lleva Comanda?',default=False)
    textoComanda = fields.Text(string='Comanda')
    comanda = fields.Many2one(string='Comanda asociada',comodel_name='motgama.comanda')
    habitacion = fields.Many2one(string='Habitación',comodel_name='motgama.flujohabitacion',ondelete='set null',required=True)
    movimiento_id = fields.Many2one(string='Movimiento',comodel_name='motgama.movimiento',compute='_compute_movimiento',store=True)
    producto_id = fields.Many2one(string='Producto',comodel_name='product.template',ondelete='set null',required=True)
    cantidad = fields.Float(string='Cantidad',required=True)
    valorUnitario = fields.Float(string='Valor Unitario',compute='_compute_valorUnitario')                                                                                   #P7.0.4R
    vlrUnitario = fields.Float(string='Valor Unitario')
    vlrSubtotal = fields.Float(string='Subtotal $',compute="_compute_vlrsubtotal",store = True)
    lugar_id = fields.Many2one(string='Bodega de Inventario',comodel_name='stock.location',ondelete='set null',store=True)
    estado = fields.Char(string='estado')
    active = fields.Boolean(string='Activo?',default=True)    
    asigna_uid = fields.Many2one(comodel_name='res.users',string='Usuario responsable',default=lambda self: self.env.user.id)
    permitecambiarvalor = fields.Boolean(string='Permite cambiar valor',default=False,compute="_compute_valorUnitario",store=True)

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

    @api.depends('vlrUnitario')
    def _compute_vlrsubtotal(self):
        for record in self:
            record['vlrSubtotal'] = record.vlrUnitario * record.cantidad

    @api.depends('producto_id')
    def _compute_valorUnitario(self):
        for record in self:
            if record.producto_id:
                movimiento = self.env['motgama.movimiento'].search([('id','=',record.movimiento_id.id)], limit=1)
                lista = movimiento.listaprecioproducto
                precioLista = self.env['product.pricelist.item'].search(['&',('pricelist_id','=',lista.id),('product_tmpl_id','=',record.producto_id.id)], limit=1)
                if not precioLista:
                    precio = record.producto_id.list_price
                else:
                    precio = precioLista.fixed_price
                if precio == 0.0:
                    record.permitecambiarvalor = True
                else:
                    record.permitecambiarvalor = False
                    record.valorUnitario = precio
    
    @api.onchange('valorUnitario')
    def _onchange_valorUnitario(self):
        for record in self:
            if record.valorUnitario:
                if record.valorUnitario != 0:
                    record.vlrUnitario = record.valorUnitario

class MotgamaComanda(models.Model):
#    Fields: Comandas
    _name = 'motgama.comanda'
    _description = 'Comanda'
    _rec_name = 'nrocomanda'
    _inherit  = 'base'
    # 19 jun se cambia por habitacion para despues realizar un autoguardado
    nrocomanda = fields.Integer(string='Nro. Comanda')
    fecha = fields.Datetime(string='Fecha')
    habitacion = fields.Many2one(string='Habitación',comodel_name='motgama.flujohabitacion',ondelete='set null',required=True)
    movimiento_id = fields.Integer(string='Movimiento')
    producto_id = fields.Many2one(string='Producto',comodel_name='product.template',ondelete='set null',required=True)   
    cantidad = fields.Float(string='Cantidad',required=True)                                                                                   #P7.0.4R
    descripcion = fields.Text(string='Descripción')
    usuario_id = fields.Many2one(string='Usuario',comodel_name='res.users',default=lambda self: self.env.user.id)
    recepcion_id = fields.Many2one(string='Recepción',comodel_name='motgama.recepcion')
    active = fields.Boolean(string='Activo?',default=True)

    @api.model
    def create(self,values):
        record = super(MotgamaComanda, self).create(values)
        self.refresh_views()
        return record

#Añade a la tabla de usuarios el campo de recepción asociada.
class Users(models.Model):
    _inherit = "res.users"
    recepcion_id = fields.Many2one(string=u'Recepción',comodel_name='motgama.recepcion',ondelete='set null')

class MotgamaPagos(models.Model):
    _name = 'motgama.pago'
    _description = 'Pago'
    movimiento_id = fields.Integer('Nro. Movimiento')
    cliente_id = fields.Many2one(comodel_name='res.partner', string='Cliente',required=True)   
    fecha = fields.Datetime(string='Fecha',default=lambda self: fields.Datetime().now())   
    mediopago = fields.Many2one(string='Medio de Pago',comodel_name='motgama.mediopago',required=True)
    valor =  fields.Float(string='Valor a pagar',required=True)
    # Se debe hacer la condicional que si el usuario va a pagar con prenda entonces se debe agregar el contacto que nos aparece desde odoo    
    descripcion = fields.Text(string='Descripcion')
    usuario_uid = fields.Integer(string='responsable',default=lambda self: self.env.user.id)
    recaudo = fields.Many2one(string='Recaudo',comodel_name='motgama.recaudo',ondelete='restrict')
    pago_id = fields.Many2one(string='Pago',comodel_name='account.payment')

class MotgamaRecaudo(models.Model):
    _name = 'motgama.recaudo'
    _description = 'Recaudo de hospedaje'
    _rec_name = 'nrorecaudo'

    nrorecaudo = fields.Char(string='Recaudo nro.',required=True,default='Nuevo')
    movimiento_id = fields.Many2one(string='Movimiento',comodel_name='motgama.movimiento')
    habitacion = fields.Many2one(string='Habitación',comodel_name='motgama.flujohabitacion')
    cliente = fields.Many2one(string='Cliente',comodel_name='res.partner')
    factura = fields.Many2one(string='Factura',comodel_name='account.invoice')
    total_pagado = fields.Float(string='Valor total')
    pagos = fields.One2many(string='Pagos',comodel_name='motgama.pago',inverse_name='recaudo')
    prenda = fields.Many2one(string='Prenda asociada',comodel_name='motgama.prendas')
    valor_pagado = fields.Float(string='Valor pagado',default=0.0)
    usuario_uid = fields.Many2one(string='Usuario que recauda',comodel_name='res.users', default=lambda self: self.env.user.id)
    tipo_recaudo = fields.Selection(string='Tipo de recaudo',selection=[('habitaciones','Recaudo de habitaciones'),('abonos','Recaudo de abonos'),('prenda','Recaudo de prenda'),('anticipos','Recaudo de anticipos'),('otros','Otros recaudos')])

    @api.model
    def create(self,values):
        if values.get('nrorecaudo','Nuevo') == 'Nuevo':
            values['nrorecaudo'] = self.env['ir.sequence'].next_by_code('motgama.recaudo') or 'Nuevo'
        return super().create(values)

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
    _description = 'Reasignaciones de habitaciones'
    # _rec_name = 'codigo'
    habitacion_anterior = fields.Many2one(string='Habitación anterior',comodel_name='motgama.flujohabitacion')
    movimiento_id = fields.Many2one(string='Movimiento',comodel_name='motgama.movimiento',ondelete='set null')
    fechareasigna = fields.Datetime(string='Fecha de reasignación',default=lambda self: fields.Datetime().now())
    habitacion_nueva = fields.Many2one(string='Habitación nueva',comodel_name='motgama.flujohabitacion')
    descripcion = fields.Char(string='Observaciones')
    active = fields.Boolean(string='Activo?',default=True)

class MotgamaUtilidades(models.TransientModel):
    _name = 'motgama.utilidades'   # sobreescribe en cada habitacion el precio del tipo                    #P7.0.4R
    _description = 'Menú de utilidades'
    nueva_recepcion = fields.Many2one(string="Nueva recepción", comodel_name="motgama.recepcion")

class MotgamaMedioPago(models.Model):
    _name = 'motgama.mediopago'
    _description = 'Medios de Pago'
    _rec_name = 'nombre'

    nombre = fields.Char(string='Nombre',required=True)
    tipo = fields.Selection(string='Tipo de pago',required=True,selection=[('electro','Electrónico'),('efectivo','Efectivo'),('bono','Bono/Descuento'),('prenda','Prenda'),('abono','Abono')])
    lleva_prenda = fields.Boolean(string='¿Lleva Prenda?',compute='_compute_prenda')
    diario_id = fields.Many2one(string='Diario de pago',comodel_name='account.journal')
    active = fields.Boolean(string='Activo',default=True)

    @api.depends('tipo')
    def _compute_prenda(self):
        for record in self:
            record.lleva_prenda = record.tipo == 'prenda'

class Company(models.Model):
    _inherit = 'res.company'

    resol_nro = fields.Char(string='Nro. Resolución')
    resol_fecha = fields.Date(string='Fecha de resolución')
    resol_fin = fields.Date(string='Fecha de fin de vigencia')
    resol_prefijo = fields.Char(string='Prefijo')
    resol_inicial = fields.Char(string='Factura inical')
    resol_final = fields.Char(string='Factura final')
    resol_texto = fields.Text(string='Vista previa',compute='_compute_texto',store=True)

    footer_factura = fields.Text(string='Pie de página en facturas')

    @api.depends('resol_nro','resol_fecha','resol_fin','resol_prefijo','resol_inicial','resol_final')
    def _compute_texto(self):
        for record in self:
            texto = 'RES DIAN No. '
            if record.resol_nro:
                texto += str(record.resol_nro)
            texto += ' de '
            if record.resol_fecha:
                texto += str(record.resol_fecha)
            texto += '\nVIGENTE HASTA '
            if record.resol_fin:
                texto += str(record.resol_fin)
            texto += '\nHABILITA DESDE '
            if record.resol_prefijo:
                texto += str(record.resol_prefijo)
            texto += ' '
            if record.resol_inicial:
                texto += str(record.resol_inicial)
            texto += ' HASTA '
            if record.resol_prefijo:
                texto += str(record.resol_prefijo)
            texto += ' '
            if record.resol_final:
                texto += str(record.resol_final)
            record.resol_texto = texto

class MotgamaLog(models.Model):
    _name = 'motgama.log'
    _description = 'Log de aplicación Motgama'

    fecha = fields.Datetime(string='Fecha y hora',default=lambda self: fields.Datetime().now())
    modelo = fields.Char(string='Modelo',required=True)
    tipo_evento = fields.Selection(string="Tipo",selection=[('registro','Registro'),('correo','Correo'),('notificacion','Notificación')],required=True)
    asunto = fields.Char(string="Asunto",required=True)
    descripcion = fields.Text(string="Descripción del evento",required=True)
    notificacion_uids = fields.Many2many(string="Usuarios a notificar",comodel_name='res.users')
    correo = fields.Char(string='Correo enviado a')

    @api.model
    def create(self,values):
        if values['tipo_evento'] == 'correo':
            paramCorreo = self.env['motgama.parametros'].search([('codigo','=','EMAILSALARMAS')],limit=1)
            if not paramCorreo:
                raise Warning('No se ha definido el parámetro "EMAILSALARMAS"')
            values['asunto'] = self.env['motgama.sucursal'].search([],limit=1).nombre + ': ' + values['asunto']
            values['descripcion'] = self.env['motgama.sucursal'].search([],limit=1).nombre + ': ' + values['descripcion']
            values['correo'] = paramCorreo.valor
            valoresCorreo = {
                'subject': values['asunto'],
                'email_from': 'luis.ortiz@sistemasgod.com', # TODO: Cambiar email por el del servidor
                'email_to': values['correo'],
                'body_html': '<h3>' + values['descripcion'] + '</h3>',
                'author_id': False
            }
            correo = self.env['mail.mail'].create(valoresCorreo)
            if correo:
                correo.sudo().send()
        record = super().create(values)
        if record.tipo_evento == 'notificacion':
            for usuario in record.notificacion_uids:
                usuario.sudo().notify_warning(message=record.descripcion,title=record.asunto,sticky=True)
        return record

class MotgamaWizardFueradeservicio(models.TransientModel):
    _name = 'motgama.wizardfueradeservicio'
    _description = 'Habitación fuera de servicio'
    observacion = fields.Text(string='Observaciones')

class MotgamaWizardFueradeuso(models.TransientModel):
    _name = 'motgama.wizardfueradeuso'
    _description = 'Habitación fuera de uso'
    observacion = fields.Text(string='Observaciones')
    usuario_orden = fields.Char(string='Nombre de quien autoriza')

class MotgamaWizardDesasigna(models.TransientModel):
    _name = 'motgama.wizarddesasigna'
    _description = 'Desasigna Habitación'
    observacion = fields.Text(string='Observaciones')

class MotgamaWizardCambiodeplan(models.TransientModel):
    _name = 'motgama.wizardcambiodeplan'
    _description = 'Cambio de Plan'
    observacion = fields.Text(string='Observaciones')

class MotgamaWizardCambiohabitacion(models.TransientModel):
    _name = 'motgama.wizardcambiohabitacion'
    _description = 'Cambio de Habitacion'
    flujoNuevo = fields.Many2one(string='Nueva habitación',comodel_name='motgama.flujohabitacion',required=True,domain='[("estado","=","D")]')
    observacion = fields.Text(string='Observaciones')