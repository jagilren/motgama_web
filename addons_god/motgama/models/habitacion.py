from odoo import models, fields, api
from odoo.exceptions import Warning
from datetime import datetime
import pytz, json

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

class MotgamaFlujoHabitacion(models.Model):#adicionada por Gabriel sep 10
    _name = 'motgama.flujohabitacion'
    _description = 'Flujo Habitación'
    _rec_name = 'codigo'
    _sql_constraints = [('codigo_uniq', 'unique (codigo)', "El código de la habitación ya Existe, Verifique!")]

    _inherit = 'base'

    codigo = fields.Char(string='Código')
    estado = fields.Selection(string='Estado',selection=[('D', 'Disponible'), ('OO', 'Ocupado Ocasional'), ('OA', 'Ocupado Amanecida'), ('LQ', 'Liquidada'),  ('RC', 'Aseo'), ('R', 'Reservada'), ('FS', 'Fuera de Servicio'), ('FU', 'Fuera de Uso')],default='D')
    ultmovimiento = fields.Many2one(string='Ultimo movimiento',comodel_name='motgama.movimiento',ondelete='set null')
    recepcion = fields.Many2one(string='Recepcion',comodel_name='motgama.recepcion',ondelete='restrict')
    active = fields.Boolean(string='Activo?',default=True)
    tipo = fields.Many2one(string='Tipo de Habitación',comodel_name='motgama.tipo',ondelete="set null")
    tema = fields.Many2one(string='Tema',comodel_name='motgama.tema', ondelete="set null")
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
    observacion = fields.Text(string='Observaciones',default='')
    sin_alerta = fields.Boolean(string="Sin Alerta",default=True)
    alerta_msg = fields.Char(string="Mensaje alerta")
    bono_id = fields.Many2one(string="Bono",comodel_name='motgama.bonos')

    @api.model
    def get_view(self):
        if self.env.ref('motgama.motgama_todas_recepciones') in self.env.user.permisos:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'motgama.flujohabitacion',
                'name': 'Habitaciones: Todas las recepciones',
                'view_mode': 'kanban,form',
                'limit': 100
            }
        if not self.env.user.recepcion_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'motgama.utilidades',
                'name': 'Utilidades',
                'view_type': 'form',
                'view_mode': 'form'
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'motgama.flujohabitacion',
                'name': 'Habitaciones ' + self.env.user.recepcion_id.nombre,
                'view_mode': 'kanban,form',
                'limit': 100,
                'domain': [('recepcion','=',self.env.user.recepcion_id.id)]
            }

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
        if not self.env.ref('motgama.motgama_inmotica') in self.env.user.permisos:
            raise Warning('No tiene permitido realizar esta acción')
        if self.inmotica:
            valoresInmotica = {
                'habitacion': self.codigo,
                'mensaje': 'evento',
                'evento': 'Botón de inmótica presionado'
            }
            mensajeInmotica = self.env['motgama.inmotica'].create(valoresInmotica)
            if not mensajeInmotica:
                raise Warning('Error al registrar inmótica')

    # Aseo
    @api.multi
    def button_aseo(self):
        self.ensure_one()

        habitacion = self.env['motgama.habitacion'].sudo().search([('codigo','=',self.codigo)],limit=1)
        if habitacion.zona_id.estado == 'FU':
            raise Warning('Toda la zona se encuentra fuera de uso, debe habilitar la zona completa')
        
        movimiento = self.ultmovimiento

        fechaActual = datetime.now()  # coloca la fecha y hora en que se habilita la habitacion

        if movimiento:      # modifica el estado para poner en aseo y poder habilitar nuevamente la habitacion  #P7.0.4R
            valores = {'aseofecha':fechaActual,
                'aseo_uid':self.env.user.id}
            movimiento.write(valores)
            self.sudo().write({'estado':'RC','notificar':True,'sin_alerta':True,'alerta_msg':''}) # pone en estado disponible
        else:
            raise Warning('No se pudo cambiar el estado para asear la habitación')
    
        self.refresh_views()
        
        return True

    # Bonos
    @api.multi
    def aplicar_bono(self):
        self.ensure_one()
        if not self.env.ref('motgama.motgama_bono') in self.env.user.permisos:
            raise Warning('No tiene permitido agregar bonos, contacte al administrador')
        if self.ultmovimiento.bono_id:
            raise Warning('Ya se redimió un bono para esta habitación')

        return {
            'name': 'Aplicar bono',
            'type': 'ir.actions.act_window',
            'res_model': 'motgama.wizard.bono',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('motgama.wizard_bonos').id,
            'target': 'new'
        }
    @api.multi
    def quita_bono(self):
        self.ensure_one()
        if not self.env.ref('motgama.motgama_quita_bono') in self.env.user.permisos:
            raise Warning('No tiene permitido retirar bonos, contacte al administrador')

        self.ultmovimiento.sudo().write({'bono_id': False})
        self.bono_id.sudo().write({'usos': self.bono_id.usos - 1})
        self.sudo().write({'bono_id': False})

    # Cambio de plan
    @api.multi
    def cambio_plan(self):
        if not self.env.ref('motgama.motgama_cambio_plan') in self.env.user.permisos:
            raise Warning('No tiene permitido cambiar de plan, contacte al administrador')

        return {
            'type': 'ir.actions.act_window',
            'res_model': "motgama.wizardcambiodeplan",
            'name': "Cambio de plan habitacion",
            'view_type': "form",
            'view_mode': "form",
            'target': "new"
        }
    
    # Cambio de habitación
    @api.multi
    def cambio_hab(self):
        if not self.env.ref('motgama.motgama_reasigna_mayor') in self.env.user.permisos:
            if not self.env.ref('motgama.motgama_reasigna_menor') in self.env.user.permisos:
                raise Warning('No tiene permitido cambiar de plan, contacte al administrador')

        return {
            'type': 'ir.actions.act_window',
            'res_model': "motgama.wizardcambiohabitacion",
            'name': "Cambio de plan habitacion",
            'view_type': "form",
            'view_mode': "form",
            'target': "new"
        }

    # Desasignación
    @api.multi
    def desasigna(self):
        if not self.env.ref('motgama.motgama_desasigna') in self.env.user.permisos:
            raise Warning('No tiene permitido desasignar habitaciones, contacte al administrador')

        return {
            'type': 'ir.actions.act_window',
            'res_model': "motgama.wizarddesasigna",
            'name': "Desasigna habitacion",
            'view_type': "form",
            'view_mode': "form",
            'target': "new"
        }

    # Descuento
    @api.multi
    def agregar_descuento(self):
        self.ensure_one()

        desc = self.env['motgama.descuento'].search([('movimiento_id','=',self.ultmovimiento.id)],limit=1)
        if desc:
            tiene_permiso = self.env.ref('motgama.motgama_edita_descuento') in self.env.user.permisos
            if not tiene_permiso:
                tiene_permiso = self.env.ref('motgama.motgama_elimina_descuento') in self.env.user.permisos
                if not tiene_permiso:
                    msg = 'No tiene permitido editar o eliminar descuentos por mal servicio'
        else:
            tiene_permiso = self.env.ref('motgama.motgama_descuento_servicio') in self.env.user.permisos
            if not tiene_permiso:
                msg = 'No tiene permitido agregar descuentos por mal servicio'

        if not tiene_permiso:
            raise Warning(msg)

        return {
            'type': 'ir.actions.act_window', 
            'res_model': 'motgama.wizard.descuento',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'name': 'Agregar descuento'
        }

    # Fuera de servicio
    @api.multi
    def fuera_servicio(self):
        if not self.env.ref('motgama.motgama_fuera_servicio') in self.env.user.permisos:
            raise Warning('No tiene permisos para marcar esta habitación como Fuera de Servicio')
        
        return {
            'name': 'Fuera de servicio',
            'type': 'ir.actions.act_window',           
            'res_model': "motgama.wizardfueradeservicio",
            'view_type': "form",
            'view_mode': "form",
            'multi': "True",
            'target': "new"
        }

    # Fuera de uso
    @api.multi
    def fuera_uso(self):
        if not self.env.ref('motgama.motgama_fuera_uso') in self.env.user.permisos:
            raise Warning('No tiene permisos para marcar esta habitación como Fuera de Uso')
        
        return {
            'name': 'Fuera de uso',
            'type': 'ir.actions.act_window',           
            'res_model': "motgama.wizardfueradeuso",
            'view_type': "form",
            'view_mode': "form",
            'multi': "True",
            'target': "new"
        }

    # Habilita
    @api.multi
    def button_habilita(self):
        self.ensure_one()
        if not self.env.ref('motgama.motgama_habilita_habitacion') in self.env.user.permisos:
            raise Warning('No tiene permitido habilitar habitaciones, contacte al administrador')
        movimiento = self.ultmovimiento

        fechaActual = datetime.now()  # coloca la fecha y hora en que se habilita la habitacion
        
        if movimiento:      # modifica el estado para poner en aseo y poder habilitar nuevamente la habitacion      #P7.0.4R
            valores = {
                'habilitafecha':fechaActual,
                'habilita_uid':self.env.user.id,
                'active':False
            }
            movimiento.write(valores)
        self.write({'estado':'D','notificar':False,'bono_id':False,'orden_venta':False,'sin_alerta':True,'alerta_msg':''}) # pone en estado disponible

        self.refresh_views()
        
        return True

    # Liquidar
    @api.multi
    def button_liquidar(self):
        self.ensure_one()
        if not self.env.ref('motgama.motgama_liquida_habitacion') in self.env.user.permisos:
            raise Warning('No tiene permitido liquidar habitaciones, contacte al administrador')
        movimiento = self.ultmovimiento
        fechaActual = fields.Datetime().now()

        if not self.env.user.tz:
            tz = pytz.timezone('America/Bogota')
        else:
            tz = pytz.timezone(self.env.user.tz)

        if not self.puede_liquidar:
            prestados = self.env['motgama.objprestados'].search([('habitacion_id','=',self.id)])
            if prestados:
                return {
                    'name': 'Hay objetos prestados',
                    'type': 'ir.actions.act_window',
                    'res_model': 'motgama.confirm.prestados',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'view_id': self.env.ref('motgama.form_confirm_prestados').id,
                    'target': 'new'
                }
            else:
                self.write({'puede_liquidar': True})
        
        param_bonos = self.env['motgama.parametros'].search([('codigo','=','CODBONOS')],limit=1)
        param_bono = self.env['motgama.parametros'].search([('codigo','=','CODBONOPROM')],limit=1)
        if movimiento.bono_id: # TODO: Cambiar
            if not param_bonos and not param_bono:
                raise Warning('Error: No se han definido los parámetros para liquidar bonos')
        
        # Se calculan las horas adicionales si es amanecida
        if self.estado == 'OA':
            if fechaActual < movimiento.horainicioamanecida:
                raise Warning('Esta asignación no ha superado la "Hora Inicio Amanecida" definida en el Calendario, debe cambiar el plan de asignación a "Ocupada Ocasional" para liquidar esta habitación en este momento')
            elif movimiento.asignafecha < movimiento.horainicioamanecida:
                delta = movimiento.horainicioamanecida - movimiento.asignafecha
                segundos = delta.total_seconds()
                horas = segundos // 3600
                minutos = (segundos // 60) % 60
                tiempoGraciaStr = self.env['motgama.parametros'].search([('codigo','=','TIEMPOGRACIA')])
                if not tiempoGraciaStr:
                    raise Warning('No existe el parámetro "TIEMPOGRACIA"')
                try:
                    tiempoGracia = int(tiempoGraciaStr.valor)
                except ValueError:
                    raise Warning('El parámetro "TIEMPOGRACIA" está mal definido, contacte al administrador')
                seCobraFraccionStr = self.env['motgama.parametros'].search([('codigo','=','COBRAFRACHORA')])
                if not seCobraFraccionStr:
                    raise Warning('No existe el parámetro "COBRAFRACHORA"')
                if seCobraFraccionStr.valor == 'S':
                    seCobraFraccion = True
                elif seCobraFraccionStr.valor == 'N':
                    seCobraFraccion = False
                else:
                    raise Warning('El parámetro "COBRAFRACHORA" está mal definido, contacte al administrador')
                if minutos > tiempoGracia:
                    if seCobraFraccion:
                        horas = float(horas) + float(minutos) / 60.0
                    else:
                        horas += 1
                horasAntes = horas
            else:
                horasAntes = 0
            
            if fechaActual > movimiento.horafinamanecida:
                delta = fechaActual - movimiento.horafinamanecida
                segundos = delta.total_seconds()
                horas = segundos // 3600
                minutos = (segundos // 60) % 60
                tiempoGraciaStr = self.env['motgama.parametros'].search([('codigo','=','TIEMPOGRACIA')])
                if not tiempoGraciaStr:
                    raise Warning('No existe el parámetro "TIEMPOGRACIA"')
                try:
                    tiempoGracia = int(tiempoGraciaStr.valor)
                except ValueError:
                    raise Warning('El parámetro "TIEMPOGRACIA" está mal definido, contacte al administrador')
                seCobraFraccionStr = self.env['motgama.parametros'].search([('codigo','=','COBRAFRACHORA')])
                if not seCobraFraccionStr:
                    raise Warning('No existe el parámetro "COBRAFRACHORA"')
                if seCobraFraccionStr.valor == 'S':
                    seCobraFraccion = True
                elif seCobraFraccionStr.valor == 'N':
                    seCobraFraccion = False
                else:
                    raise Warning('El parámetro "COBRAFRACHORA" está mal definido, contacte al administrador')
                if minutos > tiempoGracia:
                    if seCobraFraccion:
                        horas = float(horas) + float(minutos) / 60.0
                    else:
                        horas += 1
                horasDespues = horas
            else:
                horasDespues = 0
            
            horasAdicionales = horasAntes + horasDespues

            ordenVenta = self.env['sale.order'].sudo().search([('movimiento','=',movimiento.id),('state','=','sale')],limit=1)
            if not ordenVenta:
                cliente = self.env['res.partner'].sudo().search([('vat','=','1')], limit=1)
                if not cliente:
                    raise Warning('No se ha agregado el cliente genérico (NIT: 1), contacte al administrador')
                valores = {
                    'partner_id' : cliente.id,
                    'movimiento' : movimiento.id
                }
                ordenVenta = self.env['sale.order'].sudo().create(valores)
                if not ordenVenta:
                    raise Warning('Error al registrar el consumo: No se pudo crear orden de venta')
                ordenVenta.action_confirm()

            codAmanecida = self.env['motgama.parametros'].search([('codigo','=','CODHOSAMANE')])
            if not codAmanecida:
                raise Warning('No existe el parámetro "CODHOSAMANE"')
            producto = self.env['product.template'].search([('default_code','=',codAmanecida.valor)])
            if not producto:
                raise Warning('No existe producto con Referencia interna: ' + codAmanecida.valor + ' para Hospedaje Amanecida')
            valoresLineaAmanecida = {
                'customer_lead' : 0,
                'name' : producto.name,
                'order_id' : ordenVenta.id,
                'price_unit' : movimiento.tarifamanecida,
                'product_uom_qty' : 1,
                'product_id' : producto.product_variant_id.id,
                'es_hospedaje' : True
            }
            nuevaLinea = self.env['sale.order.line'].sudo().create(valoresLineaAmanecida)
            if not nuevaLinea:
                raise Warning('Error al liquidar: No se pudo agregar el hospedaje de amanecida a la orden de venta')

            if movimiento.bono_id and movimiento.bono_id.aplicahospedaje:
                desc_hosp = movimiento.tarifamanecida * movimiento.bono_id.porcpagoefectivo / 100
                if param_bonos:
                    obj = json.loads(param_bonos.valor_text) if param_bonos.valor_text else False
                    if obj and producto.categ_id.name in obj:
                        producto = self.env['product.template'].search([('default_code','=',obj[producto.categ_id.name])],limit=1)
                    elif param_bono:
                        producto = self.env['product.template'].search([('default_code','=',param_bono.valor)],limit=1)
                else:
                    producto = self.env['product.template'].search([('default_code','=',param_bono.valor)],limit=1)
                valores_bono = {
                    'customer_lead' : 0,
                    'name' : producto.name + ': ' + nuevaLinea.name,
                    'order_id': ordenVenta.id,
                    'price_unit' : 0 - desc_hosp,
                    'product_uom_qty' : 1,
                    'product_id' : producto.product_variant_id.id,
                    'es_hospedaje' : True,
                    'base_line': nuevaLinea.id
                }
                nuevaLinea = self.env['sale.order.line'].sudo().create(valores_bono)
                if not nuevaLinea:
                    raise Warning('Error al liquidar: No se pudo agregar el descuento a la orden de venta')

        elif self.estado == 'OO':
            tiempoOcasionalStr = movimiento.tiemponormalocasional
            try:
                tiempoOcasional = int(tiempoOcasionalStr)
            except ValueError:
                raise Warning('El parámetro de tiempo normal ocasional en el calendario está mal definido, contacte al administrador')
            delta = fechaActual - movimiento.asignafecha
            segundos = delta.total_seconds()
            segundosOcasional = tiempoOcasional * 3600
            if segundos > segundosOcasional:
                segundos -= segundosOcasional
                horas = segundos // 3600
                minutos = (segundos // 60) % 60
                tiempoGraciaStr = self.env['motgama.parametros'].search([('codigo','=','TIEMPOGRACIA')])
                if not tiempoGraciaStr:
                    raise Warning('No existe el parámetro "TIEMPOGRACIA"')
                try:
                    tiempoGracia = int(tiempoGraciaStr.valor)
                except ValueError:
                    raise Warning('El parámetro "TIEMPOGRACIA" está mal definido, contacte al administrador')
                seCobraFraccionStr = self.env['motgama.parametros'].search([('codigo','=','COBRAFRACHORA')])
                if not seCobraFraccionStr:
                    raise Warning('No existe el parámetro "COBRAFRACHORA"')
                if seCobraFraccionStr.valor == 'S':
                    seCobraFraccion = True
                elif seCobraFraccionStr.valor == 'N':
                    seCobraFraccion = False
                else:
                    raise Warning('El parámetro "COBRAFRACHORA" está mal definido, contacte al administrador')
                if minutos > tiempoGracia:
                    if seCobraFraccion:
                        horas = float(horas) + float(minutos) / 60.0
                    else:
                        horas += 1
                horasAdicionales = horas
            else:
                horasAdicionales = 0
            
            ordenVenta = self.env['sale.order'].sudo().search([('movimiento','=',movimiento.id),('state','=','sale')],limit=1)
            if not ordenVenta:
                cliente = self.env['res.partner'].sudo().search([('vat','=','1')], limit=1)
                if not cliente:
                    raise Warning('No se ha agregado el cliente genérico (NIT: 1), contacte al administrador')
                valores = {
                    'partner_id' : cliente.id,
                    'movimiento' : movimiento.id
                }
                ordenVenta = self.env['sale.order'].sudo().create(valores)
                if not ordenVenta:
                    raise Warning('Error al registrar el consumo: No se pudo crear orden de venta')
                ordenVenta.action_confirm()
            ordenVenta.write({'es_hospedaje':True})

            codOcasional = self.env['motgama.parametros'].search([('codigo','=','CODHOSOCASIO')])
            if not codOcasional:
                raise Warning('No existe el parámetro "CODHOSOCASIO"')
            producto = self.env['product.template'].sudo().search([('default_code','=',codOcasional.valor)])
            if not producto:
                raise Warning('No existe producto con Referencia interna: ' + codOcasional.valor + ' para Hospedaje Ocasional')
            valoresLineaOcasional = {
                'customer_lead' : 0,
                'name' : producto.name,
                'order_id' : ordenVenta.id,
                'price_unit' : movimiento.tarifaocasional,
                'product_uom_qty' : 1,
                'product_id' : producto.product_variant_id.id,
                'es_hospedaje' : True
            }
            lineaOcasional = self.env['sale.order.line'].sudo().create(valoresLineaOcasional)
            if not lineaOcasional:
                raise Warning('Error al liquidar: No se pudo agregar el hospedaje ocasional a la orden de venta')
            
            if movimiento.bono_id and movimiento.bono_id.aplicahospedaje:
                desc_hosp = movimiento.tarifaocasional * movimiento.bono_id.porcpagoefectivo / 100
                if param_bonos:
                    obj = json.loads(param_bonos.valor_text) if param_bonos.valor_text else False
                    if obj and producto.categ_id.name in obj:
                        producto = self.env['product.template'].search([('default_code','=',obj[producto.categ_id.name])],limit=1)
                    elif param_bono:
                        producto = self.env['product.template'].search([('default_code','=',param_bono.valor)],limit=1)
                else:
                    producto = self.env['product.template'].search([('default_code','=',param_bono.valor)],limit=1)
                valores_bono = {
                    'customer_lead' : 0,
                    'name' : producto.name + ': ' + lineaOcasional.name,
                    'order_id': ordenVenta.id,
                    'price_unit' : 0 - desc_hosp,
                    'product_uom_qty' : 1,
                    'product_id' : producto.product_variant_id.id,
                    'es_hospedaje' : True,
                    'base_line': lineaOcasional.id
                }
                nuevaLinea = self.env['sale.order.line'].sudo().create(valores_bono)
                if not nuevaLinea:
                    raise Warning('Error al liquidar: No se pudo agregar el descuento a la orden de venta')
            else:
                desc_hosp = 0.0

            # Descuento poco tiempo
            horasDelta = segundos / 3600
            paramTiempoDesc = self.env['motgama.parametros'].search([('codigo','=','TIEMPODESCHOS')],limit=1)
            if not paramTiempoDesc:
                raise Warning('No se ha definido el parámetro "TIEMPODESCHOS"')
            try:
                tiempoDesc = float(paramTiempoDesc.valor)
            except ValueError:
                raise Warning('El parámetro "TIEMPODESCHOS" está mal definido')
            if horasDelta < tiempoDesc:
                paramCodDesc = self.env['motgama.parametros'].search([('codigo','=','CODDESCOCUP')],limit=1)
                if not paramCodDesc:
                    raise Warning('No se ha definido el parámetro "CODDESCOCUP"')
                prod_desc_ocup = self.env['product.template'].sudo().search([('default_code','=',paramCodDesc.valor)],limit=1)
                if not prod_desc_ocup:
                    raise Warning('No existe el producto con referencia interna "' + paramCodDesc.codigo + '"')
                paramDesc = self.env['motgama.parametros'].search([('codigo','=','%DESCPOCOTIEMPO')],limit=1)
                if not paramDesc:
                    desc_tiempo = 0.0
                try:
                    if paramDesc:
                        desc_tiempo = float(paramDesc.valor)
                except ValueError:
                    raise Warning('El parámetro "' + paramDesc.codigo + '" está mal definido')
                dcto = -1 * (movimiento.tarifaocasional - desc_hosp) * desc_tiempo / 100
                if abs(dcto) >= 0.01:
                    valoresLineaDesc = {
                        'customer_lead' : 0,
                        'name' : prod_desc_ocup.name,
                        'order_id' : ordenVenta.id,
                        'price_unit' : dcto,
                        'product_uom_qty' : 1,
                        'product_id' : prod_desc_ocup.product_variant_id.id,
                        'es_hospedaje' : True,
                        'base_line': lineaOcasional.id
                    }
                    nuevaLinea = self.env['sale.order.line'].sudo().create(valoresLineaDesc)
                    if not nuevaLinea:
                        raise Warning('Error al liquidar: No se pudo agregar el descuento por poco tiempo')

        else:
            raise Warning('Error del sistema, la habitación no está ocupada')

        if horasAdicionales != 0:
            codAdicionales = self.env['motgama.parametros'].search([('codigo','=','CODHOSADCNAL')])
            if not codAdicionales:
                raise Warning('No existe el parámetro "CODHOSADCNAL"')
            producto = self.env['product.template'].sudo().search([('default_code','=',codAdicionales.valor)])
            if not producto:
                raise Warning('No existe producto con Referencia interna: ' + codAdicionales.valor + ' para Hospedaje Adicional')

            valoresLineaAdicionales = {
                'customer_lead' : 0,
                'name' : producto.name,
                'order_id' : ordenVenta.id,
                'price_unit' : round(movimiento.tarifahoradicional),
                'product_uom_qty' : horasAdicionales,
                'product_id' : producto.product_variant_id.id,
                'es_hospedaje' : True
            }
            nuevaLinea = self.env['sale.order.line'].sudo().create(valoresLineaAdicionales)
            if not nuevaLinea:
                raise Warning('Error al liquidar: No se pudo agregar el hospedaje de horas adicionales a la orden de venta')
            
            if movimiento.bono_id and movimiento.bono_id.aplica_adicional:
                desc_adic = (round(movimiento.tarifahoradicional) * horasAdicionales) * movimiento.bono_id.porcpagoefectivo / 100
                if param_bonos:
                    obj = json.loads(param_bonos.valor_text) if param_bonos.valor_text else False
                    if obj and producto.categ_id.name in obj:
                        producto = self.env['product.template'].search([('default_code','=',obj[producto.categ_id.name])],limit=1)
                    elif param_bono:
                        producto = self.env['product.template'].search([('default_code','=',param_bono.valor)],limit=1)
                else:
                    producto = self.env['product.template'].search([('default_code','=',param_bono.valor)],limit=1)
                valores_bono = {
                    'customer_lead' : 0,
                    'name' : producto.name + ': ' + nuevaLinea.name,
                    'order_id': ordenVenta.id,
                    'price_unit' : 0 - desc_adic,
                    'product_uom_qty' : 1,
                    'product_id' : producto.product_variant_id.id,
                    'es_hospedaje' : True,
                    'base_line': nuevaLinea.id
                }
                nuevaLinea = self.env['sale.order.line'].sudo().create(valores_bono)
                if not nuevaLinea:
                    raise Warning('Error al liquidar: No se pudo agregar el descuento a la orden de venta')
        
        if movimiento.bono_id and (movimiento.bono_id.aplicarestaurante or movimiento.bono_id.aplicaconsumos):
            for consumo in self.consumos:
                if (movimiento.bono_id.aplicarestaurante and consumo.llevaComanda) or (movimiento.bono_id.aplicaconsumos and not consumo.llevaComanda):
                    desc_cons = (consumo.vlrUnitario * consumo.cantidad) * movimiento.bono_id.porcpagoefectivo / 100
                    producto = consumo.producto_id
                    if param_bonos:
                        obj = json.loads(param_bonos.valor_text) if param_bonos.valor_text else False
                        if obj and producto.categ_id.name in obj:
                            producto = self.env['product.template'].search([('default_code','=',obj[producto.categ_id.name])],limit=1)
                        elif param_bono:
                            producto = self.env['product.template'].search([('default_code','=',param_bono.valor)],limit=1)
                    else:
                        producto = self.env['product.template'].search([('default_code','=',param_bono.valor)],limit=1)
                    valores_bono = {
                        'customer_lead' : 0,
                        'name' : producto.name + ': ' + consumo.line_id.name,
                        'order_id': ordenVenta.id,
                        'price_unit' : 0 - desc_cons,
                        'product_uom_qty' : 1,
                        'product_id' : producto.product_variant_id.id,
                        'es_hospedaje' : True,
                        'base_line': consumo.line_id.id
                    }
                    nuevaLinea = self.env['sale.order.line'].sudo().create(valores_bono)
                    if not nuevaLinea:
                        raise Warning('Error al liquidar: No se pudo agregar el descuento a la orden de venta')

        self.write({'estado':'LQ','orden_venta':ordenVenta.id,'notificar':True,'sin_alerta':True,'alerta_msg':''})
        movimiento.write({'liquidafecha':fechaActual,'liquida_uid':self.env.user.id,'ordenVenta':ordenVenta.id})

        desc = self.env['motgama.descuento'].search([('movimiento_id','=',movimiento.id)],limit=1)
        if desc:
            desc.aplica_descuento()

        ordenVenta.write({'liquidafecha':fechaActual})

        self.puede_liquidar = False

        return True

    # Cuenta de cobro
    @api.multi
    def button_cuentacobro(self):
        self.ensure_one()
        return self.env.ref('motgama.reporte_estadocuenta_80').report_action(docids=[self.orden_venta.id])

    # Observaciones
    @api.multi
    def edita_observacion(self):
        return {
            'name': 'Editar observaciones',
            'type': 'ir.actions.act_window',
            'res_model': "motgama.wizard.observacion",
            'view_type': "form",
            'view_mode': "form",
            'target': "new"
        }

    # Rehabilita
    @api.multi
    def button_continuar(self):
        self.ensure_one()
        movimiento = self.ultmovimiento

        ordenVieja = self.env['sale.order'].sudo().search([('movimiento','=',movimiento.id),('state','=','sale')],limit=1)
        if not ordenVieja:
            raise Warning('La habitación no fue correctamente liquidada')

        valores = {
            'partner_id' : ordenVieja.partner_id.id,
            'movimiento' : movimiento.id
        }
        ordenNueva = self.env['sale.order'].sudo().create(valores)
        if not ordenNueva:
            raise Warning('Error al crear nueva orden de venta')
        ordenNueva.action_confirm()

        lines = ordenVieja.order_line
        for line in lines:
            if not line.es_hospedaje:
                line.write({'order_id': ordenNueva.id})
        pickings = ordenVieja.picking_ids
        for picking in pickings:
            picking.write({'sale_id': ordenNueva.id})
        ordenVieja.action_cancel()
        if not ordenVieja.state == 'cancel':
            raise Warning('No se pudo cancelar la orden de venta')

        lines = ordenNueva.order_line
        for line in lines:
            valores = {
                'customer_lead' : line.customer_lead,
                'name' : line.name,
                'order_id' : ordenVieja.id,
                'price_unit' : line.price_unit,
                'product_uom_qty' : line.product_uom_qty,
                'product_id' : line.product_id.id
            }
            self.env['sale.order.line'].sudo().create(valores)

        estado = movimiento.asignatipo
        self.write({'estado': estado,'notificar':True,'sin_alerta':True,'alerta_msg':''})

        self.refresh_views()
        
        return True

    # Asigna reserva
    @api.multi
    def button_asigna_reserva(self):
        return {
            'name': 'Asignar reserva',
            'type':'ir.actions.act_window',
            'res_model':"motgama.wizardhabitacion",
            'name':"Flujo Habitacion",
            'src_model':"motgama.flujohabitacion",
            'view_type':"form",
            'view_mode':"form",
            'multi':"True",
            'target':"new"
        }

    # Abonos
    @api.multi
    def abonos(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window', 
            'res_model': 'motgama.abonos',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'name': 'Abonos de la habitación ' + self.codigo
        }
    @api.multi
    def abonar(self):
        self.ensure_one()
        if not self.env.ref('motgama.motgama_ingreso_anticipo') in self.env.user.permisos:
            raise Warning('No tiene permitido ingresar abonos, contacte al administrador')
        return {
            'name': 'Abonar',
            'type': 'ir.actions.act_window', 
            'res_model': 'motgama.wizard.abonos',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new'
        }
    @api.multi
    def revertir_abono(self):
        self.ensure_one()
        return {
            'name': 'Revertir abonos',
            'type': 'ir.actions.act_window', 
            'res_model': 'motgama.wizard.revertirabonos',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new'
        }
    @api.multi
    def devolver_abono(self):
        self.ensure_one()

    # Consumo
    @api.multi
    def button_consumos(self):
        self.ensure_one()

        return {
            'name': 'Agregar consumos a la habitación ' + self.codigo,
            'type': 'ir.actions.act_window',
            'res_model': 'motgama.wizard.consumos',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('motgama.form_wizard_consumo').id,
            'target': 'new'
        }

    # Precuenta
    @api.multi
    def button_precuenta(self):
        self.ensure_one()
        if not self.env.ref('motgama.motgama_precuenta') in self.env.user.permisos:
            raise Warning('No tiene permitido ver la precuenta')
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'motgama.wizardprecuenta',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('motgama.form_wizard_precuenta').id,
            'target': 'new',
            'name': 'Precuenta de la habitación ' + self.codigo
        }

    # Recaudo
    @api.multi
    def button_recaudar(self):
        self.ensure_one()
        if not self.env.ref('motgama.motgama_recauda_habitacion') in self.env.user.permisos:
            raise Warning('No tiene permitido recaudar habitaciones, contacte al administrador')

        if not self.puede_recaudar:
            prestados = self.env['motgama.objprestados'].search([('habitacion_id','=',self.id)])
            if prestados:
                return {
                    'name': 'Hay objetos prestados',
                    'type': 'ir.actions.act_window',
                    'res_model': 'motgama.confirm.prestados',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'view_id': self.env.ref('motgama.form_confirm_prestados').id,
                    'target': 'new'
                }
            else:
                self.write({'puede_recaudar': True})
        self.write({'puede_recaudar': False})
        return {
            'name': 'Recaudar habitación',
            'type': 'ir.actions.act_window',
            'res_model': 'motgama.wizardrecaudo',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('motgama.motgama_wizard_recaudo').id,
            'target': 'new',
            'context': {'current_id': self.id}
        }
    
    @api.multi
    def button_factura(self):
        self.ensure_one()
        return self.env.ref('motgama.reporte_factura_80').report_action(docids=[self.factura.id])
    
    # Placa
    @api.multi
    def button_reporte_placa(self):
        self.ensure_one()

        if not self.ultmovimiento.placa_vehiculo:
            raise Warning('No se registró placa de vehículo, puede hacer el reporte en el menú Procesos -> Placas Registradas')

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'motgama.wizard.placa',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('motgama.wizard_placa_form').id,
            'target': 'new',
            'name': 'Reportar placa ' + self.ultmovimiento.placa_vehiculo
        }