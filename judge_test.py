import docker

def run_code_in_docker(language, code, input_data):
    client = docker.from_env()

    # 1. コードを保存してコンパイルし、最後に入力を受け取って実行するコマンドを組み立て
    if language == 'python':
        # Python: sol.pyに保存 -> 実行
        exec_cmd = f"cat << 'EOF' > sol.py\n{code}\nEOF\necho '{input_data}' | timeout 2s python3 sol.py"
    elif language == 'cpp':
        # C++: sol.cppに保存 -> コンパイル -> 実行
        exec_cmd = f"cat << 'EOF' > sol.cpp\n{code}\nEOF\ng++ sol.cpp -o sol.out && echo '{input_data}' | timeout 2s ./sol.out"
    elif language == 'c':
        # C: sol.cに保存 -> コンパイル -> 実行
        exec_cmd = f"cat << 'EOF' > sol.c\n{code}\nEOF\ngcc sol.c -o sol.out && echo '{input_data}' | timeout 2s ./sol.out"
    else:
        return "Unsupported Language"

    try:
        # 2. コンテナを実行
        output = client.containers.run(
            image="judge-image",
            command=["sh", "-c", exec_cmd],
            network_disabled=True,
            mem_limit="256m",
            stderr=True,
            remove=True
        )
        return output.decode('utf-8').strip()
    except Exception as e:
        # コンパイルエラーやタイムアウト時にここに来る
        return f"Error: {str(e)}"

# --- テスト実行 ---
if __name__ == "__main__":
    c_test_code = """
#include <stdio.h>
int main() {
    int n;
    if(scanf("%d", &n) == 1) {
        printf("%d\\n", n * 2);
    }
    return 0;
}
"""
    print("ジャッジテストを開始します...")
    result = run_code_in_docker('c', c_test_code, "50")
    print(f"C言語の結果：{result}")