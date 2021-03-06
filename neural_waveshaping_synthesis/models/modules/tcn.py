from typing import Callable, Union

import gin
import torch
import torch.nn as nn
import torch.nn.functional as F

from .utils import CausalPad, Identity


class CausalTCNBlock(nn.Module):
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
        dilation: int,
        lookahead: int = 0,
        nonlinearity: Union[Callable, nn.Module] = nn.ReLU,
        final_nonlinearity: bool = True,
    ):
        super().__init__()
        self.net = nn.Sequential(
            CausalPad(kernel_size * dilation - dilation, lookahead),
            nn.Conv1d(in_channels, out_channels, kernel_size, dilation=dilation),
            nonlinearity(),
            CausalPad(kernel_size * dilation - dilation, lookahead),
            nn.Conv1d(out_channels, out_channels, kernel_size, dilation=dilation),
            nonlinearity() if final_nonlinearity else Identity(),
        )
        self.rescale = (
            nn.Conv1d(in_channels, out_channels, 1)
            if in_channels != out_channels
            else None
        )

    def forward(self, x: torch.Tensor):
        residual = x if not self.rescale else self.rescale(x)
        return self.net(x) + residual


@gin.configurable
class CausalTCN(nn.Module):
    def __init__(
        self,
        in_channels: int,
        hidden_channels: int,
        out_channels: int,
        kernel_size: int,
        dilation: int,
        depth: int,
        lookahead: int = 0,
    ):
        super().__init__()
        tcn_blocks = [
            CausalTCNBlock(
                hidden_channels if d > 0 else in_channels,
                hidden_channels if d < depth - 1 else out_channels,
                kernel_size,
                dilation ** d,
                lookahead,
                final_nonlinearity=True if d < depth - 1 else False,
            )
            for d in range(depth)
        ]
        self.net = nn.Sequential(*tcn_blocks)

    def forward(self, x: torch.Tensor):
        return self.net(x)