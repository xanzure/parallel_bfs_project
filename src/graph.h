#ifndef GRAPH_H
#define GRAPH_H

#include <vector>
#include <string>

struct Graph {
    int n;                      // number of vertices
    int m;                      // number of edges
    std::vector<int> row_ptr;   // CSR row pointers
    std::vector<int> col_idx;   // CSR column indices
};

Graph readGraph(const std::string& filename, bool undirected = true);

#endif