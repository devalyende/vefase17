from odoo import models, fields, api


class Container(models.Model):
    _name = 'container.lines'
    _inherit = ['mail.thread']
    _description = 'Contenedores'
    _rec_name = 'container_code'

    container_code = fields.Char(string='Numero del Contenedor', required=True, tracking=True)
    attached_file_a = fields.Many2many('ir.attachment', 'file_a_att', 'product_id', 'attachment_id', string='Adjuntar', tracking=True)
    attached_file_b = fields.Many2many('ir.attachment', 'file_b_att', 'product_id', 'attachment_id', string='Adjuntar', tracking=True)
    attached_file_c = fields.Many2many('ir.attachment', 'file_c_att', 'product_id', 'attachment_id', string='Adjuntar', tracking=True)
    bl_code = fields.Char(string='Numero de BL', tracking=True)
    size_id = fields.Many2one(
                'size.parameter',
                string='Medidas',
                help='Selecione una medida para el contenedor',
                tracking=True
    )
    products_ids = fields.One2many('container.product.lines', 'product_id', string='Productos de Importación', tracking=True)
    fiscal_ids = fields.One2many('container.fiscal.lines', 'product_id', string='Gastos Fiscales', tracking=True)
    financial_ids = fields.One2many('container.financial.lines', 'product_id', string='Gastos Financieros', tracking=True)
    total_price = fields.Float(string='Total Bsf.', compute='_compute_total_general', store=True, tracking=True)
    total_currency = fields.Float(string='Total $', compute='_compute_total_general', store=True, tracking=True)
    rate = fields.Float(string='Tasa', tracking=True)
    total_price_fiscal = fields.Float(string='Total Bsf.', compute='_compute_total_general', store=True, tracking=True)
    total_currency_fiscal = fields.Float(string='Total $', compute='_compute_total_general', store=True, tracking=True)
    total_price_financial = fields.Float(string='Total Bsf.', compute='_compute_total_general', store=True, tracking=True)
    total_currency_financial = fields.Float(string='Total $', compute='_compute_total_general', store=True, tracking=True)
    status = fields.Boolean("Disponibilidad", default=False)
    currency_id = fields.Many2one('res.currency', string="Moneda", 
                                    default=lambda self: self.env.ref('base.VEF'), readonly=1)
    currency_id2 = fields.Many2one('res.currency', string="Moneda Secundaria", 
                                    default=lambda self: self.env.ref('base.USD'), readonly=1)

    @api.depends('products_ids.total_price', 'products_ids.total_currency',
                'fiscal_ids.unit_price', 'fiscal_ids.currency_unit_price',
                'financial_ids.unit_price', 'financial_ids.currency_unit_price')
    def _compute_total_general(self):
        price = 0
        currency = 0
        fiscal_price = 0 
        fiscal_currency = 0
        financial_price = 0
        financial_currency = 0
        for rec in self.products_ids:
            price += rec.total_price
            currency += rec.total_currency
        for rec in self.fiscal_ids:
            fiscal_price += rec.unit_price
            fiscal_currency += rec.currency_unit_price
        for rec in self.financial_ids:
            financial_price += rec.unit_price
            financial_currency += rec.currency_unit_price    
        self.total_price = price
        self.total_currency = currency
        self.total_price_fiscal = fiscal_price
        self.total_currency_fiscal = fiscal_currency
        self.total_price_financial = financial_price
        self.total_currency_financial = financial_currency



class ContainerLines(models.Model):
    _name = 'container.product.lines'
    _description = 'Productos del Contenedor'
    _rec_name = 'product_id'

    currency_id = fields.Many2one('res.currency', string="Moneda", 
                                    default=lambda self: self.env.ref('base.VEF'), readonly=1)
    currency_id2 = fields.Many2one('res.currency', string="Moneda Secundaria", 
                                    default=lambda self: self.env.ref('base.USD'), readonly=1)
    product_id = fields.Many2one('container.lines', 'Contenedor')
    product_qty = fields.Integer(string='Cantidad')
    unit_price = fields.Float(string='Precio en Bs.')
    currency_unit_price = fields.Float(string='Precio en $', compute="_compute_currency_unit_price")
    products_id = fields.Many2one(
                'product.template',
                string='Producto',
                domain=[('purchase_ok', '=', True)],
                help='Selecione la lista de Productos que tendra el contenedor'
    )
    total_price = fields.Float(string='Total en Bolivares', compute='_compute_total', store=True)
    total_currency = fields.Float(string='Total en $', compute='_compute_total_currency', store=True)

    @api.depends('product_id.rate', 'unit_price')
    def _compute_currency_unit_price(self):
        for rec in self:
            if rec.product_id.rate:
                rec.currency_unit_price = rec.unit_price / rec.product_id.rate
            else:
                rec.currency_unit_price = 0.0

    @api.depends('product_qty', 'unit_price', 'currency_unit_price')
    def _compute_total(self):
        for rec in self:
            rec.total_price = rec.product_qty * rec.unit_price

    @api.depends('product_qty', 'currency_unit_price')
    def _compute_total_currency(self):
        for rec in self:
            rec.total_currency = rec.product_qty * rec.currency_unit_price



class ContainerFiscalLines(models.Model):
    _name = 'container.fiscal.lines'
    _description = 'Gastos Fiscales del Contenedor'
    _rec_name = 'product_id'

    currency_id = fields.Many2one('res.currency', string="Moneda", 
                                    default=lambda self: self.env.ref('base.VEF'), readonly=1)
    currency_id2 = fields.Many2one('res.currency', string="Moneda Secundaria", 
                                    default=lambda self: self.env.ref('base.USD'), readonly=1)
    product_id = fields.Many2one('container.lines', 'Contenedor')
    unit_price = fields.Float(string='Total en Bs.')
    fiscal_rate = fields.Float(string='Tasa')
    currency_unit_price = fields.Float(string='Total en $', compute="_compute_fiscal_total_rate")
    products_id = fields.Many2one('fiscal.expenses', string='Gastos Fiscal')

    @api.depends('fiscal_rate')
    def _compute_fiscal_total_rate(self):
        for rec in self:
            if rec.fiscal_rate:
                rec.currency_unit_price = rec.unit_price / rec.fiscal_rate
            else:
                rec.currency_unit_price = 0.0


class ContainerFinancialLines(models.Model):
    _name = 'container.financial.lines'
    _description = 'Gastos Financieros del Contenedor'
    _rec_name = 'product_id'

    currency_id = fields.Many2one('res.currency', string="Moneda", 
                                    default=lambda self: self.env.ref('base.VEF'), readonly=1)
    currency_id2 = fields.Many2one('res.currency', string="Moneda Secundaria", 
                                    default=lambda self: self.env.ref('base.USD'), readonly=1)
    product_id = fields.Many2one('container.lines', 'Contenedor')
    unit_price = fields.Float(string='Total en Bs.')
    financial_rate = fields.Float(string='Tasa')
    currency_unit_price = fields.Float(string='Total en $', compute="_compute_financial_total_rate")
    products_id = fields.Many2one('financial.expenses', string='Gastos Financieros')

    @api.depends('financial_rate')
    def _compute_financial_total_rate(self):
        for rec in self:
            if rec.financial_rate:
                rec.currency_unit_price = rec.unit_price / rec.financial_rate
            else:
                rec.currency_unit_price = 0.0
