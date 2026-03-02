import torch.nn as nn

# TCNModel_v1_outch64_GELU_head2
class TCN(nn.Module):
    def __init__(self, 
                 hidden_tcn: int = 64,
                 hidden_head: int = 64,
                 dilations: list = [1, 2, 4, 8],
                 kernel_size: int = 3,
                 in_channels: int = 6,
                 num_classes: int = 4,):
        super().__init__()
        
        self.hidden_tcn  = hidden_tcn
        self.hidden_head = hidden_head
        self.dilations   = dilations
        self.kernel_size = kernel_size
        self.in_channels = in_channels
        self.num_classes = num_classes
        
        self.tcn  = self._build_tcn()
        self.head = self._build_head()
        self.pool = self._build_pooling()
        self._init_weights()
        
    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv1d):
                nn.init.kaiming_normal_(m.weight, nonlinearity="relu")
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                nn.init.zeros_(m.bias)

    def _build_tcn(self):
        layers = []
        in_ch = self.in_channels
        out_ch = self.hidden_tcn
        
        for d in self.dilations:
            layers += [
                nn.Conv1d(in_ch, out_ch, kernel_size=self.kernel_size, padding=d, dilation=d),
                nn.BatchNorm1d(out_ch),
                nn.GELU(),
            ]
            in_ch = out_ch
        return nn.Sequential(*layers)
    
    def _build_pooling(self):
        def pool(x):
            return x.mean(-1)
        return pool

    def _build_head(self):
        return nn.Sequential(
            nn.LayerNorm(self.hidden_tcn),
            nn.Linear(self.hidden_tcn, self.hidden_head),
            nn.GELU(),
            nn.Linear(self.hidden_head, self.num_classes),
        )

    def forward(self, x):
        x = self.tcn(x)
        x = self.pool(x)
        x = self.head(x)
        return x








# class LUNA(nn.Module):
#     def __init__(self, ):
#         super().__init__()

#     def forward(self, x_signal, mask, channel_locations):
#         return x_classified, x_original


# class FEMBA(nn.Module):
#     def __init__(self, ):
#         super().__init__()

#     def forward(self, x, mask):
#         return x_classified, x_original


# class TinyMyo(nn.Module):
#     def __post_init__(self):
#         super().__init__()


#     def forward(self, ) :
#         return x_reconstructed, x_original

