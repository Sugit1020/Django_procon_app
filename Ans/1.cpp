#include <iostream>
#include <vector>
#include <random>
#include <fstream>

using namespace std;

int main() {
    // --- 設定 ---
    int N = 200000;
    int K = 100000;
    int max_val = 20000;   // 合計が21億を超えないための上限
    string filename = "int_safe_case.txt";

    random_device seed_gen;
    mt19937 engine(seed_gen());
    
    // 通常の区間は大きめの値 (15000〜20000)
    uniform_int_distribution<int> dist(15000, max_val);
    // 正解にしたい区間は小さめの値 (1〜10000)
    uniform_int_distribution<int> small_dist(1, 10000);

    ofstream ofs(filename);
    
    // 1行目: N K
    ofs << N << " " << K << "\n";

    // 正解の開始位置をランダムに決定 (1-indexedで 1 〜 N-K+1 の間)
    int secret_start = 33333; 

    // 2行目: Ai の生成
    for (int i = 1; i <= N; i++) {
        if (i >= secret_start && i < secret_start + K) {
            ofs << small_dist(engine);
        } else {
            ofs << dist(engine);
        }
        
        if (i == N) ofs << "\n";
        else ofs << " ";
    }

    ofs.close();
    cout << "ファイル '" << filename << "' を作成しました。" << endl;
    cout << "想定される正解の開始位置: " << secret_start << endl;
    cout << "この時の最大合計値は約: " << (long long)max_val * K << " (intに収まります)" << endl;

    return 0;
}