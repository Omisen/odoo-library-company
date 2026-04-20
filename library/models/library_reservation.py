import logging
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class LibraryReservation(models.Model):
    _name = "library.reservation"
    _description = "Library Reservation"
    _order = "reservation_date asc, id asc"

    book_id = fields.Many2one("library.book", required=True, ondelete="cascade")
    borrower_id = fields.Many2one("res.partner", required=True)
    reservation_date = fields.Date(default=fields.Date.context_today, readonly=True, copy=False)
    notification_date = fields.Date(readonly=True, copy=False)
    state = fields.Selection([
        ("waiting", "Waiting"),
        ("notified", "Notified"),
        ("expired", "Expired"),
        ("done", "Done"),
    ], default="waiting", required=True, copy=False)

    @api.constrains("book_id", "borrower_id", "state")
    def _check_reservation_consistency(self):
        active_states = ("waiting", "notified")
        for record in self:
            if not record.book_id or not record.borrower_id:
                continue

            existing = self.search([
                ("book_id", "=", record.book_id.id),
                ("borrower_id", "=", record.borrower_id.id),
                ("state", "in", active_states),
                ("id", "!=", record.id),
            ], limit=1)
            if existing:
                raise ValidationError(
                    _("This user already has an active reservation for this book.")
                )

            active_loan = self.env["library.loan"].search_count([
                ("book_id", "=", record.book_id.id),
                ("borrower_id", "=", record.borrower_id.id),
                ("state", "!=", "returned"),
            ])
            if active_loan:
                raise ValidationError(
                    _("This user already has this book on loan.")
                )

            if record.state == "waiting" and record.book_id.available_copies > 0:
                raise ValidationError(
                    _("This book is available. Create a loan instead of a reservation.")
                )

    def _send_notification_email(self):
        self.ensure_one()

        if not self.borrower_id.email:
            raise UserError(_("The borrower does not have an email address configured."))

        template = self.env.ref(
            "library.email_template_reservation_notify",
            raise_if_not_found=False,
        )
        if not template:
            raise UserError(_("The reservation email template was not found."))

        send_mail = getattr(template.sudo(), "send_mail", None)
        if not callable(send_mail):
            raise UserError(_("The reservation email template is not configured correctly."))

        try:
            send_mail(self.id, force_send=True)
        except Exception as err:
            _logger.exception(
                "Failed to send reservation notification for reservation %s",
                self.id,
            )
            raise UserError(
                _("Unable to send the notification email. Check the outgoing mail configuration.")
            ) from err

    def action_mark_notified(self):
        self.ensure_one()
        self.write({
            "state": "notified",
            "notification_date": fields.Date.context_today(self),
        })
        self._send_notification_email()
        return True

    @api.model
    def _notify_next_reservation(self, book):
        if not book:
            return False

        next_reservation = self.search([
            ("book_id", "=", book.id),
            ("state", "=", "waiting"),
        ], limit=1, order="reservation_date asc, id asc")

        if next_reservation:
            next_reservation.action_mark_notified()
        return next_reservation

    @api.model
    def _expire_old_reservations(self):
        limit_date = fields.Date.context_today(self) - timedelta(days=3)
        expired = self.search([
            ("state", "=", "notified"),
            ("notification_date", "!=", False),
            ("notification_date", "<=", limit_date),
        ])
        books = expired.mapped("book_id")
        expired.write({"state": "expired"})

        for book in books:
            self._notify_next_reservation(book)

        return len(expired)