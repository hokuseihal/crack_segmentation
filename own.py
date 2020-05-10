import torch
from torchvision.transforms import Resize,ToTensor,Compose,Grayscale
import glob
import random
from PIL import Image


class CrackDataset(torch.utils.data.Dataset):
    #TODO if train sample k images
    def __init__(self,rawp,maskp,transform=None,sample_k=None):
        self.raw=sorted(glob.glob(f'{rawp}/*'))
        self.mask=sorted(glob.glob(f'{maskp}/*'))
        #if sec=='train':
        #    sample_k=random.sample(range(len(self.raw)),sample_k)
        #self.raw=self.raw[sample_k]
        #self.mask=self.mask[sample_k]
        self.in_channels=3
        self.out_channels=1
        self.transform=transform if transform is not None else Compose([Resize((256,256)),ToTensor()])

        assert len(self.raw)==len(self.mask)
    def __len__(self):
        return len(self.raw)

    def __getitem__(self, item):
        imraw=Image.open(self.raw[item])
        immask=Image.open(self.mask[item])
        return self.transform(imraw),self.transform(immask)