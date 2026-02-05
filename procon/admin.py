from django.contrib import admin
from .models import Problem, TestCase, Submission

class TestCaseInline(admin.TabularInline):
    model = TestCase
    extra = 1

@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    inlines = [TestCaseInline]
    list_display = ('title', 'time_limit', 'memory_limit', 'created_at')

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    # 表示する項目に 'status' を含める
    list_display = ('created_at', 'user', 'problem', 'language', 'colored_status')
    
    # 右側にフィルターを設置（ユーザー別、問題別、結果別で絞り込める）
    list_filter = ('user', 'problem', 'status', 'language')
    
    # 検索ボックス（ユーザー名や問題タイトルで検索可能に）
    search_fields = ('user__username', 'problem__title')

    # 見やすくするために、ステータスに色をつける関数
    @admin.display(description='判定結果')
    def colored_status(self, obj):
        from django.utils.html import format_html
        colors = {
            'AC': '#00ff00', # 緑
            'WA': '#ff0000', # 赤
            'TLE': '#ffa500', # オレンジ
            'WJ': '#888888', # グレー
        }
        color = colors.get(obj.status, '#000000')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )