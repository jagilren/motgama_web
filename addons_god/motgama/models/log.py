from odoo import models, fields, api
from odoo.exceptions import Warning

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
            mailserver = self.env['ir.mail_server'].sudo().search([],limit=1)
            if not mailserver:
                email_from = ''
            else:
                email_from = mailserver.smtp_user
            valoresCorreo = {
                'subject': values['asunto'],
                'email_from': email_from,
                'email_to': values['correo'],
                'body_html': '<h3>' + values['descripcion'] + '</h3>',
                'author_id': False
            }
            correo = self.env['mail.mail'].sudo().create(valoresCorreo)
            if correo:
                correo.sudo().send()
        record = super().create(values)
        return record