from itertools import repeat

import torch
from torch.nn import Sequential as Seq, Linear as Lin, ReLU
from torch_geometric.nn import GINConv, GINEConv


def test_gin_conv():
    in_channels, out_channels = (16, 32)
    edge_index = torch.tensor([[0, 0, 0, 1, 2, 3], [1, 2, 3, 0, 0, 0]])
    num_nodes = edge_index.max().item() + 1
    x = torch.randn((num_nodes, in_channels))

    nn = Seq(Lin(in_channels, 32), ReLU(), Lin(32, out_channels))
    conv = GINConv(nn, train_eps=True)
    assert conv.__repr__() == (
        'GINConv(nn=Sequential(\n'
        '  (0): Linear(in_features=16, out_features=32, bias=True)\n'
        '  (1): ReLU()\n'
        '  (2): Linear(in_features=32, out_features=32, bias=True)\n'
        '))')
    assert conv(x, edge_index).size() == (num_nodes, out_channels)
    jitcls = conv.jittable(x=x, edge_index=edge_index, full_eval=True)
    jitconv = jitcls(nn, train_eps=True)
    jitconv.load_state_dict(conv.state_dict())
    jittedconv = torch.jit.script(jitconv)
    conv.eval()
    jitconv.eval()
    jittedconv.eval()
    assert (torch.abs(conv(x, edge_index) -
            jitconv(x, edge_index)) < 1e-6).all().item()
    assert (torch.abs(conv(x, edge_index) -
            jittedconv(x, edge_index)) < 1e-6).all().item()

    conv = GINConv(nn, train_eps=False)
    assert conv(x, edge_index).size() == (num_nodes, out_channels)
    jitcls = conv.jittable(x=x, edge_index=edge_index, full_eval=True)
    jitconv = jitcls(nn, train_eps=False)
    jitconv.load_state_dict(conv.state_dict())
    jittedconv = torch.jit.script(jitconv)
    conv.eval()
    jitconv.eval()
    jittedconv.eval()
    assert (torch.abs(conv(x, edge_index) -
            jitconv(x, edge_index)) < 1e-6).all().item()
    assert (torch.abs(conv(x, edge_index) -
            jittedconv(x, edge_index)) < 1e-6).all().item()


def test_gine_conv():
    in_channels, out_channels = (16, 32)
    edge_index = torch.tensor([[0, 0, 0, 1, 2, 3], [1, 2, 3, 0, 0, 0]])
    num_nodes = edge_index.max().item() + 1
    x = torch.randn((num_nodes, in_channels))
    edge_attr = torch.randn((edge_index.size(1), in_channels))

    nn = Seq(Lin(in_channels, 32), ReLU(), Lin(32, out_channels))
    conv = GINEConv(nn, train_eps=True)
    assert conv.__repr__() == (
        'GINEConv(nn=Sequential(\n'
        '  (0): Linear(in_features=16, out_features=32, bias=True)\n'
        '  (1): ReLU()\n'
        '  (2): Linear(in_features=32, out_features=32, bias=True)\n'
        '))')
    assert conv(x, edge_index, edge_attr).size() == (num_nodes, out_channels)
    jitcls = conv.jittable(x=x, edge_index=edge_index,
                           edge_attr=edge_attr, full_eval=True)
    jitconv = jitcls(nn, train_eps=True)
    jitconv.load_state_dict(conv.state_dict())
    jittedconv = torch.jit.script(jitconv)
    conv.eval()
    jitconv.eval()
    jittedconv.eval()
    assert (torch.abs(conv(x, edge_index, edge_attr) -
            jitconv(x, edge_index, edge_attr)) < 1e-6).all().item()
    assert (torch.abs(conv(x, edge_index, edge_attr) -
            jittedconv(x, edge_index, edge_attr)) < 1e-6).all().item()

    conv = GINEConv(nn, train_eps=False)
    assert conv(x, edge_index, edge_attr).size() == (num_nodes, out_channels)
    jitcls = conv.jittable(x=x, edge_index=edge_index,
                           edge_attr=edge_attr, full_eval=True)
    jitconv = jitcls(nn, train_eps=False)
    jitconv.load_state_dict(conv.state_dict())
    jittedconv = torch.jit.script(jitconv)
    conv.eval()
    jitconv.eval()
    jittedconv.eval()
    assert (torch.abs(conv(x, edge_index, edge_attr) -
            jitconv(x, edge_index, edge_attr)) < 1e-6).all().item()
    assert (torch.abs(conv(x, edge_index, edge_attr) -
            jittedconv(x, edge_index, edge_attr)) < 1e-6).all().item()


def test_gin_conv_on_regular_graph():
    edge_index = torch.tensor([[0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5],
                               [1, 5, 0, 2, 1, 3, 2, 4, 3, 5, 0, 4]])
    x = torch.ones(6, 1)
    conv = GINConv(Seq(Lin(1, 8), ReLU(), Lin(8, 8)))

    out = conv(x, edge_index)
    for i in range(8):
        assert out[:, i].tolist() == list(repeat(out[0, i].item(), 6))
