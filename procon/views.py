import os
import tempfile
import docker
import time
import re
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import logout as django_logout
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views import generic
from django.db.models import Sum, Max
from django.contrib.auth.models import User
from .models import Problem, TestCase, Submission

class SignUpView(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'

def manual_logout(request):
    django_logout(request)
    return redirect('problem_list')

# --- ランキング表示 ---
def ranking(request):
    users = User.objects.all()
    ranking_data = []

    for user in users:
        # 各ユーザーごとに問題ごとの最高得点を合計する
        total_score = 0
        # ユーザーが提出した問題のIDリストを取得
        problem_ids = Submission.objects.filter(user=user).values_list('problem_id', flat=True).distinct()
        
        for pid in problem_ids:
            best_score = Submission.objects.filter(user=user, problem_id=pid).aggregate(Max('score'))['score__max'] or 0
            total_score += best_score
            
        if total_score > 0:
            last_success = Submission.objects.filter(user=user, score__gt=0).aggregate(Max('created_at'))['created_at__max']
            ranking_data.append({
                'username': user.username,
                'total_score': total_score,
                'last_success': last_success,
            })

    # スコア順（降順）、同点なら時間順（昇順）でソート
    ranking_data.sort(key=lambda x: (-x['total_score'], x['last_success'] if x['last_success'] else 0))

    return render(request, 'procon/ranking.html', {'users': ranking_data})

# --- Dockerジャッジエンジン (Django側で時間を計測) ---
def run_code_in_docker(language, code, input_data):
    client = docker.from_env()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file_path = os.path.join(tmpdir, 'input.txt')
        ext = 'py' if language == 'python' else 'cpp' if language == 'cpp' else 'c'
        code_file_path = os.path.join(tmpdir, f'sol.{ext}')

        with open(input_file_path, 'w', encoding='utf-8') as f:
            f.write(input_data)
        with open(code_file_path, 'w', encoding='utf-8') as f:
            f.write(code)

        # 救済のために内部の timeout は 10s に設定
        if language == 'python':
            exec_cmd = "timeout 10s python3 /judge/sol.py < /judge/input.txt; if [ $? -eq 124 ]; then echo '---LIMIT_EXCEEDED---'; fi"
        elif language == 'cpp':
            exec_cmd = "g++ /judge/sol.cpp -O3 -o /judge/sol.out && timeout 10s /judge/sol.out < /judge/input.txt; if [ $? -eq 124 ]; then echo '---LIMIT_EXCEEDED---'; fi"
        elif language == 'c':
            exec_cmd = "gcc /judge/sol.c -O3 -o /judge/sol.out && timeout 10s /judge/sol.out < /judge/input.txt; if [ $? -eq 124 ]; then echo '---LIMIT_EXCEEDED---'; fi"
        else:
            return "Unsupported Language", 0.0

        start_time = time.time() # 計測開始
        try:
            output = client.containers.run(
                image="judge-image",
                command=["sh", "-c", exec_cmd],
                volumes={tmpdir: {'bind': '/judge', 'mode': 'rw'}},
                network_disabled=True,
                mem_limit="512m", 
                stderr=True,
                remove=True
            )
            elapsed_time = time.time() - start_time # 計測終了
            return output.decode('utf-8').strip(), elapsed_time
        except Exception as e:
            return f"Error: {str(e)}", 0.0

# --- 問題一覧 (これが消えていた可能性があります) ---
def problem_list(request):
    problems = Problem.objects.all().order_by('score', 'created_at')
    user_score = 0
    solved_ids = []

    if request.user.is_authenticated:
        # 1. スコアが 0 より大きい提出がある問題の ID を取得
        # (これで AC も TLE(半分点) も対象になります)
        solved_ids = list(Submission.objects.filter(
            user=request.user, 
            score__gt=0
        ).values_list('problem_id', flat=True).distinct())
        
        # 2. 合計スコアの計算
        # 各問題の「自己ベストスコア」を足し合わせる
        total = 0
        for pid in solved_ids:
            # その問題に対する自分の提出の中で最大のスコアを取得
            best_for_problem = Submission.objects.filter(
                user=request.user, 
                problem_id=pid
            ).aggregate(Max('score'))['score__max'] or 0
            total += best_for_problem
        user_score = total
        
    else:
        # ゲストの場合も同様にセッションから取得
        user_score = request.session.get('guest_score', 0)
        solved_ids = request.session.get('guest_solved_ids', [])

    context = {
        'problems': problems,
        'user_score': user_score,
        'solved_ids': solved_ids,
    }
    return render(request, 'procon/problem_list.html', context)

# --- 問題詳細 & 判定ロジック ---
def problem_detail(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    samples = problem.test_cases.filter(is_sample=True)
    result = None
    lang = 'cpp'

    if request.method == 'POST':
        code = request.POST.get('code').replace('\r\n', '\n')
        lang = request.POST.get('language')
        testcases = TestCase.objects.filter(problem=problem)
        
        if not testcases.exists():
            result = "テストケースが登録されていません。"
        else:
            final_status = 'AC'
            is_slow = False
            earned_score = problem.score

            for tc in testcases:
                judge_res, elapsed_time = run_code_in_docker(lang, code, tc.input_data)
                
                if "---LIMIT_EXCEEDED---" in judge_res:
                    final_status = 'TLE'
                    earned_score = 0
                    break
                if "Error:" in judge_res:
                    final_status = 'RE'
                    earned_score = 0
                    break
                
                if judge_res.strip() != tc.output_data.strip():
                    final_status = 'WA'
                    earned_score = 0
                    break
                
                # 2.0秒を超えたら「遅い」フラグ（しきい値は適宜調整してください）
                if elapsed_time > 2.0:
                    is_slow = True

            if final_status == 'AC' and is_slow:
                final_status = 'TLE'
                earned_score = problem.score // 2

            if request.user.is_authenticated:
                Submission.objects.create(
                    problem=problem, user=request.user,
                    code=code, language=lang, status=final_status, score=earned_score
                )
                result = f"【参加者】判定完了: {final_status} (スコア: {earned_score})"
            # problem_detail 内のゲスト処理部分
            else:
                if 'guest_solved_ids' not in request.session:
                    request.session['guest_solved_ids'] = []
                
                # AC または TLE でスコアがある場合
                if earned_score > 0 and problem.id not in request.session['guest_solved_ids']:
                    current_score = request.session.get('guest_score', 0)
                    request.session['guest_score'] = current_score + earned_score
                    request.session['guest_solved_ids'].append(problem.id)
                    request.session.modified = True
                result = f"【ゲスト】判定完了: {final_status}"

    return render(request, 'procon/problem_detail.html', {
        'problem': problem, 'result': result, 'selected_lang': lang, 'samples': samples
    })