from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

class LibraryReservation(models.Model):
    _name = "library.reservation"
    _description = "Library Reservation"
    _order = "reservation_date asc"
    
    book_id = fields.Many2one('library.book', required=True, ondelete='cascade')
    borrower_id = fields.Many2one('res.partner', required=True)
    reservation_date = fields.Datetime(default=fields.Date.context_today, readonly=True)
    state = fields.Selection([
        ('waiting', 'In attesa'),
        ('notified', 'Notificato'),
        ('expired', 'Scaduta'),
        ('done', 'Completata'),
    ], default='waiting')
    
    
    @api.model_create_multi
    def create(self, vals_list):
        pass