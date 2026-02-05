from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Problem(models.Model):
    title = models.CharField(max_length=200)
    statement = models.TextField()
    score = models.IntegerField(default=100)
    time_limit = models.IntegerField(default = 2)
    memory_limit = models.IntegerField(default = 256)
    created_at = models.DateTimeField(auto_now_add = True)
    class Meta:
        ordering = ['score', 'created_at']
    def __str__(self):
        return self.title

# 以下のようなエクセルの表のようなものを作っている
# id (自動),title,statement,time_limit,memory_limit,created_at
# 1,A問題,1+1を...,2,256,2026/01/31...
# 2,B問題,数列を...,2,256,2026/01/31...

class TestCase(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='test_cases')
    input_data = models.TextField()
    output_data = models.TextField()
    is_sample = models.BooleanField(default=False)

class Submission(models.Model):
    STATUS_CHOICES = [
        ('WJ', 'Waiting for Judge'),
        ('AC', 'Accepted'),
        ('WA', 'Wrong Answer'),
        ('TLE', 'Time Limit Exceeded'),
        ('MLE', 'Memory Limit Exceeded'),
        ('RE', 'Runtime Error'),
        ('CE', 'Compilation Error'),
    ]
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.TextField()
    language = models.CharField(max_length=20)
    #choicesで入力される文字列を限定している
    status = models.CharField(max_length=3, choices=STATUS_CHOICES, default='WJ')
    created_at = models.DateTimeField(auto_now_add=True)