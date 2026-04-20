#include <fstream>
#include <iostream>
#include <queue>
#include <vector>
#include "graph.h"

std::vector<int> bfs(const Graph& g, int source)
{
    std::vector<bool> visited(g.n, false);
    std::vector<int> distance(g.n, -1);
    std::queue<int> q;

    visited[source] = true;
    distance[source] = 0;
    q.push(source);

    while (!q.empty()) 
    {
        int u = q.front();
        q.pop();

        for (int i = g.row_ptr[u]; i < g.row_ptr[u + 1]; i++) 
        {
            int v = g.col_idx[i];
            if (!visited[v]) 
            {
                visited[v] = true;
                distance[v] = distance[u] + 1;
                q.push(v);
            }
        }
    }

    return distance;
}

int main(int argc, char* argv[])
{
    if (argc != 3) 
    {
        std::cerr << "Usage: ./bfs_seq <graph_file> <undirected_flag>" << std::endl;
        return 1;
    }

    bool undirected = std::stoi(argv[2])==1;

    Graph g = readGraph(argv[1], undirected);
    std::vector<int> result = bfs(g, 0);

    int checksum = 0;
    for (int i = 0; i < g.n; i++) 
    {
        if (result[i] != -1) 
        {
            checksum += result[i];
        }
    }

    std::cout << checksum << std::endl;
    return 0;
}