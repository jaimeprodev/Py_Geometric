import torch
import torch.nn.functional as F
from torch.utils.checkpoint import checkpoint


class DeepGCNLayer(torch.nn.Module):
    r"""The skip connection operations from the
    `"DeepGCNs: Can GCNs Go as Deep as CNNs?"
    <https://arxiv.org/abs/1904.03751>`_ and `"All You Need to Train Deeper
    GCNs" <https://arxiv.org/abs/2006.07739>`_ papers.
    The implemented skip connections includes the pre-activation residual
    connection (:obj:`"res+"`), the residual connection (:obj:`"res"`),
    the dense connection (:obj:`"dense"`) and no connections (:obj:`"plain"`).

    * **Res+** (:obj:`"res+"`):

    .. math::
        \text{Normalization}\to\text{Activation}\to\text{Dropout}\to
        \text{GraphConv}\to\text{Res}

    * **Res** (:obj:`"res"`) / **Dense** (:obj:`"dense"`) / **Plain**
      (:obj:`"plain"`):

    .. math::
        \text{GraphConv}\to\text{Normalization}\to\text{Activation}\to
        \text{Res/Dense/Plain}\to\text{Dropout}

    .. note::

        For an example of using :obj:`GENConv`, see
        `examples/ogbn_proteins_deepgcn.py
        <https://github.com/rusty1s/pytorch_geometric/blob/master/examples/
        ogbn_proteins_deepgcn.py>`_.

    Args:
        conv (torch.nn.Module, optional): the GCN operator.
            (default: :obj:`None`)
        norm (torch.nn.Module): the normalization layer. (default: :obj:`None`)
        act (torch.nn.Module): the activation layer. (default: :obj:`None`)
        block (string, optional): The skip connection operation to use
            (:obj:`"res+"`, :obj:`"res"`, :obj:`"dense"` or :obj:`"plain"`).
            (default: :obj:`"res+"`)
        dropout: (float, optional): Whether to apply or dropout.
            (default: :obj:`0.`)
        ckpt_grad (bool, optional): If set to :obj:`True`, will checkpoint this
            part of the model. Checkpointing works by trading compute for
            memory, since intermediate activations do not need to be kept in
            memory. Set this to :obj:`True` in case you encounter out-of-memory
            errors while going deep. (default: :obj:`False`)
    """
    def __init__(self, conv=None, norm=None, act=None, block='res+',
                 dropout=0., ckpt_grad=False):
        super(DeepGCNLayer, self).__init__()

        self.conv = conv
        self.norm = norm
        self.act = act
        self.block = block.lower()
        assert self.block in ['res+', 'res', 'dense', 'plain']
        self.dropout = dropout
        self.ckpt_grad = ckpt_grad

    def reset_parameters(self):
        self.conv.reset_parameters()
        self.norm.reset_parameters()

    def forward(self, *args, **kwargs):
        """"""
        args = list(args)
        x = args.pop(0)

        if self.block == 'res+':
            if self.norm is not None:
                h = self.norm(x)
            if self.act is not None:
                h = self.act(h)
            h = F.dropout(h, p=self.dropout, training=self.training)
            if self.conv is not None and self.ckpt_grad and h.requires_grad:
                h = checkpoint(self.conv, h, *args, **kwargs)
            else:
                h = self.conv(h, *args, **kwargs)

            return x + h

        else:
            if self.conv is not None and self.ckpt_grad and x.requires_grad:
                h = checkpoint(self.conv, x, *args, **kwargs)
            else:
                h = self.conv(x, *args, **kwargs)
            if self.norm is not None:
                h = self.norm(x)
            if self.act is not None:
                h = self.act(h)

            if self.block == 'res':
                return x + h
            elif self.block == 'dense':
                return torch.cat([x, h], dim=-1)
            elif self.block == 'plain':
                return h

    def __repr__(self):
        return '{}(block={})'.format(self.__class__.__name__, self.block)
