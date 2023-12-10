import torch
import torch.nn as nn


class conv_block(nn.Module):

    def __init__(self, in_c, out_c):
        super().__init__()
        self.conv1 = nn.Conv2d(in_c, out_c, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(out_c)
        self.conv2 = nn.Conv2d(out_c, out_c, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(out_c)
        self.relu = nn.ReLU()

    def forward(self, inputs):
        x = self.conv1(inputs)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.conv2(x)
        x = self.bn2(x)
        x = self.relu(x)
        return x

class encoder_block(nn.Module):
    def __init__(self, in_c, out_c):
        super().__init__()
        self.conv = conv_block(in_c, out_c)
        self.pool = nn.MaxPool2d((2, 2))
    def forward(self, inputs):
        x = self.conv(inputs)
        p = self.pool(x)
        return x, p

class decoder_block(nn.Module):
    def __init__(self, in_c, out_c):
        super().__init__()
        self.up = nn.ConvTranspose2d(in_c, out_c, kernel_size=2, stride=2, padding=0)
        self.conv = conv_block(out_c+out_c, out_c)
    def forward(self, inputs, skip):
        x = self.up(inputs)
        x = torch.cat([x, skip], axis=1)
        x = self.conv(x)
        return x


import torch.nn as nn

class UNet(torch.nn.Module):
    def __init__(self, depth, base_dim, in_channels, out_channels):
        """
        Initializes the UNet model.

        Parameters:
        - depth (int): Depth of the U-Net architecture.
        - base_dim (int): Number of channels in the first encoder block.
        - in_channels (int): Number of input channels.
        - out_channels (int): Number of output channels.
        """
        super(UNet, self).__init__()

        # Encoder
        self.depth = depth
        self.e1 = encoder_block(in_channels, base_dim)
        for i in range(2, depth + 1):
            setattr(self, f'e{i}', encoder_block(int(base_dim), int(base_dim * 2)))
            base_dim *= 2

        # Bottleneck
        self.b = conv_block(base_dim, base_dim * 2)
        base_dim *= 2

        # Decoder
        for i in range(1, depth + 1):
            setattr(self, f'd{i}', decoder_block(int(base_dim), int(base_dim / 2)))
            base_dim /= 2

        # Classifier
        self.outputs = nn.Conv2d(int(base_dim), out_channels, kernel_size=1, padding=0)

    def forward(self, inputs):
        # Encoder
        s = [None] * self.depth
        p = [None] * self.depth
        s[0], p[0] = self.e1(inputs)
        for i in range(2, self.depth + 1):
            e_block = getattr(self, f'e{i}')
            s[i - 1], p[i - 1] = e_block(p[i - 2])

        # Bottleneck
        b = self.b(p[self.depth - 1])

        # Decoder
        for i in range(1, self.depth + 1):
            d_block = getattr(self, f'd{i}')
            b = d_block(b, s[self.depth - i])

        # Classifier
        outputs = self.outputs(b)
        return outputs
