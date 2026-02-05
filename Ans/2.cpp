#include <iostream>
#include <vector>
#include <string>
using namespace std;

int main() {
    vector<char> stack;
    string s; cin >> s;

    for (char c : s) {
        if (c == '0') stack.push_back('0');
        else if (c == '1') stack.push_back('1');
        else if (c == 'B' && !stack.empty()) stack.pop_back();
    }

    for (char c : stack) {
        std::cout << c;
    }
    std::cout << std::endl;

    return 0;
}