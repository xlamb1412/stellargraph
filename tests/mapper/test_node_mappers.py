# -*- coding: utf-8 -*-
#
# Copyright 2018 Data61, CSIRO
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""
Mapper tests:

"""
from stellargraph.core.graph import *
from stellargraph.mapper.node_mappers import *

import networkx as nx
import numpy as np
import random
import pytest
import pandas as pd
import scipy.sparse as sps


def example_graph_1(feature_size=None):
    G = nx.Graph()
    elist = [(1, 2), (2, 3), (1, 4), (3, 2)]
    G.add_nodes_from([1, 2, 3, 4], label="default")
    G.add_edges_from(elist, label="default")

    # Add example features
    if feature_size is not None:
        for v in G.nodes():
            G.node[v]["feature"] = np.ones(feature_size)
        return StellarGraph(G, node_features="feature")

    else:
        return StellarGraph(G)


def example_graph_2(feature_size=None):
    G = nx.Graph()
    elist = [(1, 2), (1, 3), (1, 4), (3, 2), (3, 5)]
    G.add_nodes_from([1, 2, 3, 4, 5], label="default")
    G.add_edges_from(elist, label="default")

    # Add example features
    if feature_size is not None:
        for v in G.nodes():
            G.node[v]["feature"] = int(v) * np.ones(feature_size, dtype="int")
        return StellarGraph(G, node_features="feature")

    else:
        return StellarGraph(G)


def example_graph_3(feature_size=None, n_edges=20, n_nodes=6, n_isolates=1):
    G = nx.Graph()
    n_noniso = n_nodes - n_isolates
    edges = [
        (random.randint(0, n_noniso - 1), random.randint(0, n_noniso - 1))
        for _ in range(n_edges)
    ]
    G.add_nodes_from(range(n_nodes))
    G.add_edges_from(edges, label="default")

    # Add example features
    if feature_size is not None:
        for v in G.nodes():
            G.node[v]["feature"] = int(v) * np.ones(feature_size, dtype="int")
        return StellarGraph(G, node_features="feature")

    else:
        return StellarGraph(G)


def example_digraph_2(feature_size=None):
    G = nx.DiGraph()
    elist = [(1, 2), (2, 3), (1, 4), (3, 2)]
    G.add_edges_from(elist)

    # Add example features
    if feature_size is not None:
        for v in G.nodes():
            G.node[v]["feature"] = np.ones(feature_size)
        return StellarDiGraph(G, node_features="feature")

    else:
        return StellarDiGraph(G)


def example_hin_1(feature_size_by_type=None):
    G = nx.Graph()
    G.add_nodes_from([0, 1, 2, 3], label="A")
    G.add_nodes_from([4, 5, 6], label="B")
    G.add_edges_from([(0, 4), (1, 4), (1, 5), (2, 4), (3, 5)], label="R")
    G.add_edges_from([(4, 5)], label="F")

    # Add example features
    if feature_size_by_type is not None:
        for v, vdata in G.nodes(data=True):
            nt = vdata["label"]
            vdata["feature"] = int(v) * np.ones(feature_size_by_type[nt], dtype="int")
        return StellarGraph(G, node_features="feature")

    else:
        return StellarGraph(G)


def example_hin_2(feature_size_by_type=None):
    nodes_type_1 = [0, 1, 2, 3]
    nodes_type_2 = [4, 5]

    # Create isolated graphs
    G = nx.Graph()
    G.add_nodes_from(nodes_type_1, label="t1")
    G.add_nodes_from(nodes_type_2, label="t2")
    G.add_edges_from([(0, 4), (1, 4), (2, 5), (3, 5)], label="e1")

    # Add example features
    if feature_size_by_type is not None:
        for v, vdata in G.nodes(data=True):
            nt = vdata["label"]
            vdata["feature"] = int(v) * np.ones(feature_size_by_type[nt], dtype="int")

        G = StellarGraph(G, node_features="feature")

    else:
        G = StellarGraph(G)

    return G, nodes_type_1, nodes_type_2


def example_hin_3(feature_size_by_type=None):
    nodes_type_1 = [0, 1, 2]
    nodes_type_2 = [4, 5, 6]

    # Create isolated graphs
    G = nx.Graph()
    G.add_nodes_from(nodes_type_1, label="t1")
    G.add_nodes_from(nodes_type_2, label="t2")
    G.add_edges_from([(0, 4), (1, 5)], label="e1")
    G.add_edges_from([(0, 2)], label="e2")

    # Node 2 has no edges of type 1
    # Node 1 has no edges of type 2
    # Node 6 has no edges

    # Add example features
    if feature_size_by_type is not None:
        for v, vdata in G.nodes(data=True):
            nt = vdata["label"]
            vdata["feature"] = (int(v) + 10) * np.ones(
                feature_size_by_type[nt], dtype="int"
            )

        G = StellarGraph(G, node_features="feature")

    else:
        G = StellarGraph(G)

    return G, nodes_type_1, nodes_type_2


def test_nodemapper_constructor_nx():
    """
    GraphSAGENodeGenerator requires a StellarGraph object
    """
    G = nx.Graph()
    G.add_nodes_from(range(4))

    with pytest.raises(TypeError):
        GraphSAGENodeGenerator(G, batch_size=2, num_samples=[2, 2])


def test_nodemapper_constructor_no_feats():
    """
    GraphSAGENodeGenerator requires the graph to have features
    """
    n_feat = 4

    G = example_graph_1()
    with pytest.raises(RuntimeError):
        GraphSAGENodeGenerator(G, batch_size=2, num_samples=[2, 2])


def test_nodemapper_constructor():
    n_feat = 4

    G = example_graph_1(feature_size=n_feat)

    generator = GraphSAGENodeGenerator(G, batch_size=2, num_samples=[2, 2])

    mapper = generator.flow(list(G))

    assert generator.batch_size == 2
    assert mapper.data_size == 4
    assert len(mapper.ids) == 4


def test_nodemapper_1():
    n_feat = 4
    n_batch = 2

    # test graph
    G1 = example_graph_1(n_feat)

    mapper1 = GraphSAGENodeGenerator(G1, batch_size=n_batch, num_samples=[2, 2]).flow(
        G1.nodes()
    )
    assert len(mapper1) == 2

    G2 = example_graph_2(n_feat)

    mapper2 = GraphSAGENodeGenerator(G2, batch_size=n_batch, num_samples=[2, 2]).flow(
        G2.nodes()
    )
    assert len(mapper2) == 3

    for mapper in [mapper1, mapper2]:
        for ii in range(2):
            nf, nl = mapper[ii]
            assert len(nf) == 3
            assert nf[0].shape == (n_batch, 1, n_feat)
            assert nf[1].shape == (n_batch, 2, n_feat)
            assert nf[2].shape == (n_batch, 2 * 2, n_feat)
            assert nl is None

    # Check beyond the graph lengh
    with pytest.raises(IndexError):
        nf, nl = mapper1[len(mapper1)]

    # Check the last batch
    nf, nl = mapper2[len(mapper2) - 1]
    assert nf[0].shape == (1, 1, n_feat)
    assert nf[1].shape == (1, 2, n_feat)
    assert nf[2].shape == (1, 2 * 2, n_feat)

    # This will fail as the nodes are not in the graph
    with pytest.raises(KeyError):
        GraphSAGENodeGenerator(G1, batch_size=2, num_samples=[2, 2]).flow(["A", "B"])


def test_nodemapper_shuffle():
    n_feat = 1
    n_batch = 2

    G = example_graph_2(feature_size=n_feat)
    nodes = list(G.nodes())

    # With shuffle
    random.seed(15)
    mapper = GraphSAGENodeGenerator(G, batch_size=n_batch, num_samples=[0]).flow(
        nodes, nodes, shuffle=True
    )

    expected_node_batches = [[5, 4], [3, 1], [2]]
    assert len(mapper) == 3
    for ii in range(len(mapper)):
        nf, nl = mapper[ii]
        assert all(np.ravel(nf[0]) == expected_node_batches[ii])
        assert all(np.array(nl) == expected_node_batches[ii])

    # This should re-shuffle the IDs
    mapper.on_epoch_end()
    expected_node_batches = [[4, 3], [1, 5], [2]]
    assert len(mapper) == 3
    for ii in range(len(mapper)):
        nf, nl = mapper[ii]
        assert all(np.ravel(nf[0]) == expected_node_batches[ii])
        assert all(np.array(nl) == expected_node_batches[ii])

    # With no shuffle
    mapper = GraphSAGENodeGenerator(G, batch_size=n_batch, num_samples=[0]).flow(
        nodes, nodes, shuffle=False
    )
    expected_node_batches = [[1, 2], [3, 4], [5]]
    assert len(mapper) == 3
    for ii in range(len(mapper)):
        nf, nl = mapper[ii]
        assert all(np.ravel(nf[0]) == expected_node_batches[ii])
        assert all(np.array(nl) == expected_node_batches[ii])


def test_nodemapper_with_labels():
    n_feat = 4
    n_batch = 2

    # test graph
    G2 = example_graph_2(n_feat)
    nodes = list(G2)
    labels = [n * 2 for n in nodes]

    gen = GraphSAGENodeGenerator(G2, batch_size=n_batch, num_samples=[2, 2]).flow(
        nodes, labels
    )
    assert len(gen) == 3

    for ii in range(3):
        nf, nl = gen[ii]

        # Check sizes - note batch sizes are (2,2,1) for each iteration
        assert len(nf) == 3
        assert nf[0].shape[1:] == (1, n_feat)
        assert nf[1].shape[1:] == (2, n_feat)
        assert nf[2].shape[1:] == (2 * 2, n_feat)

        # Check labels
        assert all(int(a) == int(2 * b) for a, b in zip(nl, nf[0][:, 0, 0]))

    # Check beyond the graph lengh
    with pytest.raises(IndexError):
        nf, nl = gen[len(gen)]


def test_nodemapper_zero_samples():
    n_feat = 4
    n_batch = 2

    # test graph
    G = example_graph_1(feature_size=n_feat)
    mapper = GraphSAGENodeGenerator(G, batch_size=n_batch, num_samples=[0]).flow(
        G.nodes()
    )

    # This is an edge case, are we sure we want this behaviour?
    assert len(mapper) == 2
    for ii in range(len(mapper)):
        nf, nl = mapper[ii]
        assert len(nf) == 2
        assert nf[0].shape == (n_batch, 1, n_feat)
        assert nf[1].shape == (n_batch, 0, n_feat)
        assert nl is None

    # test graph
    G = example_graph_1(feature_size=n_feat)
    mapper = GraphSAGENodeGenerator(G, batch_size=n_batch, num_samples=[0, 0]).flow(
        G.nodes()
    )

    # This is an edge case, are we sure we want this behaviour?
    assert len(mapper) == 2
    for ii in range(len(mapper)):
        nf, nl = mapper[ii]
        assert len(nf) == 3
        assert nf[0].shape == (n_batch, 1, n_feat)
        assert nf[1].shape == (n_batch, 0, n_feat)
        assert nf[1].shape == (n_batch, 0, n_feat)
        assert nl is None


def test_nodemapper_isolated_nodes():
    n_feat = 4
    n_batch = 2

    # test graph
    G = example_graph_3(feature_size=n_feat, n_nodes=6, n_isolates=1, n_edges=20)

    # Check connectedness
    ccs = list(nx.connected_components(G))
    assert len(ccs) == 2

    n_isolates = [5]
    assert nx.degree(G, n_isolates[0]) == 0

    # Check both isolated and non-isolated nodes have same sampled feature shape
    for head_nodes in [[1], [2], n_isolates]:
        mapper = GraphSAGENodeGenerator(G, batch_size=n_batch, num_samples=[2, 2]).flow(
            head_nodes
        )
        nf, nl = mapper[0]
        assert nf[0].shape == (1, 1, n_feat)
        assert nf[1].shape == (1, 2, n_feat)
        assert nf[2].shape == (1, 4, n_feat)

    # One isolate and one non-isolate
    mapper = GraphSAGENodeGenerator(G, batch_size=n_batch, num_samples=[2, 2]).flow(
        [1, 5]
    )
    nf, nl = mapper[0]
    assert nf[0].shape == (2, 1, n_feat)
    assert nf[1].shape == (2, 2, n_feat)
    assert nf[2].shape == (2, 4, n_feat)

    # Isolated nodes have the "dummy node" as neighbours
    # Currently, the dummy node has zeros for features – this could change
    assert pytest.approx(nf[1][1]) == 0
    assert pytest.approx(nf[2][2:]) == 0


def test_nodemapper_manual_schema():
    """
    Tests checks on head nodes
    """
    n_feat = 4
    n_batch = 2

    # test graph
    G = example_graph_1(feature_size=n_feat)

    # Create manual schema
    schema = G.create_graph_schema(create_type_maps=True)
    GraphSAGENodeGenerator(G, schema=schema, batch_size=n_batch, num_samples=[1]).flow(
        list(G)
    )

    # Create manual schema without type maps
    # Currently this raises an error:
    schema = G.create_graph_schema(create_type_maps=False)
    with pytest.raises(RuntimeError):
        GraphSAGENodeGenerator(
            G, schema=schema, batch_size=n_batch, num_samples=[1]
        ).flow(list(G))


def test_nodemapper_incorrect_targets():
    """
    Tests checks on target shape
    """
    n_feat = 4
    n_batch = 2

    # test graph
    G = example_graph_1(feature_size=n_feat)

    with pytest.raises(TypeError):
        GraphSAGENodeGenerator(G, batch_size=n_batch, num_samples=[0]).flow(list(G), 1)

    with pytest.raises(ValueError):
        GraphSAGENodeGenerator(G, batch_size=n_batch, num_samples=[0]).flow(
            list(G), targets=[]
        )


def test_hinnodemapper_constructor():
    feature_sizes = {"A": 10, "B": 10}
    G = example_hin_1(feature_sizes)

    # Should fail when head nodes are of different type
    with pytest.raises(ValueError):
        HinSAGENodeGenerator(G, batch_size=2, num_samples=[2, 2]).flow(G.nodes())

    gen = HinSAGENodeGenerator(G, batch_size=2, num_samples=[2, 2])
    mapper = gen.flow([0, 1, 2, 3])
    assert gen.batch_size == 2
    assert mapper.data_size == 4
    assert len(mapper.ids) == 4


def test_hinnodemapper_constructor_all_options():
    feature_sizes = {"A": 10, "B": 10}
    G = example_hin_1(feature_sizes)

    gen = HinSAGENodeGenerator(G, batch_size=2, num_samples=[2, 2])

    nodes_of_type_a = G.nodes_of_type("A")
    mapper = gen.flow(nodes_of_type_a)
    assert gen.batch_size == 2
    assert mapper.data_size == len(nodes_of_type_a)


def test_hinnodemapper_constructor_no_features():
    G = example_hin_1(feature_size_by_type=None)
    with pytest.raises(RuntimeError):
        mapper = HinSAGENodeGenerator(G, batch_size=2, num_samples=[2, 2]).flow(
            G.nodes()
        )


def test_hinnodemapper_constructor_nx_graph():
    G = nx.Graph()
    with pytest.raises(TypeError):
        HinSAGENodeGenerator(G, batch_size=2, num_samples=[2, 2])

    with pytest.raises(TypeError):
        HinSAGENodeGenerator(None, batch_size=2, num_samples=[2, 2])


def test_hinnodemapper_level_1():
    batch_size = 2
    feature_sizes = {"t1": 1, "t2": 2}
    G, nodes_type_1, nodes_type_2 = example_hin_2(feature_sizes)

    mapper = HinSAGENodeGenerator(G, batch_size=batch_size, num_samples=[2]).flow(
        nodes_type_2
    )

    schema = G.create_graph_schema()
    sampling_adj = schema.type_adjacency_list(["t2"], 1)

    assert len(mapper) == 1

    # Get a batch!
    batch_feats, batch_targets = mapper[0]

    # Check shapes are (batch_size, nsamples, feature_size)
    assert np.shape(batch_feats[0]) == (2, 1, 2)
    assert np.shape(batch_feats[1]) == (2, 2, 1)

    # Check the types
    assert np.all(batch_feats[0] >= 4)
    assert np.all(batch_feats[1] < 4)


def test_hinnodemapper_level_2():
    batch_size = 2
    feature_sizes = {"t1": 1, "t2": 2}
    G, nodes_type_1, nodes_type_2 = example_hin_2(feature_sizes)

    mapper = HinSAGENodeGenerator(G, batch_size=batch_size, num_samples=[2, 3]).flow(
        nodes_type_2
    )

    schema = G.create_graph_schema()
    sampling_adj = schema.type_adjacency_list(["t2"], 2)

    assert len(mapper) == 1

    # Get a batch!
    batch_feats, batch_targets = mapper[0]

    # Check types match adjacency list
    assert len(batch_feats) == len(sampling_adj)
    for bf, adj in zip(batch_feats, sampling_adj):
        nt = adj[0]
        assert bf.shape[0] == batch_size
        assert bf.shape[2] == feature_sizes[nt]

        batch_node_types = {schema.get_node_type(n) for n in np.ravel(bf)}

        assert len(batch_node_types) == 1
        assert nt in batch_node_types


def test_hinnodemapper_shuffle():
    random.seed(10)

    batch_size = 2
    feature_sizes = {"t1": 1, "t2": 4}
    G, nodes_type_1, nodes_type_2 = example_hin_2(feature_sizes)

    mapper = HinSAGENodeGenerator(G, batch_size=batch_size, num_samples=[0]).flow(
        nodes_type_1, nodes_type_1, shuffle=True
    )

    expected_node_batches = [[3, 2], [1, 0]]
    assert len(mapper) == 2
    for ii in range(len(mapper)):
        nf, nl = mapper[ii]
        assert all(np.ravel(nf[0]) == expected_node_batches[ii])
        assert all(np.array(nl) == expected_node_batches[ii])

    # This should re-shuffle the IDs
    mapper.on_epoch_end()
    expected_node_batches = [[2, 1], [3, 0]]
    assert len(mapper) == 2
    for ii in range(len(mapper)):
        nf, nl = mapper[ii]
        assert all(np.ravel(nf[0]) == expected_node_batches[ii])
        assert all(np.array(nl) == expected_node_batches[ii])

    # With no shuffle
    mapper = HinSAGENodeGenerator(G, batch_size=batch_size, num_samples=[0]).flow(
        nodes_type_1, nodes_type_1, shuffle=False
    )
    expected_node_batches = [[0, 1], [2, 3]]
    assert len(mapper) == 2
    for ii in range(len(mapper)):
        nf, nl = mapper[ii]
        assert all(np.ravel(nf[0]) == expected_node_batches[ii])
        assert all(np.array(nl) == expected_node_batches[ii])


def test_hinnodemapper_with_labels():
    batch_size = 2
    feature_sizes = {"t1": 1, "t2": 2}
    G, nodes_type_1, nodes_type_2 = example_hin_2(feature_sizes)

    labels = [n * 2 for n in nodes_type_1]

    gen = HinSAGENodeGenerator(G, batch_size=batch_size, num_samples=[2, 3]).flow(
        nodes_type_1, labels, shuffle=False
    )
    assert len(gen) == 2

    for ii in range(2):
        nf, nl = gen[ii]

        # Check sizes of neighbours and features (in bipartite graph)
        assert len(nf) == 3
        assert nf[0].shape == (2, 1, 1)
        assert nf[1].shape == (2, 2, 2)
        assert nf[2].shape == (2, 2 * 3, 1)

        # Check labels
        assert all(int(a) == int(2 * b) for a, b in zip(nl, nf[0][:, 0, 0]))

    # Check beyond the graph lengh
    with pytest.raises(IndexError):
        nf, nl = gen[len(gen)]


def test_hinnodemapper_manual_schema():
    """
    Tests checks on head nodes
    """
    n_batch = 2
    feature_sizes = {"t1": 1, "t2": 2}
    G, nodes_type_1, nodes_type_2 = example_hin_2(feature_sizes)

    # Create manual schema
    schema = G.create_graph_schema(create_type_maps=True)
    HinSAGENodeGenerator(G, schema=schema, batch_size=n_batch, num_samples=[1]).flow(
        nodes_type_1
    )

    # Create manual schema without type maps
    # Currently this raises an error
    schema = G.create_graph_schema(create_type_maps=False)
    with pytest.raises(RuntimeError):
        HinSAGENodeGenerator(
            G, schema=schema, batch_size=n_batch, num_samples=[1]
        ).flow(nodes_type_1)


def test_hinnodemapper_zero_samples():
    batch_size = 3
    feature_sizes = {"t1": 1, "t2": 1}
    G, nodes_type_1, nodes_type_2 = example_hin_3(feature_sizes)

    mapper = HinSAGENodeGenerator(G, batch_size=batch_size, num_samples=[0, 0]).flow(
        nodes_type_2
    )

    schema = G.create_graph_schema()
    sampling_adj = schema.type_adjacency_list(["t2"], 2)

    assert len(mapper) == 1

    # Get a batch!
    batch_feats, batch_targets = mapper[0]
    assert len(batch_feats) == len(sampling_adj)


def test_hinnodemapper_no_neighbors():
    batch_size = 3
    feature_sizes = {"t1": 1, "t2": 1}
    G, nodes_type_1, nodes_type_2 = example_hin_3(feature_sizes)

    mapper = HinSAGENodeGenerator(G, batch_size=batch_size, num_samples=[2, 1]).flow(
        nodes_type_2
    )

    schema = G.create_graph_schema()
    sampling_adj = schema.type_adjacency_list(["t2"], 2)

    assert len(mapper) == 1

    # Get a batch!
    batch_feats, batch_targets = mapper[0]
    assert len(batch_feats) == len(sampling_adj)

    # Head nodes
    assert np.all(np.ravel(batch_feats[0]) == np.array([14, 15, 16]))

    # Next level - node 6 has no neighbours
    assert np.all(batch_feats[1][:, 0, 0] == np.array([10, 11, 0]))

    # Following level has two edge types
    # First edge type (e1): Node 0 has 4, node 1 has 5, and node 6 sampling has terminated
    assert np.all(batch_feats[2][:, 0, 0] == np.array([14, 15, 0]))

    # Second edge type (e2): Node 0 has 2, node 1 has none, and node 6 sampling has terminated
    assert np.all(batch_feats[3][:, 0, 0] == np.array([12, 0, 0]))


def create_graph_features():
    G = nx.Graph()
    G.add_nodes_from(["a", "b", "c"])
    G.add_edges_from([("a", "b"), ("b", "c"), ("a", "c")])
    G = G.to_undirected()
    return G, np.array([[1, 1], [1, 0], [0, 1]])


class Test_FullBatchNodeGenerator:
    """
    Tests of FullBatchNodeGenerator class
    """

    n_feat = 4
    target_dim = 5

    G = example_graph_3(feature_size=n_feat, n_nodes=6, n_isolates=1, n_edges=20)
    N = len(G.nodes())

    def test_generator_constructor(self):
        generator = FullBatchNodeGenerator(self.G)
        assert generator.Aadj.shape == (self.N, self.N)
        assert generator.features.shape == (self.N, self.n_feat)

    def test_generator_constructor_wrong_G_type(self):
        with pytest.raises(TypeError):
            generator = FullBatchNodeGenerator(nx.Graph(self.G))

    def test_generator_constructor_hin(self):
        feature_sizes = {"t1": 1, "t2": 1}
        Ghin, nodes_type_1, nodes_type_2 = example_hin_3(feature_sizes)
        with pytest.raises(TypeError):
            generator = FullBatchNodeGenerator(Ghin)

    def generator_flow(
        self, G, node_ids, node_targets, sparse=False, method="none", k=1
    ):
        generator = FullBatchNodeGenerator(G, sparse=sparse, method=method, k=k)
        n_nodes = len(G)

        gen = generator.flow(node_ids, node_targets)
        if sparse:
            [X, tind, A_ind, A_val], y = gen[0]
            A_sparse = sps.coo_matrix(
                (A_val[0], (A_ind[0, :, 0], A_ind[0, :, 1])), shape=(n_nodes, n_nodes)
            )
            A_dense = A_sparse.toarray()

        else:
            [X, tind, A], y = gen[0]
            A_dense = A[0]

        assert np.allclose(X, gen.features)  # X should be equal to gen.features
        assert tind.shape[1] == len(node_ids)

        if node_targets is not None:
            assert np.allclose(y, node_targets)

        # Check that the diagonals are one
        if method == "self_loops":
            assert np.allclose(A_dense.diagonal(), 1)

        return A_dense, tind, y

    def test_generator_flow_notargets(self):
        node_ids = list(self.G.nodes())[:3]
        _, tind, y = self.generator_flow(
            self.G, node_ids, None, sparse=False, method="none"
        )
        assert np.allclose(tind, range(3))
        _, tind, y = self.generator_flow(
            self.G, node_ids, None, sparse=True, method="none"
        )
        assert np.allclose(tind, range(3))

        node_ids = list(self.G.nodes())
        _, tind, y = self.generator_flow(
            self.G, node_ids, None, sparse=False, method="none"
        )
        assert np.allclose(tind, range(len(node_ids)))
        _, tind, y = self.generator_flow(
            self.G, node_ids, None, sparse=True, method="none"
        )
        assert np.allclose(tind, range(len(node_ids)))

    def test_generator_flow_withtargets(self):
        node_ids = list(self.G.nodes())[:3]
        node_targets = np.ones((len(node_ids), self.target_dim)) * np.arange(3)[:, None]
        _, tind, y = self.generator_flow(self.G, node_ids, node_targets, sparse=True)
        assert np.allclose(tind, range(3))
        assert np.allclose(y, node_targets[:3])
        _, tind, y = self.generator_flow(self.G, node_ids, node_targets, sparse=False)
        assert np.allclose(tind, range(3))
        assert np.allclose(y, node_targets[:3])

        node_ids = list(self.G.nodes())[::-1]
        node_targets = (
            np.ones((len(node_ids), self.target_dim))
            * np.arange(len(node_ids))[:, None]
        )
        _, tind, y = self.generator_flow(self.G, node_ids, node_targets)
        assert np.allclose(tind, range(len(node_ids))[::-1])
        assert np.allclose(y, node_targets)

    def test_generator_flow_targets_as_list(self):
        generator = FullBatchNodeGenerator(self.G)
        node_ids = list(self.G.nodes())[:3]
        node_targets = [1] * len(node_ids)
        gen = generator.flow(node_ids, node_targets)

        inputs, y = gen[0]
        assert y.shape == (1, 3)
        assert np.sum(y) == 3

    def test_generator_flow_targets_not_iterator(self):
        generator = FullBatchNodeGenerator(self.G)
        node_ids = list(self.G.nodes())[:3]
        node_targets = 1
        with pytest.raises(TypeError):
            generator.flow(node_ids, node_targets)

    def test_fullbatch_generator_init_1(self):
        G, feats = create_graph_features()
        nodes = G.nodes()
        node_features = pd.DataFrame.from_dict(
            {n: f for n, f in zip(nodes, feats)}, orient="index"
        )
        G = StellarGraph(G, node_type_name="node", node_features=node_features)

        generator = FullBatchNodeGenerator(G, name="test", method=None)
        assert generator.name == "test"
        assert np.array_equal(feats, generator.features)

    def test_fullbatch_generator_init_3(self):
        G, feats = create_graph_features()
        nodes = G.nodes()
        node_features = pd.DataFrame.from_dict(
            {n: f for n, f in zip(nodes, feats)}, orient="index"
        )
        G = StellarGraph(G, node_type_name="node", node_features=node_features)

        func = "Not callable"

        with pytest.raises(ValueError):
            generator = FullBatchNodeGenerator(G, "test", transform=func)

    def test_fullbatch_generator_transform(self):
        G, feats = create_graph_features()
        nodes = G.nodes()
        node_features = pd.DataFrame.from_dict(
            {n: f for n, f in zip(nodes, feats)}, orient="index"
        )
        G = StellarGraph(G, node_type_name="node", node_features=node_features)

        def func(features, A, **kwargs):
            return features, A.dot(A)

        generator = FullBatchNodeGenerator(G, "test", transform=func)
        assert generator.name == "test"

        A = nx.to_numpy_array(G)
        assert np.array_equal(A.dot(A), generator.Aadj.toarray())

    def test_generator_methods(self):
        node_ids = list(self.G.nodes())
        Aadj = nx.to_numpy_array(self.G)
        Aadj_selfloops = Aadj + np.eye(*Aadj.shape) - np.diag(Aadj.diagonal())
        Dtilde = np.diag(Aadj_selfloops.sum(axis=1) ** (-0.5))
        Agcn = Dtilde.dot(Aadj_selfloops).dot(Dtilde)

        A_dense, _, _ = self.generator_flow(
            self.G, node_ids, None, sparse=True, method="none"
        )
        assert np.allclose(A_dense, Aadj)
        A_dense, _, _ = self.generator_flow(
            self.G, node_ids, None, sparse=False, method="none"
        )
        assert np.allclose(A_dense, Aadj)

        A_dense, _, _ = self.generator_flow(
            self.G, node_ids, None, sparse=True, method="self_loops"
        )
        assert np.allclose(A_dense, Aadj_selfloops)
        A_dense, _, _ = self.generator_flow(
            self.G, node_ids, None, sparse=False, method="self_loops"
        )
        assert np.allclose(A_dense, Aadj_selfloops)

        A_dense, _, _ = self.generator_flow(
            self.G, node_ids, None, sparse=True, method="gat"
        )
        assert np.allclose(A_dense, Aadj_selfloops)
        A_dense, _, _ = self.generator_flow(
            self.G, node_ids, None, sparse=False, method="gat"
        )
        assert np.allclose(A_dense, Aadj_selfloops)

        A_dense, _, _ = self.generator_flow(
            self.G, node_ids, None, sparse=True, method="gcn"
        )
        assert np.allclose(A_dense, Agcn)
        A_dense, _, _ = self.generator_flow(
            self.G, node_ids, None, sparse=False, method="gcn"
        )
        assert np.allclose(A_dense, Agcn)

        # Check other pre-processing options
        A_dense, _, _ = self.generator_flow(
            self.G, node_ids, None, sparse=True, method="sgc", k=2
        )
        assert np.allclose(A_dense, Agcn.dot(Agcn))
        A_dense, _, _ = self.generator_flow(
            self.G, node_ids, None, sparse=False, method="sgc", k=2
        )
        assert np.allclose(A_dense, Agcn.dot(Agcn))
