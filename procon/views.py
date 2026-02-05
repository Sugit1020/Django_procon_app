import os
import tempfile
import docker
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import logout as django_logout
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views import generic
from django.db.models import Sum
from .models import Problem, TestCase, Submission

class SignUpView(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'

def manual_logout(request):
    django_logout(request)
    return redirect('problem_list')

# --- Dockerジャッジエンジン (巨大データ対応版) ---
def run_code_in_docker(language, code, input_data):
    client = docker.from_env()
    
    # 1. 一時ディレクトリを作成（判定後に自動で物理削除される）
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file_path = os.path.join(tmpdir, 'input.txt')
        
        # 拡張子の決定
        ext = 'py' if language == 'python' else 'cpp' if language == 'cpp' else 'c'
        code_file_path = os.path.join(tmpdir, f'sol.{ext}')

        # 2. ファイルに書き込む（これで引数の長さ制限を回避）
        with open(input_file_path, 'w', encoding='utf-8') as f:
            f.write(input_data)
        with open(code_file_path, 'w', encoding='utf-8') as f:
            f.write(code)

        # 3. 実行コマンド（timeoutが124を返した時にTLEを識別する文字列を出す）
        if language == 'python':
            exec_cmd = "timeout 1s python3 /judge/sol.py < /judge/input.txt; if [ $? -eq 124 ]; then echo '---TLE_DETECTED---'; fi"
        elif language == 'cpp':
            exec_cmd = "g++ /judge/sol.cpp -O3 -o /judge/sol.out && timeout 1s /judge/sol.out < /judge/input.txt; if [ $? -eq 124 ]; then echo '---TLE_DETECTED---'; fi"
        elif language == 'c':
            exec_cmd = "gcc /judge/sol.c -O3 -o /judge/sol.out && timeout 1s /judge/sol.out < /judge/input.txt; if [ $? -eq 124 ]; then echo '---TLE_DETECTED---'; fi"
        else:
            return "Unsupported Language"

        try:
            # 4. Docker実行（tmpdir を コンテナ内の /judge にマウント）
            output = client.containers.run(
                image="judge-image",
                command=["sh", "-c", exec_cmd],
                volumes={tmpdir: {'bind': '/judge', 'mode': 'rw'}},
                network_disabled=True,
                mem_limit="512m", 
                stderr=True,
                remove=True
            )
            return output.decode('utf-8').strip()
        except Exception as e:
            return f"Error: {str(e)}"

# --- View関数 ---

def problem_list(request):
    problems = Problem.objects.all().order_by('score', 'created_at')
    user_score = 0
    solved_ids = []

    if request.user.is_authenticated:
        solved_ids = list(Submission.objects.filter(
            user=request.user, 
            status='AC'
        ).values_list('problem_id', flat=True).distinct())
        user_score = Problem.objects.filter(id__in=solved_ids).aggregate(Sum('score'))['score__sum'] or 0
    else:
        user_score = request.session.get('guest_score', 0)
        solved_ids = request.session.get('guest_solved_ids', [])

    context = {
        'problems': problems,
        'user_score': user_score,
        'solved_ids': solved_ids,
    }
    return render(request, 'procon/problem_list.html', context)

def problem_detail(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    samples = problem.test_cases.filter(is_sample=True)
    result = None
    lang = 'cpp' # デフォルトを C++ に設定

    if request.method == 'POST':
        code = request.POST.get('code').replace('\r\n', '\n')
        lang = request.POST.get('language')
        testcases = TestCase.objects.filter(problem=problem)
        
        if not testcases.exists():
            result = "テストケースが登録されていません。"
        else:
            final_status = 'AC'
            for tc in testcases:
                judge_res = run_code_in_docker(lang, code, tc.input_data)
                
                # 特殊ステータスの判定
                if "---TLE_DETECTED---" in judge_res:
                    final_status = 'TLE'
                    break
                if "Error:" in judge_res:
                    final_status = 'RE'
                    break
                
                actual = judge_res.strip()
                expected = tc.output_data.strip()

                if actual != expected:
                    final_status = 'WA'
                    break

            # 保存処理
            if request.user.is_authenticated:
                Submission.objects.create(
                    problem=problem, user=request.user,
                    code=code, language=lang, status=final_status
                )
                result = f"【参加者】判定完了: {final_status}"
            else:
                if 'guest_solved_ids' not in request.session:
                    request.session['guest_solved_ids'] = []
                
                if final_status == 'AC' and problem.id not in request.session['guest_solved_ids']:
                    current_score = request.session.get('guest_score', 0)
                    request.session['guest_score'] = current_score + problem.score
                    request.session['guest_solved_ids'].append(problem.id)
                    request.session.modified = True
                
                result = f"【ゲスト】判定完了: {final_status}"

    return render(request, 'procon/problem_detail.html', {
        'problem': problem, 
        'result': result, 
        'selected_lang': lang, 
        'samples': samples
    })