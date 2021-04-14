from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import UserError,Warning, ValidationError

class MotgamaCalendario(models.Model):#ok
#    Fields:CALENDARIO: Listas de precios a aplicar por cada dia de la semana, diurno y nocturno
    _name = 'motgama.calendario'
    _description = u'Calendario'
    _rec_name = 'diasemana'
    _order = 'diasemana ASC'
    _sql_constraints = [('codigo_uniq', 'unique (diasemana)', "El dia ya Existe, Verifique!")]
    diasemana = fields.Selection(string=u'Día Semana',selection=[('0', 'Lunes'), ('1', 'Martes'), ('2', 'Miércoles'), ('3', 'Jueves'), ('4', 'Viernes'), ('5', 'Sábado'), ('6', 'Domingo')])
    listapreciodia = fields.Selection(string=u'Lista precio Día',selection=[('1', 'L1'),('2', 'L2'),('3', 'L3'),('4', 'L4'),('5', 'L5')],required=True)    
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