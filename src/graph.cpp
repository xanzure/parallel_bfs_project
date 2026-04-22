#include <fstream>
#include <iostream>
#include <vector>
#include <stdexcept>
#include <algorithm>
#include "graph.h"

Graph readGraph(const std::string& filename, bool undirected)
{
    std::ifstream file(filename);
    if (!file) {
        throw std::runtime_error("Error: could not open file " + filename);
    }

    int n_header, m;
    file >> n_header >> m;
    if (!file || m < 0) {
        throw std::runtime_error("Error: invalid graph header in " + filename);
    }

    std::vector<std::pair<int,int>> edges;
    edges.reserve(m);

    int max_node = -1;

    for (int i = 0; i < m; i++) {
        int u, v;
        if (!(file >> u >> v)) {
            throw std::runtime_error("Error: failed reading edge " + std::to_string(i));
        }
        if (u < 0 || v < 0) {
            throw std::runtime_error("Error: negative node id in " + filename);
        }

        edges.push_back({u, v});
        max_node = std::max(max_node, std::max(u, v));
    }

    int n = max_node + 1;

    std::vector<int> degree(n, 0);
    for (const auto& [u, v] : edges) {
        degree[u]++;
        if (undirected) degree[v]++;
    }

    std::vector<int> row_ptr(n + 1, 0);
    for (int i = 0; i < n; i++) {
        row_ptr[i + 1] = row_ptr[i] + degree[i];
    }

    std::vector<int> col_idx(row_ptr[n]);
    std::vector<int> next_pos = row_ptr;

    for (const auto& [u, v] : edges) {
        col_idx[next_pos[u]++] = v;
        if (undirected) {
            col_idx[next_pos[v]++] = u;
        }
    }

    Graph g;
    g.n = n;
    g.m = static_cast<int>(col_idx.size());
    g.row_ptr = std::move(row_ptr);
    g.col_idx = std::move(col_idx);
    return g;
}