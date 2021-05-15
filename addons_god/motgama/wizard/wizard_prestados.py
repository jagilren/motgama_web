from odoo import fields, models, api
from odoo.exceptions import Warning

class MotgamaConfirmPrestados(models.TransientModel):
    _name = 'motgama.confirm.prestados'
    _description = 'Mensaje de confirmación al liquidar o recaudar si existen objetos prestados'

    texto = fields.Text(string="",compute="_compute_texto")
    habitacion = fields.Many2one(comodel_name="motgama.flujohabitacion", default=lambda self: self._get_habitacion())

    @api.model
    def _get_habitacion(self):
        habitacion = self.env.context['active_id']
        if self.env['motgama.flujohabitacion'].search([('id','=',habitacion)],limit=1):
            return habitacion
        else:
            raise Warning('Error del sistema')

    @api.depends('habitacion')
    def _compute_texto(self):
        for record in self:
            if record.habitacion:
                if record.habitacion.estado in ['OO','OA']:
                    record.texto = "Existen actualmente objetos prestados en la habitacion ¿Está seguro que desea liquidar?"
                elif record.habitacion.estado == 'LQ':
                    record.texto = "Existen actualmente objetos prestados en la habitacion ¿Está seguro que desea recaudar?"

    @api.multi
    def confirmar(self):
        self.ensure_one()
        if self.habitacion.estado in ['OO','OA']:
            self.habitacion.write({'puede_liquidar': True})
            self.habitacion.button_liquidar()
        if self.habitacion.estado == 'LQ':
            self.habitacion.write({'puede_recaudar': True})
            return self.habitacion.button_recaudar()
        
        return True

class MotgamaWizardEntregaprestados(models.TransientModel):
    _name = 'motgama.wizard_entregaprestados'
    _description = 'Entrega Objetos Prestados'
    fecha = fields.Datetime(string=u'fecha entrega',default=lambda self: fields.Datetime().now())
    observacion = fields.Char(string='Observaciones')
    estado_devolucion = fields.Selection(string='Estado devolución',selection=[('ok','Devuelto en buen estado'),('mal','Devuelto en mal estado'),('no','No devuelto')],default='ok')

    @api.multi
    def entregar_objeto(self):
        self.ensure_one()
        if not self.env.ref('motgama.motgama_devuelve_prestados') in self.env.user.permisos:
            raise Warning('No tiene permitido devolver objetos prestados, contacte al administrador')

        idObjeto = self.env.context['active_id']
        objeto = self.env['motgama.objprestados'].search([('id','=',idObjeto)],limit=1)

        valores = {
            'devueltofecha': self.fecha,
            'devuelto_uid': self.env.user.id,
            'entregadonota': self.observacion,
            'estado_devolucion': self.estado_devolucion,
            'active': False
        }

        objeto.write(valores)
        objeto.habitacion_id.refresh_views()