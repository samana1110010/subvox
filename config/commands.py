7.
#include <stdio.h>

struct Item {
    int id, w, v;
    float r;
};

int main() {
    int n, c, i, j, rem;
    float fp = 0, used = 0;
    int dp = 0, discW = 0;

    printf("Enter number of products: ");
    scanf("%d", &n);

    struct Item a[n], t;

    printf("Enter weight and value:\n");
    for(i = 0; i < n; i++) {
        a[i].id = i + 1;
        scanf("%d%d", &a[i].w, &a[i].v);
        a[i].r = (float)a[i].v / a[i].w;
    }

    printf("Enter shelf capacity: ");
    scanf("%d", &c);

    for(i = 0; i < n - 1; i++) {
        for(j = i + 1; j < n; j++) {
            if(a[i].r < a[j].r) {
                t = a[i];
                a[i] = a[j];
                a[j] = t;
            }
        }
    }

    printf("\nSorted Items:\n");
    printf("ID\tW\tV\tR\n");

    for(i = 0; i < n; i++) {
        printf("%d\t%d\t%d\t%.2f\n", a[i].id, a[i].w, a[i].v, a[i].r);
    }

    printf("\nFractional Knapsack:\n");
    printf("ID\tFrac\tW_taken\tV_gain\n");

    rem = c;

    for(i = 0; i < n && rem > 0; i++) {
        if(a[i].w <= rem) {
            printf("%d\t1.00\t%d\t%d\n", a[i].id, a[i].w, a[i].v);
            rem -= a[i].w;
            used += a[i].w;
            fp += a[i].v;
        }
        else {
            float f = (float)rem / a[i].w;

            printf("%d\t%.2f\t%.2f\t%.2f\n", a[i].id, f, f * a[i].w, f * a[i].v);

            used += f * a[i].w;
            fp += f * a[i].v;
            rem = 0;
        }
    }

    printf("Shelf used = %.2f/%d\n", used, c);
    printf("Fractional value = %.2f\n", fp);

    printf("\n0/1 Greedy Knapsack:\n");
    printf("ID\tW\tV\n");

    rem = c;

    for(i = 0; i < n && rem > 0; i++) {
        if(a[i].w <= rem) {
            printf("%d\t%d\t%d\n", a[i].id, a[i].w, a[i].v);
            rem -= a[i].w;
            discW += a[i].w;
            dp += a[i].v;
        }
    }

    printf("Shelf used = %d/%d\n", discW, c);
    printf("0/1 greedy value = %d\n", dp);

    printf("\nNote: Fractional greedy is optimal, but 0/1 greedy is only a heuristic.\n");

    return 0;
}



8.
#include <stdio.h>

#define INF 9999
#define MAX 100

int minDistance(int dist[], int visited[], int n) {
    int min = INF, index = -1;

    for(int i = 0; i < n; i++) {
        if(!visited[i] && dist[i] < min) {
            min = dist[i];
            index = i;
        }
    }

    return index;
}

void printPath(int parent[], int v) {
    if(v == -1)
        return;

    printPath(parent, parent[v]);
    printf("%d ", v);
}

int main() {
    int n, src, i, j, u, v;
    int cost[MAX][MAX], dist[MAX], visited[MAX], parent[MAX];

    printf("Enter number of vertices: ");
    scanf("%d", &n);

    printf("Enter adjacency matrix (0 for no edge):\n");
    for(i = 0; i < n; i++) {
        for(j = 0; j < n; j++) {
            scanf("%d", &cost[i][j]);
        }
    }

    printf("Enter source vertex: ");
    scanf("%d", &src);

    for(i = 0; i < n; i++) {
        dist[i] = INF;
        visited[i] = 0;
        parent[i] = -1;
    }

    dist[src] = 0;

    for(i = 0; i < n - 1; i++) {
        u = minDistance(dist, visited, n);

        if(u == -1)
            break;

        visited[u] = 1;

        for(v = 0; v < n; v++) {
            if(!visited[v] && cost[u][v] > 0 && dist[u] + cost[u][v] < dist[v]) {
                dist[v] = dist[u] + cost[u][v];
                parent[v] = u;
            }
        }
    }

    printf("\nShortest Paths from %d:\n", src);
    printf("Vertex\tDistance\tPath\n");

    for(i = 0; i < n; i++) {
        printf("%d\t", i);

        if(dist[i] == INF) {
            printf("INF\t\tNo path\n");
        }
        else {
            printf("%d\t\t", dist[i]);
            printPath(parent, i);
            printf("\n");
        }
    }

    return 0;
}

