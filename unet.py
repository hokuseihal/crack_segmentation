from collections import OrderedDict

import torch
import torch.nn as nn
from torchvision.utils import save_image


class UNet(nn.Module):

    def __init__(self, in_channels=3, out_channels=1, init_features=32, cutpath=False, savefolder=False,dropout=0.2):
        super(UNet, self).__init__()

        features = init_features
        self.cutpath = cutpath
        self.savefolder = savefolder
        self.encoder1 = UNet._block(in_channels, features, name="enc1")
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.encoder2 = UNet._block(features, features * 2, name="enc2")
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.encoder3 = UNet._block(features * 2, features * 4, name="enc3")
        self.pool3 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.encoder4 = UNet._block(features * 4, features * 8, name="enc4")
        self.pool4 = nn.MaxPool2d(kernel_size=2, stride=2)

        self.bottleneck = UNet._block(features * 8, features * 16, name="bottleneck")

        self.upconv4 = nn.ConvTranspose2d(
            features * 16, features * 8, kernel_size=2, stride=2
        )
        self.decoder4 = UNet._block((features * 8) * 2, features * 8, name="dec4")
        self.upconv3 = nn.ConvTranspose2d(
            features * 8, features * 4, kernel_size=2, stride=2
        )
        self.decoder3 = UNet._block((features * 4) * 2, features * 4, name="dec3")
        self.upconv2 = nn.ConvTranspose2d(
            features * 4, features * 2, kernel_size=2, stride=2
        )
        self.decoder2 = UNet._block((features * 2) * 2, features * 2, name="dec2")
        self.upconv1 = nn.ConvTranspose2d(
            features * 2, features, kernel_size=2, stride=2
        )
        self.decoder1 = UNet._block(features * 2, features, name="dec1")

        self.conv = nn.Conv2d(
            in_channels=features, out_channels=out_channels, kernel_size=1
        )
        self.dropout1=nn.Dropout(dropout)
        self.dropout2=nn.Dropout(dropout)
        self.dropout3=nn.Dropout(dropout)
        self.dropout4=nn.Dropout(dropout)

    def forward(self, x):
        enc1 = self.dropout1(self.encoder1(x))
        enc2 = self.dropout2(self.encoder2(self.pool1(enc1)))
        enc3 = self.dropout3(self.encoder3(self.pool2(enc2)))
        enc4 = self.dropout4(self.encoder4(self.pool3(enc3)))

        bottleneck = self.bottleneck(self.pool4(enc4))

        if self.cutpath:
            enc1 = torch.zeros_like(enc1)
            enc2 = torch.zeros_like(enc2)
            enc3 = torch.zeros_like(enc3)
            enc4 = torch.zeros_like(enc4)
        dec4 = self.upconv4(bottleneck)
        dec4 = torch.cat((dec4, enc4), dim=1)
        dec4 = self.decoder4(dec4)
        dec3 = self.upconv3(dec4)
        dec3 = torch.cat((dec3, enc3), dim=1)
        dec3 = self.decoder3(dec3)
        dec2 = self.upconv2(dec3)
        dec2 = torch.cat((dec2, enc2), dim=1)
        dec2 = self.decoder2(dec2)
        dec1 = self.upconv1(dec2)
        dec1 = torch.cat((dec1, enc1), dim=1)
        dec1 = self.decoder1(dec1)

        if self.savefolder:
            save_image(enc1[0].unsqueeze(1), f'{self.savefolder}/enc1_out.jpg')
            save_image(enc2[0].unsqueeze(1), f'{self.savefolder}/enc2_out.jpg')
            save_image(enc3[0].unsqueeze(1), f'{self.savefolder}/enc3_out.jpg')
            save_image(enc4[0].unsqueeze(1), f'{self.savefolder}/enc4_out.jpg')
            save_image(dec1[0].unsqueeze(1), f'{self.savefolder}/dec1_out.jpg')
            save_image(dec2[0].unsqueeze(1), f'{self.savefolder}/dec2_out.jpg')
            save_image(dec3[0].unsqueeze(1), f'{self.savefolder}/dec3_out.jpg')
            save_image(dec4[0].unsqueeze(1), f'{self.savefolder}/dec4_out.jpg')
            save_image(self.encoder1.enc1conv1.weight[:,0].unsqueeze(1),f'{self.savefolder}/encoder1.jpg')
            save_image(self.encoder2.enc2conv1.weight[:,0].unsqueeze(1),f'{self.savefolder}/encoder2.jpg')
            save_image(self.encoder3.enc3conv1.weight[:,0].unsqueeze(1),f'{self.savefolder}/encoder3.jpg')
            save_image(self.encoder4.enc4conv1.weight[:,0].unsqueeze(1),f'{self.savefolder}/encoder4.jpg')
            save_image(self.decoder1.dec1conv1.weight[:,0].unsqueeze(1),f'{self.savefolder}/decoder1.jpg')
            save_image(self.decoder2.dec2conv1.weight[:,0].unsqueeze(1),f'{self.savefolder}/decoder2.jpg')
            save_image(self.decoder3.dec3conv1.weight[:,0].unsqueeze(1),f'{self.savefolder}/decoder3.jpg')
            save_image(self.decoder4.dec4conv1.weight[:,0].unsqueeze(1),f'{self.savefolder}/decoder4.jpg')
        return torch.sigmoid(self.conv(dec1))

    @staticmethod
    def _block(in_channels, features, name):
        return nn.Sequential(
            OrderedDict(
                [
                    (
                        name + "conv1",
                        nn.Conv2d(
                            in_channels=in_channels,
                            out_channels=features,
                            kernel_size=3,
                            padding=1,
                            bias=False,
                        ),
                    ),
                    (name + "norm1", nn.BatchNorm2d(num_features=features)),
                    (name + "relu1", nn.ReLU(inplace=True)),
                    (
                        name + "conv2",
                        nn.Conv2d(
                            in_channels=features,
                            out_channels=features,
                            kernel_size=3,
                            padding=1,
                            bias=False,
                        ),
                    ),
                    (name + "norm2", nn.BatchNorm2d(num_features=features)),
                    (name + "relu2", nn.ReLU(inplace=True)),
                ]
            )
        )


class wrapped_UNet(nn.Module):
    def __init__(self, unet, in_ch, out_ch):
        super(wrapped_UNet, self).__init__()
        self.unet = unet
        self.conv = nn.Conv2d(in_ch, out_ch, 1)

    def forward(self, x):
        x = self.unet(x)
        x = self.conv(x)
        return x
