import time
from django.conf import settings
from django.core import mail
from django.core.mail.message import EmailMessage
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify
from fdfgen import forge_fdf
import subprocess
import os
import tempfile
import shutil

from base import models as base_models
from base import actions as base_actions
from base.email_templates import CERTIFICATE


BATCH_SIZE = 10
BATCH_TIMER = 20


class Command(BaseCommand):
    help = 'Send participation certificates to checked-in participants'

    def add_arguments(self, parser):
        parser.add_argument('-d', '--dry-run', default=False, action='store_true')
        parser.add_argument('-n', '--no-clean', default=False, action='store_true', help="Don't clean generated certificates")
        parser.add_argument('-b', '--batch', default=BATCH_SIZE)
        parser.add_argument('--names', default=False, action='store_true', help='Print names of participants as the emails are generated')
        parser.add_argument('--resend', default=None, help='Resend the certificate for a specific participant (by username)')

    def handle(self, *args, **options):
        if options['resend']:
            self.stdout.write("Resending for {}".format(options['resend']))
            checked_in = [base_models.Participant.objects.get(user__username=options['resend'])]
        else:
            self.stdout.write("Sending certifications to checked-in blue team participants")
            checked_in = base_models.Participant.objects.filter(checked_in=True, is_red=False, is_green=False,
                                                                team__isnull=False)

        cert_file = base_actions.get_global_setting('certificate_template')
        if not cert_file:
            self.stderr.write(self.style.ERROR('You need to specify a certificate template'))
            raise CommandError("Certificate not sepcified")
        cert_file = os.path.join(settings.MEDIA_ROOT, cert_file.name)
        self.stdout.write("Using certificate: {}".format(cert_file), self.style.MIGRATE_HEADING)

        cdc_name = base_actions.get_global_setting('competition_name')
        cdc_date = base_actions.get_global_setting('competition_date').strftime('%B %-d, %Y')
        emails = []

        tmp = tempfile.mkdtemp(prefix="signup-certs")

        num = 0
        for participant in checked_in:
            fields = [
                ('participant_name', participant.user.get_full_name()),
                ('cdc_name', cdc_name),
                ('issue_date', cdc_date),
            ]

            outfile = slugify(participant.user.username) + '.pdf'

            # Forge FDF
            fdf = forge_fdf("", fields, [], [], [])
            with open(os.path.join(tmp, 'data.fdf'), 'w') as fp:
                fp.write(fdf)

            # Fill PDF
            subprocess.check_call(["pdftk", cert_file, 'fill_form', 'data.fdf', 'output', outfile, 'flatten'], cwd=tmp)

            subject = "[CDC] {} Certificate".format(cdc_name)
            body = CERTIFICATE.format(fname=participant.user.first_name, lname=participant.user.last_name,
                                      support=settings.SUPPORT_EMAIL)

            message = EmailMessage(subject, body, settings.SUPPORT_EMAIL, [participant.user.email],
                                   reply_to=[settings.SUPPORT_EMAIL])
            message.attach_file(os.path.join(tmp, outfile))
            emails.append(message)
            if options['names']:
                self.stdout.write(" -> Generated Email for {}".format(participant))

            if not options['dry_run']:
                self.stdout.write(" -> Sending mail for {}".format(participant), self.style.MIGRATE_SUCCESS)
                message.send()
                num += 1

                if num > options['batch']:
                    time.sleep(BATCH_TIMER)
                    num = 0

        if not options['no_clean']:
            shutil.rmtree(tmp)