9b.
#include <stdio.h>

#define MAX 100

int main() {
    int n;
    int reach[MAX][MAX];

    printf("Enter number of webpages (vertices): ");
    scanf("%d", &n);

    printf("Enter adjacency matrix (1 if link exists, else 0):\n");
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            scanf("%d", &reach[i][j]);
        }
    }

    for (int k = 0; k < n; k++) {
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                reach[i][j] = reach[i][j] || (reach[i][k] && reach[k][j]);
            }
        }
    }

    printf("\nReachability Matrix (Transitive Closure):\n");
    printf("1 means reachable, 0 means not reachable\n\n");

    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            printf("%d ", reach[i][j]);
        }
        printf("\n");
    }

    return 0;
}

9a.
#include <stdio.h>

#define MAX 100
#define INF 999999

void printPath(int next[MAX][MAX], int u, int v) {
    if (next[u][v] == -1) {
        printf("No route");
        return;
    }

    printf("%d", u);

    while (u != v) {
        u = next[u][v];
        printf(" -> %d", u);
    }
}

int main() {
    int n;
    int dist[MAX][MAX];
    int next[MAX][MAX];

    printf("Enter number of cities: ");
    scanf("%d", &n);

    printf("Enter travel time matrix:\n");
    printf("Use %d for INF (no direct route), 0 on diagonal.\n", INF);

    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            scanf("%d", &dist[i][j]);

            if (i == j || dist[i][j] == INF) {
                next[i][j] = -1;
            } else {
                next[i][j] = j;
            }
        }
    }

    for (int k = 0; k < n; k++) {
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                if (dist[i][k] != INF && dist[k][j] != INF) {
                    int newDist = dist[i][k] + dist[k][j];

                    if (newDist < dist[i][j]) {
                        dist[i][j] = newDist;
                        next[i][j] = next[i][k];
                    }
                }
            }
        }
    }

    printf("\nAll-Pairs Shortest Travel Time Matrix:\n");

    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            if (dist[i][j] == INF) {
                printf("INF\t");
            } else {
                printf("%d\t", dist[i][j]);
            }
        }
        printf("\n");
    }

    printf("\nShortest Routes Between All City Pairs:\n");

    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            if (i != j) {#include <stdio.h>
#include <stdlib.h>

#define MAX_ITEMS 200

int main() {
    int n, W;
    int wt[MAX_ITEMS], val[MAX_ITEMS];

    printf("Enter number of items: ");
    scanf("%d", &n);

    printf("Enter truck capacity (max weight): ");
    scanf("%d", &W);

    if (n <= 0 || n > MAX_ITEMS || W <= 0) {
        printf("Invalid input.\n");
        return 1;
    }

    printf("Enter weights of items:\n");
    for (int i = 0; i < n; i++) {
        scanf("%d", &wt[i]);
    }

    printf("Enter values of items:\n");
    for (int i = 0; i < n; i++) {
        scanf("%d", &val[i]);
    }

    int *dp = (int *)calloc(W + 1, sizeof(int));

    unsigned char **take = (unsigned char **)malloc((n + 1) * sizeof(unsigned char *));

    for (int i = 0; i <= n; i++) {
        take[i] = (unsigned char *)calloc(W + 1, sizeof(unsigned char));
    }

    for (int i = 1; i <= n; i++) {
        for (int w = W; w >= wt[i - 1]; w--) {
            int newVal = val[i - 1] + dp[w - wt[i - 1]];

            if (newVal > dp[w]) {
                dp[w] = newVal;
                take[i][w] = 1;
            }
        }
    }

    printf("\nMaximum value that can be loaded = %d\n", dp[W]);

    int w = W;
    int totalWeight = 0;
    int totalValue = dp[W];

    printf("\nTruck Load Manifest (Selected items):\n");
    printf("ItemIndex\tWeight\tValue\n");

    for (int i = n; i >= 1; i--) {
        if (take[i][w] == 1) {
            printf("%d\t\t%d\t%d\n", i - 1, wt[i - 1], val[i - 1]);
            totalWeight += wt[i - 1];
            w -= wt[i - 1];
        }
    }

    printf("\nTotal Loaded Weight = %d\n", totalWeight);
    printf("Total Loaded Value = %d\n", totalValue);
    printf("Unused Capacity = %d\n", W - totalWeight);

    for (int i = 0; i <= n; i++) {
        free(take[i]);
    }

    free(take);
    free(dp);

    return 0;
}
                printf("Route %d -> %d : ", i, j);
                printPath(next, i, j);

                if (dist[i][j] == INF) {
                    printf(" | Time: INF\n");
                } else {
                    printf(" | Time: %d\n", dist[i][j]);
                }
            }
        }
    }

    return 0;
}

