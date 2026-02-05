#pragma region template
#include <iostream>
#include <bits/stdc++.h>

#define rep(i,n) for (int i = 0; i < (n); i++)
#define rep2(i,a,n) for (int i = (a); i < (n); i++)
#define cout(a) cout << a << endl
#define INF 2e9
typedef long long ll;
using namespace std;

template<class T>
void print2d(const vector<vector<T>> &a) {
    for (auto &r : a) {
        for (auto &x : r) cout << x << " ";
        cout << "\n";
    }
}

template<class T>
void printv(const vector<T> &a) {
    for (auto &x : a) {
        cout << x << " ";
    }
    cout << endl;
}
#pragma endregion

int main(void) {
    int n, k; cin >> n >> k;
    int first, last;
    vector<int> a;
    a.push_back(0);
    for (int i = 1; i <= n; i++) {
        int x; cin >> x;
        a.push_back(a.back() + x);
    }
    int min_area = 2e9;
    for (int i = 0; i + k <= n; i++) {
        if (a[i + k] - a[i] < min_area) {
            min_area = a[i + k] - a[i];
            first = i + 1;
            last = i + k;
        }
    }
    cout << first << " " << last << endl;
    return 0;
}