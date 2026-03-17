/*
	Task	: sol_dfs
	Author	: Phumipat C. [MAGCARI]
	Language: C++
	Created	: 20 March 2024 [23:00]
	Algo	: 
	Status	: 
*/
#include<bits/stdc++.h>
#define rep(i, a, b) for(int i = a; i <= (b); ++i)
#define repr(i, a, b) for(int i = a; i >= (b); --i)
#define repl(i, a, b) for(LL i = a; i <= (b); ++i)
#define reprl(i, a, b) for(LL i = a; i >= (b); --i)
#define all(x) begin(x),end(x)
#define allst(x,y) (x).begin()+y,(x).end()
#define rmdup(x) sort(all(x)),(x).resize(unique((x).begin(),(x).end())-(x).begin())
#define sz(x) (int)(x).size()
#define decp(x) fixed << setprecision(x)
#define MOD (LL )(1e9+7)
using namespace std;
using LL = long long;
using PII = pair<int ,int >;
using PLL = pair<long long ,long long >;
const int dir4[2][4] = {{1,-1,0,0},{0,0,1,-1}};
const int dir8[2][8] = {{-1,-1,-1,0,1,1,1,0},{-1,0,1,1,-1,0,1,-1}};
LL modN(LL a,LL b,LL c = MOD){
	if(b == 0)	return 1;
	if(b == 1)	return a%c;
	LL now = modN(a,b/2,c);
	if(b&1)	return (((now*now)%c)*(a%c))%c;
	else	return (now*now)%c;
}
const int N = 710;
int world[2][N][N], areaInSouth[N][N];
bool worm[N][N];
int R,C;
map<int ,int > markingCnt;
int bfsInSouth(int marking, int i,int j) {
	if(areaInSouth[i][j])
		return markingCnt[areaInSouth[i][j]];
	
	queue<pair<int ,int > > que;
	int cnt = 0;

	if(!world[1][i][j]){
		que.push({i,j});
		cnt++;
		areaInSouth[i][j] = marking;
	}

	while(!que.empty()) {
		auto now = que.front();
		que.pop();

		rep(k,0,3){
			int ni = now.first + dir4[0][k];
			int nj = now.second + dir4[1][k];
			if(ni < 1 || nj < 1 || ni > R || nj > C)
				continue;
			if(world[1][ni][nj])
				continue;
			if(areaInSouth[ni][nj])
				continue;

			que.push({ni,nj});
			cnt++;
			areaInSouth[ni][nj] = marking;
		}
	}
	return markingCnt[marking] = cnt;
}
int bfsInNorth(int i,int j) {
	queue<pair<int ,int > > que;
	int cnt = 0;
	if(!world[0][i][j]){
		que.push({i,j});
		cnt++;
		world[0][i][j] = 2;
	}
	
	while(!que.empty()) {
		auto now = que.front();
		que.pop();

		rep(k,0,3) {
			int ni = now.first + dir4[0][k];
			int nj = now.second + dir4[1][k];
			if(ni < 1 || nj < 1 || ni > R || nj > C)
				continue;
			if(world[0][ni][nj])
				continue;
			que.push({ni,nj});
			cnt++;
			world[0][ni][nj] = 2;
		}
	}
	int maxFromSouth = 0;
	rep(i,1,R)
		rep(j,1,C)
			if(world[0][i][j] == 2 && worm[i][j])
				maxFromSouth = max(maxFromSouth, markingCnt[areaInSouth[i][j]]);
	return cnt + maxFromSouth;
}

void init(){
	
}
void solve(){
	int K;
	cin >> R >> C >> K;
	rep(i,1,R)
		rep(j,1,C)
			cin >> world[0][i][j];
	rep(i,1,R)
		rep(j,1,C)
			cin >> world[1][i][j];
	rep(k,1,K){
		int a,b;
		cin >> a >> b;
		worm[a][b] = true;
		int maxCnt = bfsInSouth(-k,a,b);
	}

	cout << bfsInNorth(1,1);
}
int main(){
	cin.tie(0)->sync_with_stdio(0);
	cin.exceptions(cin.failbit);
	// freopen("d:/Code/C_Programming/input.in","r",stdin);
	init();
	int q = 1;
	// cin >> q;
	for(int Q=1;Q<=q;Q++){
		// cout << "Case #" << Q << ": ";
		solve();
	}
	return 0;
}