# -*- coding: utf-8 -*-
#
# Copyright 2018-2019 Data61, CSIRO
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest
from stellargraph.utils.saliency_maps import IntegratedGradientsGAT
import numpy as np
from stellargraph.layer import GraphAttention
from stellargraph import StellarGraph
from stellargraph.layer import GAT
from stellargraph.mapper import FullBatchNodeGenerator
from keras import Model
from keras.optimizers import Adam
from keras.losses import categorical_crossentropy
import networkx as nx
import keras.backend as K
import keras


def example_graph_1(feature_size=None):
    G = nx.Graph()
    elist = [(0, 1), (0, 2), (2, 3), (3, 4), (0, 0), (1, 1), (2, 2), (3, 3), (4, 4)]
    G.add_nodes_from([0, 1, 2, 3, 4], label="default")
    G.add_edges_from(elist, label="default")

    # Add example features
    if feature_size is not None:
        for v in G.nodes():
            G.node[v]["feature"] = np.ones(feature_size)
        return StellarGraph(G, node_features="feature")

    else:
        return StellarGraph(G)


def create_GAT_model(graph):
    generator = FullBatchNodeGenerator(graph, sparse=False, method=None)
    train_gen = generator.flow([0, 1], np.array([[1, 0], [0, 1]]))

    gat = GAT(
        layer_sizes=[2, 2],
        generator=generator,
        bias=False,
        in_dropout=0,
        attn_dropout=0,
        activations=["elu", "softmax"],
        normalize=None,
        saliency_map_support=True,
    )
    for layer in gat._layers:
        layer._initializer = "ones"
    x_inp, x_out = gat.node_model()
    keras_model = Model(inputs=x_inp, outputs=x_out)
    return gat, keras_model, generator, train_gen


def get_ego_node_num(graph, target_idx):
    G_ego = nx.ego_graph(graph, target_idx, radius=2)
    return G_ego.number_of_nodes()


def test_ig_saliency_map():
    graph = example_graph_1(feature_size=4)
    base_model, keras_model_gat, generator, train_gen = create_GAT_model(graph)
    keras_model_gat.compile(
        optimizer=Adam(lr=0.1), loss=categorical_crossentropy, weighted_metrics=["acc"]
    )
    weights = [
        np.array(
            [
                [0.47567585, 0.7989239],
                [0.33588523, 0.19814175],
                [0.15685713, 0.43643117],
                [0.7725941, 0.68441933],
            ]
        ),
        np.array([[0.71832293], [0.8542117]]),
        np.array([[0.46560588], [0.8165422]]),
        1.0,
        0.0,
        np.array([[0.4391179, 0.595691], [0.06000895, 0.2613866]]),
        np.array([[0.43496376], [0.02840129]]),
        np.array([[0.33972418], [0.22352563]]),
        1.0,
        0.0,
    ]
    keras_model_gat.set_weights(weights)

    # sanity check to make sure that the values of delta and non_exist_edges are not trainable
    # the expected value should be delta = 1.0 and non_exist_edges = 0.0
    for var in keras_model_gat.non_trainable_weights:
        if "ig_delta" in var.name:
            assert K.get_value(var) == 1.0
        if "ig_non_exist_edge" in var.name:
            assert K.get_value(var) == 0.0

    ig_saliency = IntegratedGradientsGAT(
        keras_model_gat, train_gen, generator.node_list
    )
    target_id = 0
    class_of_interest = 0
    ig_link_importance = ig_saliency.get_link_importance(
        target_id, class_of_interest, steps=200
    )
    print(ig_link_importance)

    ig_link_importance_ref = np.array(
        [
            [4.759e-11, 4.759e-11, 4.759e-11, 0, 0],
            [-1.442e-10, -1.442e-10, 0, 0, 0],
            [1.183e-10, 0, 1.183e-10, 1.183e-10, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
        ]
    )
    # Check the number of non-zero elements in the node importance matrix. We expect to see the number be same with the number of nodes in the ego network.
    assert pytest.approx(
        np.sum(np.ma.masked_array(ig_link_importance, mask=train_gen.A_dense)), 0
    )
    assert pytest.approx(ig_link_importance_ref, abs=1e-11) == ig_link_importance
    non_zero_edge_importance = np.sum(np.abs(ig_link_importance) > 1e-11)
    assert 8 == non_zero_edge_importance
    ig_node_importance = ig_saliency.get_node_importance(
        target_id, class_of_interest, steps=200
    )
    print(ig_node_importance)
    assert pytest.approx(ig_node_importance, np.array([-13.06, -9.32, -7.46, -3.73, 0]))
    non_zero_node_importance = np.sum(np.abs(ig_node_importance) > 1e-5)
    assert 4 == non_zero_node_importance
