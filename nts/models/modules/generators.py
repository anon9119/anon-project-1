import math

import torch
import torch.nn


class Wavetable(nn.Module):
    def __init__(
        self,
        wavetable_length: int,
        n_wavetables: int = 1,
        sample_rate: int = 16000,
        initialisation: str = "sine",
    ):
        super().__init__()
        self.wavetable_length = wavetable_length
        self.sr = sr

        if initialisation == "sine":
            sinusoid = torch.sin(
                math.tau
                * torch.ones(wavetable_length, n_wavetables).cumsum(0)
                / wavetable_length
            )
            self.wavetable = nn.Parameter(sinusoid[None, :, :, None])
        else:
            self.wavetable = nn.Parameter(
                torch.rand(1, wavetable_length, n_wavetables, 1)
            )

    def forward(self, f0: torch.Tensor):
        phase = (f0.cumsum(-1) / self.sr)[:, :, None, :] % 1
        wt_phase = torch.linspace(0.0, 1.0, self.wavetable_length, device=f0.device)[
            None, :, None, None
        ]
        diff = torch.abs(phase - wt_phase) * self.wavetable_length
        weights = F.relu(1 - diff)
        weighted_wavetable = self.wavetable * weights
        return weighted_wavetable.sum(1)


class ParallelNoise(nn.Module):
    def __init__(self, noise_channels: int = 1):
        super().__init__()
        self.noise_channels = noise_channels

    def forward(self, x: torch.Tensor):
        noise = torch.rand(
            1,
            self.noise_channels,
            x.shape[-1],
            device=x.device,
            requires_grad=x.requires_grad,
        ).expand(x.shape[0], -1, -1)
        noise = noise * 2 - 1
        noise = noise
        return torch.cat((noise, x), dim=1)