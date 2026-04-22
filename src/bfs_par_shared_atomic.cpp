#include <iostream>
#include <vector>
#include <atomic>
#include <omp.h>
#include "graph.h"

std::vector<int> bfs_parallel(const Graph& g, int source)
{
    std::vector<std::atomic<int>> distance(g.n);
    for (int i = 0; i < g.n; i++) 
    {
        distance[i].store(-1);
    }
    distance[source].store(0);

    std::vector<int> current_frontier;
    current_frontier.push_back(source);

    int level = 0;
    std::vector<int> next_frontier(g.n);
    std::atomic<int> next_size;

    while (!current_frontier.empty()) 
    {
        next_size.store(0);

        #pragma omp parallel
        {
            #pragma omp for schedule(static)
            for (int i = 0; i < (int)current_frontier.size(); i++) 
            {
                int u = current_frontier[i];

                for (int j = g.row_ptr[u]; j < g.row_ptr[u + 1]; j++) 
                {
                    int v = g.col_idx[j];

                    int expected = -1;
                    if (distance[v].compare_exchange_strong(expected, level + 1)) 
                    {
                        int pos = next_size.fetch_add(1);
                        next_frontier[pos] = v;
                    }
                }
            }
        }

        int total = next_size.load();
        current_frontier.assign(next_frontier.begin(), next_frontier.begin() + total);
        level++;
    }

    std::vector<int> result(g.n);
    for (int i = 0; i < g.n; i++) 
    {
        result[i] = distance[i].load();
    }

    return result;
}

int main(int argc, char* argv[])
{
    if (argc != 3) 
    {
        std::cerr << "Usage: ./bfs_par_shared_atomic <graph_file> <undirected_flag>" << std::endl;
        return 1;
    }

    bool undirected = std::stoi(argv[2]) == 1;

    Graph g = readGraph(argv[1], undirected);
    std::vector<int> result = bfs_parallel(g, 0);

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