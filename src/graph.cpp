#include <fstream>
#include <iostream>
#include "graph.h"

Graph readGraph(const std::string& filename, bool undirected)
{
    std::ifstream file(filename);
    if (!file) {
        std::cerr << "Error: could not open file " << filename << std::endl;
        exit(1);
    }

    int n, m;
    file >> n >> m;

    std::vector<std::vector<int>> adj(n);

    for (int i = 0; i < m; i++) {
        int u, v;
        file >> u >> v;
        adj[u].push_back(v);
        if (undirected) {
            adj[v].push_back(u);
        }
    }

    std::vector<int> row_ptr(n + 1), col_idx;
    row_ptr[0] = 0;

    for (int i = 0; i < n; i++) {
        row_ptr[i + 1] = row_ptr[i] + adj[i].size();
    }

    for (int i = 0; i < n; i++) {
        for (int j = 0; j < adj[i].size(); j++) {
            col_idx.push_back(adj[i][j]);
        }
    }

    Graph g;
    g.n = n;
    g.m = m;
    g.row_ptr = row_ptr;
    g.col_idx = col_idx;

    return g;
}