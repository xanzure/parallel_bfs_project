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

    while (!current_frontier.empty()) 
    {
        std::vector<int> next_frontier;
        std::vector<std::vector<int>> local_frontiers(omp_get_max_threads());

        #pragma omp parallel
        {
            int tid = omp_get_thread_num();
            auto& local = local_frontiers[tid];

            #pragma omp for schedule(dynamic)
            for (int i = 0; i < (int)current_frontier.size(); i++) 
            {
                int u = current_frontier[i];

                for (int j = g.row_ptr[u]; j < g.row_ptr[u + 1]; j++) 
                {
                    int v = g.col_idx[j];

                    int expected = -1;
                    if (distance[v].compare_exchange_strong(expected, level + 1)) 
                    {
                        local.push_back(v);
                    }
                }
            }
        }

        int total = 0;
        for (int i = 0; i < (int)local_frontiers.size(); i++) 
        {
            total += local_frontiers[i].size();
        }

        next_frontier.reserve(total);

        for (int i = 0; i < (int)local_frontiers.size(); i++) 
        {
            next_frontier.insert(next_frontier.end(),
                                 local_frontiers[i].begin(),
                                 local_frontiers[i].end());
        }

        level++;
        current_frontier = next_frontier;
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
        std::cerr << "Usage: ./bfs_parallel <graph_file> <undirected_flag>" << std::endl;
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