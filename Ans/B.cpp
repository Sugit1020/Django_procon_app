#include <iostream>
#include <vector>
using namespace std;
int main(void) {
    int max_num = 0, max_index, k;
    vector<int> a(3);
    for (int i = 0; i < 3; i++)  {
        cin >> a[i];
        if (a[i] > max_num) {
            max_num = a[i];
            max_index = i;
        }
    }
    cin >> k;
    for (int i = 0; i < k; i++) {
        a[max_index] *= 2;
    }
    int sum = 0;
    for (int i = 0; i < 3; i++) {
        sum += a[i];
    } 
    cout << sum << endl;
}