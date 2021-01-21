import torch
import torch_geometric
from torch_geometric.data import Data, Batch


def test_batch():
    torch_geometric.set_debug(True)

    x1 = torch.tensor([1, 2, 3], dtype=torch.float)
    e1 = torch.tensor([[0, 1, 1, 2], [1, 0, 2, 1]])
    s1 = '1'
    x2 = torch.tensor([1, 2], dtype=torch.float)
    e2 = torch.tensor([[0, 1], [1, 0]])
    s2 = '2'

    batch = Batch.from_data_list([Data(x1, e1, s=s1), Data(x2, e2, s=s2)])

    assert batch.__repr__() == (
        'Batch(batch=[5], edge_index=[2, 6], ptr=[3], s=[2], x=[5])')
    assert len(batch) == 5
    assert batch.x.tolist() == [1, 2, 3, 1, 2]
    assert batch.edge_index.tolist() == [[0, 1, 1, 2, 3, 4],
                                         [1, 0, 2, 1, 4, 3]]
    assert batch.s == ['1', '2']
    assert batch.batch.tolist() == [0, 0, 0, 1, 1]
    assert batch.ptr.tolist() == [0, 3, 5]
    assert batch.num_graphs == 2

    data = batch[0]
    assert data.__repr__() == ('Data(edge_index=[2, 4], s="1", x=[3])')
    data = batch[1]
    assert data.__repr__() == ('Data(edge_index=[2, 2], s="2", x=[2])')

    assert len(batch.index_select([1, 0])) == 2
    assert len(batch.index_select(torch.tensor([1, 0]))) == 2
    assert len(batch.index_select(torch.tensor([True, False]))) == 1
    assert len(batch[:2]) == 2

    data_list = batch.to_data_list()
    assert len(data_list) == 2
    assert len(data_list[0]) == 3
    assert data_list[0].x.tolist() == [1, 2, 3]
    assert data_list[0].edge_index.tolist() == [[0, 1, 1, 2], [1, 0, 2, 1]]
    assert data_list[0].s == '1'
    assert len(data_list[1]) == 3
    assert data_list[1].x.tolist() == [1, 2]
    assert data_list[1].edge_index.tolist() == [[0, 1], [1, 0]]
    assert data_list[1].s == '2'

    torch_geometric.set_debug(True)


class MyData(Data):
    def __cat_dim__(self, key, item):
        if key == 'per_graph_tensor':
            return None
        else:
            return super().__cat_dim__(key, item)


def test_newaxis_batching():
    torch_geometric.set_debug(True)
    N_datas = 3
    N_nodes = torch.randint(low=3, high=10, size=(N_datas,))
    N_features = 8
    target_shape = (4, 7)
    datas = [
        MyData(
            x=torch.randn(n_node, N_features),
            per_graph_tensor=torch.randn(target_shape)
        )
        for n_node in N_nodes
    ]

    batch = Batch.from_data_list(datas)

    assert batch.x.shape == (sum(N_nodes), N_features)
    assert batch.per_graph_tensor.shape == (N_datas,) + target_shape
    for i in range(N_datas):
        orig = datas[i].per_graph_tensor
        from_batch = batch.get_example(i).per_graph_tensor
        assert orig.shape == target_shape
        assert orig.shape == from_batch.shape
        assert torch.all(orig == from_batch)
