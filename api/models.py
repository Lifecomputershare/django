from django.db import models
from django.conf import settings


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Company(TimeStampedModel):
    name = models.CharField(max_length=255)
    industry = models.CharField(max_length=255, blank=True)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)


class SubscriptionPlan(TimeStampedModel):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    job_limit = models.IntegerField()
    ai_match_limit = models.IntegerField()
    duration_days = models.IntegerField()


class CompanySubscription(TimeStampedModel):
    PAYMENT_STATUS_PENDING = "pending"
    PAYMENT_STATUS_PAID = "paid"
    PAYMENT_STATUS_FAILED = "failed"

    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_STATUS_PENDING, "Pending"),
        (PAYMENT_STATUS_PAID, "Paid"),
        (PAYMENT_STATUS_FAILED, "Failed"),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name="subscriptions")
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    payment_status = models.CharField(max_length=16, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_STATUS_PENDING)


class UserProfile(TimeStampedModel):
    ROLE_ADMIN = "admin"
    ROLE_RECRUITER = "recruiter"
    ROLE_CANDIDATE = "candidate"

    ROLE_CHOICES = [
        (ROLE_ADMIN, "Admin"),
        (ROLE_RECRUITER, "Recruiter"),
        (ROLE_CANDIDATE, "Candidate"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=32, choices=ROLE_CHOICES)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name="users")
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)


class Job(TimeStampedModel):
    JOB_TYPE_FULL_TIME = "full_time"
    JOB_TYPE_PART_TIME = "part_time"
    JOB_TYPE_CONTRACT = "contract"
    JOB_TYPE_INTERNSHIP = "internship"

    JOB_TYPE_CHOICES = [
        (JOB_TYPE_FULL_TIME, "Full time"),
        (JOB_TYPE_PART_TIME, "Part time"),
        (JOB_TYPE_CONTRACT, "Contract"),
        (JOB_TYPE_INTERNSHIP, "Internship"),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="jobs")
    title = models.CharField(max_length=255)
    description = models.TextField()
    salary_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    location = models.CharField(max_length=255)
    job_type = models.CharField(max_length=32, choices=JOB_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)


class Application(models.Model):
    STATUS_PENDING = "pending"
    STATUS_REVIEWED = "reviewed"
    STATUS_REJECTED = "rejected"
    STATUS_HIRED = "hired"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_REVIEWED, "Reviewed"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_HIRED, "Hired"),
    ]

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications")
    resume_file = models.FileField(upload_to="resumes/")
    match_score = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_PENDING)
    applied_at = models.DateTimeField(auto_now_add=True)


class AIMatchLog(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="match_logs")
    similarity_score = models.FloatField()
    keywords_matched = models.JSONField(default=list)
    processed_at = models.DateTimeField(auto_now_add=True)


class UserAuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    method = models.CharField(max_length=8)
    path = models.CharField(max_length=512)
    status_code = models.IntegerField(null=True, blank=True)
    ip_address = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
