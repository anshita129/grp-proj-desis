#include <bits/stdc++.h>
using namespace std;
#define int long long int
#define ll long long int
#define lld long double
#define ull unsigned long long int
#define vi vector<int>
#define vvi vector<vector<int>>
#define vpii vector<pair<int,int>>
#define pb push_back
#define read(a, n)               \
    for (int i = 0; i < n; ++i)    \
        cin >> a[i];
#define print(a, n)              \
    for (int i = 0; i < n; ++i)    \
        if (i == n - 1)               \
        {                             \
            cout << a[i] << endl;       \
        }                             \
        else                          \
        {                             \
            cout << a[i] << ' ';        \
        }
#define read_matrix(a,n,m) \
for(ll i = 0 ; i < n ; i++) \
    for(ll j = 0 ; j < m ; j++) \
        cin >> a[i][j];
#define deb(x) cout << #x << '=' << x << endl
#define no cout<<"NO"<<endl
#define yes cout<<"YES"<<endl
#define trav(it, x) for (auto it = x.begin(); it != x.end(); it++)
#define f(a, start, end) for (int a = start; a < end; a++)
#define fi(a, start, end, inc) for (int a = start; a < end; a += inc)
#define all(x) x.begin(), x.end()
#define sortall(x) sort(all(x))
#define pb push_back
#define F first
#define S second
#define mp make_pair
const int MOD =1e9+7;
#define PI 3.141592653589793238
#define put(x) cout << x << endl
#define INF 1e18

int bintodec(int n, vi &a)
{
    int res = 0;
    int p = 1;
    for (int i = n - 1; i >= 0; i--)
    {
        res = res + (a[i] * p);
        p = p * 2;
    }
    return res;
}
void dectobin(int n, vi &a, int num)
{
    int i = (n - 1);
    while (num)
    {
        a[i] = num % 2;
        num = num / 2;
        i--;
    }
    return;
}
int binaryexp(int a, int b)
{
    int ans = 1;
    while (b)
    {
        if (b % 2 == 1)
            ans = (ans * a);
        b = b / 2;
        a = (a * a);
    }
    return ans;
}
int modularbinaryexp(int a, int b)
{
    int ans = 1;
    while (b)
    {
        if (b % 2 == 1)
            ans = (ans * a) % MOD;
        b = b / 2;
        a = (a * a) % MOD;
    }
    return ans;
}
int modInverse(int A, int M){
    return modularbinaryexp(A, M - 2);
}

vi removeDuplicates(const vi& v){
    unordered_set<int> seen;
    vi res;
    for(int x : v){
        if(!seen.count(x)){
            seen.insert(x);
            res.pb(x);
        }
    }
    return res;
}

map<int,int> freq(vector<int>&a){
    map<int,int> mp;
    for(auto &x:a) mp[x]++;
    return mp;
}

int mex(vector<int>& a) {
    unordered_set<int> s(a.begin(), a.end());
    int x = 0;
    while (s.count(x)) x++;
    return x;
}

void solve()
{
    int n,h,l;
    cin>>n>>h>>l;
    vi a(n);
    read(a,n);
    if(h>l) swap(h,l);
    int ch=0;
    int cl=0;
    f(i,0,n){
        if(a[i]<=l) cl++;
        if(a[i]<=h) ch++;
    }
    if(ch<=cl/2) cout<<ch;
    else cout<<cl/2;
    cout<<"\n";
}

int32_t main()
{
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    cout.tie(NULL);
    int t = 1;
    cin >> t;
    while (t--)
    {
        solve();
    }
    return 0;
}