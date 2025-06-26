from celery import shared_task
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import Application, Job
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


@shared_task(bind=True, max_retries=settings.EMAIL_TASK_MAX_RETRIES)
def send_application_confirmation_email(self, application_id):
    """
    Send confirmation email to candidate after successful job application
    """
    try:
        application = Application.objects.select_related(
            'job__company', 'job__posted_by', 'candidate'
        ).get(id=application_id)
        
        candidate = application.candidate
        job = application.job
        company = job.company
        
        # Email subject
        subject = f"Application Confirmation - {job.title} at {company.name}"
        
        # Email context
        context = {
            'candidate_name': f"{candidate.first_name} {candidate.last_name}".strip() or candidate.email,
            'job_title': job.title,
            'company_name': company.name,
            'company_website': company.website,
            'job_location': job.location,
            'job_type': job.get_job_type_display(),
            'salary': job.salary,
            'application_date': application.applied_at.strftime('%B %d, %Y'),
            'application_status': application.get_status_display(),
        }
        
        # Render HTML email
        html_message = render_to_string('emails/application_confirmation.html', context)
        plain_message = strip_tags(html_message)
        
        # Send email
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[candidate.email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send()
        
        logger.info(f"Application confirmation email sent to {candidate.email} for job {job.title}")
        return f"Email sent successfully to {candidate.email}"
        
    except Application.DoesNotExist:
        logger.error(f"Application with ID {application_id} not found")
        raise
    except Exception as exc:
        logger.error(f"Failed to send application confirmation email: {str(exc)}")
        # Retry with exponential backoff
        raise self.retry(
            exc=exc,
            countdown=settings.EMAIL_TASK_RETRY_DELAY * (2 ** self.request.retries)
        )


@shared_task(bind=True, max_retries=settings.EMAIL_TASK_MAX_RETRIES)
def send_application_status_update_email(self, application_id, old_status, new_status):
    """
    Send email notification when application status is updated
    """
    try:
        application = Application.objects.select_related(
            'job__company', 'job__posted_by', 'candidate'
        ).get(id=application_id)
        
        candidate = application.candidate
        job = application.job
        company = job.company
        
        # Email subject based on status
        status_subjects = {
            'REV': f"Your application is under review - {job.title} at {company.name}",
            'INT': f"Interview invitation - {job.title} at {company.name}",
            'OFF': f"Job offer - {job.title} at {company.name}",
            'REJ': f"Application update - {job.title} at {company.name}",
        }
        
        subject = status_subjects.get(new_status, f"Application update - {job.title} at {company.name}")
        
        # Email context
        context = {
            'candidate_name': f"{candidate.first_name} {candidate.last_name}".strip() or candidate.email,
            'job_title': job.title,
            'company_name': company.name,
            'company_website': company.website,
            'old_status': dict(Application.STATUS_CHOICES).get(old_status, old_status),
            'new_status': dict(Application.STATUS_CHOICES).get(new_status, new_status),
            'status_code': new_status,
            'application_date': application.applied_at.strftime('%B %d, %Y'),
        }
        
        # Render HTML email
        html_message = render_to_string('emails/application_status_update.html', context)
        plain_message = strip_tags(html_message)
        
        # Send email
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[candidate.email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send()
        
        logger.info(f"Status update email sent to {candidate.email} for application {application_id}")
        return f"Status update email sent successfully to {candidate.email}"
        
    except Application.DoesNotExist:
        logger.error(f"Application with ID {application_id} not found")
        raise
    except Exception as exc:
        logger.error(f"Failed to send status update email: {str(exc)}")
        # Retry with exponential backoff
        raise self.retry(
            exc=exc,
            countdown=settings.EMAIL_TASK_RETRY_DELAY * (2 ** self.request.retries)
        )


@shared_task(bind=True, max_retries=settings.EMAIL_TASK_MAX_RETRIES)
def send_new_application_notification_to_employer(self, application_id):
    """
    Send notification email to employer when a new application is received
    """
    try:
        application = Application.objects.select_related(
            'job__company', 'job__posted_by', 'candidate'
        ).get(id=application_id)
        
        employer = application.job.posted_by
        candidate = application.candidate
        job = application.job
        company = job.company
        
        # Email subject
        subject = f"New Application Received - {job.title}"
        
        # Email context
        context = {
            'employer_name': f"{employer.first_name} {employer.last_name}".strip() or employer.email,
            'candidate_name': f"{candidate.first_name} {candidate.last_name}".strip() or candidate.email,
            'candidate_email': candidate.email,
            'job_title': job.title,
            'company_name': company.name,
            'application_date': application.applied_at.strftime('%B %d, %Y at %I:%M %p'),
            'cover_letter': application.cover_letter,
            'candidate_phone': candidate.phone,
        }
        
        # Render HTML email
        html_message = render_to_string('emails/new_application_notification.html', context)
        plain_message = strip_tags(html_message)
        
        # Send email
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[employer.email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send()
        
        logger.info(f"New application notification sent to employer {employer.email}")
        return f"Employer notification sent successfully to {employer.email}"
        
    except Application.DoesNotExist:
        logger.error(f"Application with ID {application_id} not found")
        raise
    except Exception as exc:
        logger.error(f"Failed to send employer notification email: {str(exc)}")
        # Retry with exponential backoff
        raise self.retry(
            exc=exc,
            countdown=settings.EMAIL_TASK_RETRY_DELAY * (2 ** self.request.retries)
        )


@shared_task
def send_bulk_email_notifications(application_ids, email_type='confirmation'):
    """
    Send bulk email notifications for multiple applications
    """
    results = []
    
    for app_id in application_ids:
        try:
            if email_type == 'confirmation':
                result = send_application_confirmation_email.delay(app_id)
            elif email_type == 'employer_notification':
                result = send_new_application_notification_to_employer.delay(app_id)
            else:
                continue
                
            results.append({
                'application_id': app_id,
                'task_id': result.id,
                'status': 'queued'
            })
        except Exception as e:
            results.append({
                'application_id': app_id,
                'error': str(e),
                'status': 'failed'
            })
    
    return results


@shared_task
def cleanup_old_email_tasks():
    """
    Periodic task to clean up old email task results
    This can be scheduled to run daily
    """
    from celery.result import AsyncResult
    from django_celery_results.models import TaskResult
    from datetime import datetime, timedelta
    
    # Delete task results older than 7 days
    cutoff_date = datetime.now() - timedelta(days=7)
    deleted_count = TaskResult.objects.filter(
        date_created__lt=cutoff_date
    ).delete()[0]
    
    logger.info(f"Cleaned up {deleted_count} old email task results")
    return f"Cleaned up {deleted_count} old task results"