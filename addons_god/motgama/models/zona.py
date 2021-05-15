from odoo import models, fields, api

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

    @api.multi
    def fuera_uso(self):
        self.ensure_one()

        for habitacion_id in self.habitacion_ids:
            flujo = self.env['motgama.flujohabitacion'].search([('codigo','=',habitacion_id.codigo)],limit=1)
            if not flujo or flujo.estado != 'D':
                continue

            reservas = self.env['motgama.reserva'].search([('habitacion_id','=',flujo.id)])
            if reservas:
                continue

            infomovimiento = {      # Crea registro de movimiento para colocar la hab fuera de uso                      P7.0.4R
                'habitacion_id':habitacion_id.id,
                'fueradeusohora':fields.Datetime().now(),
                'fueradeuso_uid':self.env.user.id,
                'observacion':'Zona fuera de uso',
                'fueradeuso_usuarioorden':self.env.user.id
            }
            nuevoMovimiento = self.env['motgama.movimiento'].create(infomovimiento)

            if nuevoMovimiento:
                flujo.sudo().write({'estado':'FU','ultmovimiento':nuevoMovimiento.id,'active':False})
            else:
                raise Warning('No se pudo cambiar el estado de la habitación')

        self.write({'estado':'FU'})
        valores = {
            'fecha': fields.Datetime().now(),
            'modelo': 'motgama.zona',
            'tipo_evento': 'correo',
            'asunto': 'La zona ' + self.nombre + ' ha sido puesta Fuera de Uso',
            'descripcion': 'El usuario ' + self.env.user.name + ' ha puesto la zona ' + self.nombre + ' en estado Fuera de Uso.'
        }
        self.env['motgama.log'].create(valores)
    
    @api.multi
    def habilitar(self):
        self.ensure_one()

        cods = []
        for habitacion_id in self.habitacion_ids:
            flujo = self.env['motgama.flujohabitacion'].search([('codigo','=',habitacion_id.codigo),('active','=',False)],limit=1)
            if not flujo or flujo.estado != 'FU':
                continue

            valoresMovto = {
                'habilitafecha':fields.Datetime().now(),
                'habilita_uid':self.env.user.id,
                'active':False
            }
            flujo.ultmovimiento.write(valoresMovto)

            valoresFlujo = {
                'estado':'D',
                'active':True
            }
            flujo.write(valoresFlujo)
        
        self.write({'estado':'H'})