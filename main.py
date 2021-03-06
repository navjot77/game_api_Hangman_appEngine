#!/usr/bin/env python

"""main.py - This file contains handlers that are called by taskqueue and/or
cronjobs."""

import webapp2
from google.appengine.api import mail, app_identity
from api import HangmanApi
from models import Game


class SendReminderEmail(webapp2.RequestHandler):
    def get(self):
        """Send a reminder email to each User with an email about games.
        Called every hour using a cron job"""
        app_id = app_identity.get_application_id()
        games=Game.query(Game.game_over == False)
        if games:
            for game in games:
                user_key=game.user
                user=user_key.get()
                user_name=user.name
                user_email=user.email
                if user_email:
                    subject = 'This is a reminder!'
                    body = 'Hello {}, Complete Your Game...!'.format(user_name)
                    # This will send test emails, the arguments to send_mail
                    #  are: from, to, subject, body
                    mail.send_mail('noreply@{}.appspotmail.com'.format(app_id),
                                   user_email,
                                   subject,
                                   body)


class UpdateAverageMovesRemaining(webapp2.RequestHandler):
    def post(self):
        """Update game listing announcement in memcache."""
        HangmanApi._cache_average_attempts()
        self.response.set_status(204)


app = webapp2.WSGIApplication([
    ('/crons/send_reminder', SendReminderEmail),
    ('/tasks/cache_average_attempts', UpdateAverageMovesRemaining),
], debug=True)