10.
#include <stdio.h>

int max(int a, int b) {
    return (a > b) ? a : b;
}

int main() {
    int n, W, i, j;

    printf("Enter number of items: ");
    scanf("%d", &n);

    int wt[n], val[n];

    printf("Enter weights:\n");
    for(i = 0; i < n; i++)
        scanf("%d", &wt[i]);

    printf("Enter values:\n");
    for(i = 0; i < n; i++)
        scanf("%d", &val[i]);

    printf("Enter capacity: ");
    scanf("%d", &W);

    int dp[n + 1][W + 1];

    for(i = 0; i <= n; i++) {
        for(j = 0; j <= W; j++) {
            if(i == 0 || j == 0)
                dp[i][j] = 0;

            else if(wt[i - 1] <= j)
                dp[i][j] = max(val[i - 1] + dp[i - 1][j - wt[i - 1]],
                               dp[i - 1][j]);

            else
                dp[i][j] = dp[i - 1][j];
        }
    }

    printf("\nMaximum Profit = %d\n", dp[n][W]);

    printf("\nSelected Items:\n");
    printf("Item\tWeight\tValue\n");

    j = W;

    for(i = n; i > 0; i--) {
        if(dp[i][j] != dp[i - 1][j]) {
            printf("%d\t%d\t%d\n", i, wt[i - 1], val[i - 1]);
            j = j - wt[i - 1];
        }
    }

    return 0;
}

11.
#include <stdio.h>

#define MAX 50

int n, target;
int denom[MAX], count[MAX], used[MAX];

void print() {
    printf("{ ");
    for(int i = 0; i < n; i++) {
        if(used[i] > 0)
            printf("%d x %d  ", denom[i], used[i]);
    }
    printf("}\n");
}

void solve(int i, int sum) {
    if(sum == target) {
        print();
        return;
    }

    if(i == n || sum > target)
        return;

    for(int k = 0; k <= count[i]; k++) {
        used[i] = k;
        solve(i + 1, sum + k * denom[i]);
    }

    used[i] = 0;
}

int main() {
    printf("Enter number of denominations: ");
    scanf("%d", &n);

    printf("Enter denomination and count:\n");
    for(int i = 0; i < n; i++) {
        scanf("%d%d", &denom[i], &count[i]);
        used[i] = 0;
    }

    printf("Enter target amount: ");
    scanf("%d", &target);

    printf("\nPossible combinations:\n");
    solve(0, 0);

    return 0;
}
12.
#include <stdio.h>

int x[20], n, count = 0;

int place(int k, int j) {
    for(int i = 1; i < k; i++) {
        if(x[i] == j)
            return 0;

        if(x[i] - i == j - k)
            return 0;

        if(x[i] + i == j + k)
            return 0;
    }

    return 1;
}

void NQueens(int k) {
    for(int j = 1; j <= n; j++) {
        if(place(k, j)) {
            x[k] = j;

            if(k == n) {
                count++;

                printf("\nSolution %d:\n", count);

                for(int i = 1; i <= n; i++) {
                    for(int j = 1; j <= n; j++) {
                        if(x[i] == j)
                            printf(" Q ");
                        else
                            printf(" . ");
                    }
                    printf("\n");
                }
            }
            else {
                NQueens(k + 1);
            }
        }
    }
}

int main() {
    printf("Enter number of queens: ");
    scanf("%d", &n);

    NQueens(1);

    if(count == 0)
        printf("\nNo solution exists.\n");
    else
        printf("\nTotal solutions = %d\n", count);

    return 0;
}

