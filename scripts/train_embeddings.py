"""
scripts/train_embeddings.py
---------------------------
Generates temporal Node2Vec-style embeddings via chronological random walks + Word2Vec.

This script converts the weighted founder multigraph (produced by ``query_graph.py``)
into dense vector representations (embeddings) for each founder node. The procedure:

    1. Load the weighted multigraph from ``data/weighted_graph_{t_anchor}.feather``.
    2. Build a bidirectional adjacency list where each edge carries its timestamp (``t_h``)
       and weight.
    3. Simulate random walks that are forced to advance chronologically through the graph
       (each hop must traverse an edge with ``t_h >= current_time``), ensuring PiT safety.
    4. Train a Word2Vec Skip-Gram model on the resulting corpus of walk sequences.
    5. Save the embedding matrix to ``data/embeddings_{t_anchor}.csv``.

The chronological constraint on walks ensures that the embedding reflects each founder's
network influence *up to* ``t_anchor``, not beyond.

Usage::
    python scripts/train_embeddings.py --t-anchor YYYY-MM-DD [--num-walks 10]
        [--walk-length 20] [--vector-size 64] [--window 5]
"""

import argparse
import os
import pandas as pd
from collections import defaultdict
import random
import numpy as np
from gensim.models import Word2Vec

def load_graph(feather_path):
    """Load a weighted multigraph from a feather file into a bidirectional adjacency list.

    Each directed edge (u -> v) and reverse edge (v -> u) is stored with its
    timestamp ``t_h`` and weight ``w``, enabling chronological walk simulation.

    Args:
        feather_path (str): Path to the ``.feather`` file containing columns
            ``u``, ``v``, ``weight``, and ``t_h``.

    Returns:
        defaultdict: Adjacency list mapping node_id (str) to a list of
            (neighbor_id, t_h, weight) tuples.
    """
    print(f"Loading multigraph from {feather_path}...")
    df = pd.read_feather(feather_path)
    
    adj = defaultdict(list)
    for _, row in df.iterrows():
        u = str(row['u'])
        v = str(row['v'])
        w = float(row['weight'])
        t_h = pd.to_datetime(row['t_h'])
        
        # Treat as bidirectional in the adjacency list
        adj[u].append((v, t_h, w))
        adj[v].append((u, t_h, w))
        
    print(f"Graph loaded. {len(adj)} unique nodes.")
    return adj

def simulate_walks(adj, num_walks=10, walk_length=20):
    """Simulate chronologically-constrained random walks over the founder graph.

    Each walk starts at a random node and proceeds by selecting the next hop from
    neighbors whose edge timestamp ``t_h`` is greater than or equal to the timestamp
    of the most recently traversed edge. This enforces temporal ordering so that the
    resulting sequences capture the *evolution* of each founder's network rather than
    a static snapshot.

    Transition probabilities at each step are proportional to edge weights, so
    higher-quality (longer, less-diluted) co-associations are traversed more often.

    Args:
        adj (defaultdict): Bidirectional adjacency list from ``load_graph``.
        num_walks (int): Number of walk iterations per node. Defaults to 10.
        walk_length (int): Maximum steps per walk. Walks may terminate early if
            no chronologically valid next hop exists. Defaults to 20.

    Returns:
        list[list[str]]: A list of walks, where each walk is a list of node ID strings.
    """
    walks = []
    nodes = list(adj.keys())
    
    print(f"Simulating {num_walks} chronologically routed walks of length {walk_length} per node...")
    
    for i in range(num_walks):
        random.shuffle(nodes)
        for node in nodes:
            walk = [node]
            curr_node = node
            # The earliest possible time for the start of the walk
            curr_time = pd.Timestamp.min
            
            for _ in range(walk_length - 1):
                neighbors = adj[curr_node]
                
                # Filter for strictly chronological forward progression (or identical time)
                valid_edges = [(v, t, w) for (v, t, w) in neighbors if t >= curr_time]
                
                if not valid_edges:
                    # Dead end chronological path, break early and retain what we have
                    break
                    
                # Probabilistic transition based on edge weights
                weights = np.array([w for (_, _, w) in valid_edges])
                total_w = np.sum(weights)
                
                if total_w == 0:
                    probs = np.ones(len(valid_edges)) / len(valid_edges)
                else:
                    probs = weights / total_w
                
                idx = np.random.choice(len(valid_edges), p=probs)
                next_node, next_time, _ = valid_edges[idx]
                
                walk.append(next_node)
                curr_node = next_node
                curr_time = next_time
                
            walks.append(walk)
            
        if (i+1) % 2 == 0:
            print(f"Finished {i+1}/{num_walks} walk iterations.")
            
    return walks

def build_embeddings(t_anchor_str, num_walks, walk_length, vector_size, window):
    """Orchestrate the full embedding pipeline for a given anchor date.

    Loads the weighted graph, simulates chronological random walks, trains a
    Word2Vec Skip-Gram model, and saves the resulting embedding matrix.

    Args:
        t_anchor_str (str): Anchor date in ``YYYY-MM-DD`` format. Used to locate
            the weighted graph file and name the output embedding CSV.
        num_walks (int): Number of walk iterations to simulate per node.
        walk_length (int): Maximum steps per individual walk.
        vector_size (int): Dimensionality of the embedding vectors (default: 64).
        window (int): Word2Vec context window size (default: 5).
    """
    in_path = f"data/weighted_graph_{t_anchor_str}.feather"
    if not os.path.exists(in_path):
        print(f"Graph {in_path} not found! Please run query_graph.py first.")
        return
        
    adj = load_graph(in_path)
    
    walks = simulate_walks(adj, num_walks=num_walks, walk_length=walk_length)
    print(f"Total paths generated: {len(walks)}")
    
    print(f"Training Word2Vec Skip-Gram model (vectors={vector_size}, window={window})...")
    # sg=1 designates skip-gram architecture
    model = Word2Vec(sentences=walks, vector_size=vector_size, window=window, min_count=1, workers=4, sg=1)
    
    out_path = f"data/embeddings_{t_anchor_str}.csv"
    
    # Save the embeddings dictionary mapping node ID -> vector
    word_vectors = model.wv
    vocab = word_vectors.index_to_key
    
    emb_df = pd.DataFrame(word_vectors.vectors, index=vocab)
    emb_df.index.name = "founder_id"
    emb_df.to_csv(out_path)
    
    print(f"Embeddings successfully saved to {out_path}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--t-anchor", type=str, required=True, help="Anchor date YYYY-MM-DD")
    parser.add_argument("--num-walks", type=int, default=10)
    parser.add_argument("--walk-length", type=int, default=20)
    parser.add_argument("--vector-size", type=int, default=64)
    parser.add_argument("--window", type=int, default=5)
    args = parser.parse_args()
    
    build_embeddings(args.t_anchor, args.num_walks, args.walk_length, args.vector_size, args.window)
