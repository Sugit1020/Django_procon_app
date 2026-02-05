#include <iostream>
#include <vector>

using namespace std;

int main() {
    int N, K;
    if (!(cin >> N >> K)) return 0;

    vector<long long> A(N);
    for (int i = 0; i < N; i++) {
        cin >> A[i];
    }

    // 非常に大きな値で初期化
    long long min_sum = -1; 
    int best_start = 1;

    // すべての開始位置 i を試す
    for (int i = 0; i <= N - K; i++) {
        long long current_sum = 0;

        // 【ここが O(K)】 毎回 K 個の要素を愚直に足し合わせる
        for (int j = 0; j < K; j++) {
            current_sum += A[i + j];
        }

        // 初回、または今の合計が最小値を下回ったら更新
        if (min_sum == -1 || current_sum < min_sum) {
            min_sum = current_sum;
            best_start = i + 1; // 1-indexed
        }
    }

    // 結果出力
    cout << best_start << " " << best_start + K - 1 << endl;

    return 0;
}