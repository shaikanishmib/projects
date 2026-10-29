"""Small CPU CNN; no pretrained weights or network downloads."""

from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from .data import Sample
from .features import pixels


class Images(Dataset):
    def __init__(self, root: Path, samples: list[Sample], size: int, augment: bool = False, brightness: float = 1.):
        self.root, self.samples, self.size = root, samples, size
        self.augment, self.brightness = augment, brightness

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        sample = self.samples[index]
        array = pixels(self.root, sample, self.size, self.brightness)
        image = torch.from_numpy(array.copy()).permute(2, 0, 1)
        if self.augment:
            if torch.rand(()) < .5:
                image = image.flip(1)
            if torch.rand(()) < .5:
                image = image.flip(2)
            image = image.rot90(int(torch.randint(0, 4, ()).item()), (1, 2))
        return image, torch.tensor(sample.label, dtype=torch.float32)


class SmallCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Conv2d(3, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.AdaptiveAvgPool2d(1),
            nn.Flatten(), nn.Linear(64, 1),
        )

    def forward(self, images):
        return self.layers(images).squeeze(1)


def predict(model: SmallCNN, dataset: Images, batch_size: int) -> np.ndarray:
    model.eval()
    values = []
    with torch.no_grad():
        for images, _ in DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=0):
            values.extend(torch.sigmoid(model(images)).tolist())
    return np.asarray(values)


def train_cnn(root: Path, splits: dict[str, list[Sample]], config: dict, output: Path):
    from sklearn.metrics import log_loss

    torch.manual_seed(config["seed"])
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(config["threads"])
    model = SmallCNN()
    optimizer = torch.optim.AdamW(model.parameters(), lr=config["learning_rate"], weight_decay=.0001)
    training = Images(root, splits["train"], config["image_size"], augment=True)
    validation = Images(root, splits["validation"], config["image_size"])
    # Each patient has equal total contribution regardless of their image count.
    counts = {}
    for s in splits["train"]:
        counts[s.patient_id] = counts.get(s.patient_id, 0) + 1
    weights = torch.tensor([1 / counts[s.patient_id] for s in splits["train"]])
    sampler = torch.utils.data.WeightedRandomSampler(weights, len(training), replacement=True)
    loader = DataLoader(training, batch_size=config["batch_size"], sampler=sampler, num_workers=0)
    history, best = [], float("inf")
    for epoch in range(config["epochs"]):
        model.train()
        losses = []
        for images, labels in loader:
            optimizer.zero_grad(set_to_none=True)
            loss = nn.functional.binary_cross_entropy_with_logits(model(images), labels)
            if not torch.isfinite(loss):
                raise ValueError("Nonfinite training loss")
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach()))
        probabilities = predict(model, validation, config["batch_size"])
        grouped = {}
        for sample, probability in zip(splits["validation"], probabilities):
            grouped.setdefault(sample.patient_id, [sample.label, []])[1].append(probability)
        val_loss = float(log_loss([v[0] for v in grouped.values()],
                                  [np.mean(v[1]) for v in grouped.values()], labels=[0, 1]))
        history.append({"epoch": epoch + 1, "training_batch_mean_loss": float(np.mean(losses)),
                        "validation_patient_log_loss": val_loss})
        if val_loss < best:
            best = val_loss
            torch.save(model.state_dict(), output / "cnn.pt")
    model.load_state_dict(torch.load(output / "cnn.pt", map_location="cpu", weights_only=True))
    return model, history
