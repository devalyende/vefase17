from odoo import models, fields, api


class ImportsVefase(models.Model):
    _name = 'imports.vefase'
    _inherit = ['mail.thread']
    _description = 'Importaciones Vefase'
    _rec_name = 'bl_code'

    bl_code = fields.Char(string='Numero de Control', required=True, tracking=True)
    description = fields.Text(string='Description', tracking=True)
    stage = fields.Selection([
        ('new', 'Nuevo'),
        ('in_process', 'En Proceso'),
        ('complete', 'Completado'),
        ('cancel', 'Cancelado')
    ], string='Estatus', group_expand='_expand_stages', default='new', tracking=True)
    priority = fields.Selection([
        ('0', 'Ninguna'),
        ('1', 'Baja'),
        ('2', 'Media'),
        ('3', 'Alta'),
    ], 'Prioridad', default='0', tracking=True)
    partner_id = fields.Many2one(
                'res.partner',
                string='Proveedor',
                domain=[('international_type', '=', True)],
                help='Selecione una Empresa de tipo Internacional',
                tracking=True
    )
    country_id = fields.Many2one('res.country', string='Pais de Origen', tracking=True)
    origin_city = fields.Char(string='Ciudad de Origen', tracking=True)
    destiny_country_id = fields.Many2one('res.country', string='Pais de Destino', tracking=True)
    destiny_city = fields.Char(string='Ciudad de Destino', tracking=True)
    loading_port = fields.Many2one('loading.unloading', string='Puerto de Carga', tracking=True)
    discharge_port = fields.Many2one('loading.unloading', string='Puerto de Descarga', tracking=True)
    current_location = fields.Char(string='Ubicacion Actual', tracking=True)
    import_type = fields.Selection(
                [('null', ''), ('maritimo', 'Marítimo'), ('aereo', 'Aéreo')],
                string='Medio de Importación',
                required=True,
                default='null',
                help='Seleccione el tipo de importación: marítimo o aéreo',
                tracking=True
    )
    aereal_id = fields.Many2one('company.aereal', string='Compañía Responsable', tracking=True)
    nautical_id = fields.Many2one('company.nautical', string='Compañía Responsable', tracking=True)
    estimated_date = fields.Date(string='Fecha de Llegada', tracking=True)
    limit_pay_date = fields.Date(string='Fecha Limite de Pago', tracking=True)
    delivery_date = fields.Date(string='Fecha de Entrega', tracking=True)
    delivery_number = fields.Char(string='Numero de Guia', tracking=True)
    container_ids = fields.One2many('imports.vefase.lines', 'container_id', string='Nombre', tracking=True)
    notes = fields.Html(string="Notas", tracking=True)
    checklist_ids = fields.One2many('check.list.lines', 'container_id', tracking=True)
    todo_check = fields.Char(string="Tareas Pendiente", compute="_compute_todo", tracking=True)
    todo_name = fields.Char(string="Ultima Tarea", compute="_compute_todo_name", tracking=True)
    account_ids = fields.Many2one('account.account', string='Cuenta Asociada')
    currency_id = fields.Many2one('res.currency', string="Moneda", 
                                    default=lambda self: self.env.ref('base.VEF'), readonly=1)
    currency_id2 = fields.Many2one('res.currency', string="Moneda Secundaria", 
                                    default=lambda self: self.env.ref('base.USD'), readonly=1)
    total_import = fields.Float(string="Total en Bs.", compute="_compute_total_import")
    total_import_rate = fields.Float(string="Total en $", compute="_compute_total_import")

    def _expand_stages(self, states, domain, order):
        # return all stages
        return [key for key, val in type(self).stage.selection]

    @api.depends('checklist_ids.status')
    def _compute_todo(self):
        for rec in self:
            lines = rec.checklist_ids.filtered(lambda r: not r.status)
            if not rec.checklist_ids:
                rec.todo_check = 'No hay tareas pendientes'
            elif not lines:
                rec.todo_check = 'Se han realizado todas las tareas'
            elif len(lines) == 1:
                rec.todo_check = 'Hay 1 tarea pendiente'
            else:
                rec.todo_check = f'Hay {len(lines)} tareas pendientes'

    @api.depends('checklist_ids.checklist_id.name')
    def _compute_todo_name(self):
        for rec in self:
            lines = rec.checklist_ids.filtered(lambda r: not r.status)
            if not lines:
                rec.todo_name = False
            else:
                rec.todo_name = lines[-1].checklist_id.name

    @api.depends('container_ids')
    def _compute_total_import(self):
        total_import = 0
        total_import_rate = 0
        for rec in self.container_ids:
            total_import += rec.total_price + rec.total_fiscal + rec.total_financial
            total_import_rate += rec.total_currency + rec.total_fiscal_rate + rec.total_financial_rate
        self.total_import = total_import
        self.total_import_rate = total_import_rate


class ImportsLines(models.Model):
    _name = 'imports.vefase.lines'
    _description = 'Contenedores de la Importacion'
    _rec_name = 'container_id'

    currency_id = fields.Many2one('res.currency', string="Moneda", 
                                    default=lambda self: self.env.ref('base.VEF'), readonly=1)
    currency_id2 = fields.Many2one('res.currency', string="Moneda Secundaria", 
                                    default=lambda self: self.env.ref('base.USD'), readonly=1)
    containers_id = fields.Many2one('container.lines', string='Contenedor',
                                    domain=[('status', '=', False)])
    container_id = fields.Many2one('imports.vefase')
    total_price = fields.Float(related='containers_id.total_price')
    total_currency = fields.Float(related='containers_id.total_currency')
    total_financial = fields.Float(related='containers_id.total_price_financial')
    total_fiscal = fields.Float(related='containers_id.total_price_fiscal')
    total_financial_rate = fields.Float(related='containers_id.total_currency_financial')
    total_fiscal_rate = fields.Float(related='containers_id.total_currency_fiscal')

    @api.model
    def create(self, vals):
        record = super().create(vals)
        if record.containers_id:
            record.containers_id.write({'status': True})
            record.containers_id.write({'bl_code': record.container_id.bl_code})
        return record

    def unlink(self):
        for record in self:
            bl_code = ''
            if record.containers_id:
                record.containers_id.write({'status': False})
                record.containers_id.write({'bl_code': bl_code})
        return super().unlink()

class ChecklistLines(models.Model):
    _name = 'check.list.lines'
    _description = 'Checklist de la Improtacion'
    _rec_name = 'checklist_id'

    checklist_id = fields.Many2one('check.list', string='Checklist')
    container_id = fields.Many2one('imports.vefase')
    status = fields.Boolean("Estatus")
