from django.db import models

class UserSession(models.Model):
    user_id = models.CharField(max_length=100)
    audio_file = models.FileField(upload_to='audio_files/', blank=True, null=True)
    audiotext = models.TextField(blank=True, null=True)  # Store text data directly
    feedbacktext = models.TextField(blank=True, null=True)  # Store feedback text directly
    created_at = models.DateTimeField(auto_now_add=True)
    

class Meta:
        # Specify the app label for the model
        app_label = 'users'
        db_table = "Audiotext"
