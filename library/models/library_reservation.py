from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

import logging

_logger = logging.getLogger(__name__)


class LibraryReservation(models.Model):
    _name = "library.reservation"
    _description = "Library Reservation"
    _order = "reservation_date asc"
    
    book_id = fields.Many2one('library.book', required=True, ondelete='cascade')
    borrower_id = fields.Many2one('res.partner', required=True)
    reservation_date = fields.Date(default=fields.Date.context_today, readonly=True)
    state = fields.Selection([
        ('waiting', 'Waiting'),
        ('notified', 'Notified'),
        ('expired', 'Expired'),
        ('done', 'Done'),
    ], default='waiting')
    
    
    @api.constrains('book_id', 'borrower_id')
    def _check_duplicate(self):
        for record in self:
            existing = self.search([
                ('book_id', '=', record.book_id.id),
                ('borrower_id', '=', record.borrower_id.id),
                ('state', '=', 'waiting'),
                ('id', '!=', record.id),
            ])
            if existing:
                raise ValidationError(
                    _('This user already has a reservation for this book.')
                )

    def _send_notification_email(self):
        self.ensure_one()

        if not self.borrower_id.email:
            raise UserError(_('The borrower does not have an email address configured.'))

        template = self.env.ref(
            'library.email_template_reservation_notify',
            raise_if_not_found=False,
        )
        if not template:
            raise UserError(_('The reservation email template was not found.'))

        send_mail = getattr(template.sudo(), 'send_mail', None)
        if not callable(send_mail):
            raise UserError(_('The reservation email template is not configured correctly.'))

        try:
            send_mail(self.id, force_send=True)
        except Exception as err:
            _logger.exception(
                'Failed to send reservation notification for reservation %s',
                self.id,
            )
            raise UserError(
                _('Unable to send the notification email. Check the outgoing mail configuration.')
            ) from err
            
    
    @api.model
    def _expire_old_reservations(self):
        from datetime import timedelta
        limit = fields.Datetime.now() - timedelta(days=3)
        expired = self.search([
            ('state', '=', 'notified'),
            ('reservation_date', '<', limit),
        ])
        expired.write({'state': 'expired'})
        # notifica prossimo in lista
        for res in expired:
            next_res = self.search([
                ('book_id', '=', res.book_id.id),
                ('state', '=', 'waiting'),
            ], limit=1, order='reservation_date asc')
            if next_res:
                next_res.state = 'notified'
                next_res._send_notification_email()