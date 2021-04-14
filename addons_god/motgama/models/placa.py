from odoo import models, fields, api

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