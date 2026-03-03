import torch
from torch import nn
import pytorch_lightning as pl
from torchmetrics.classification import Accuracy
import hydra

class ClassificationTask(pl.LightningModule):
    def __init__(self, hparams):
        super().__init__()
        self.save_hyperparameters(hparams)
        self.model = hydra.utils.instantiate(self.hparams.model)
        self.criterion = hydra.utils.instantiate(self.hparams.criterion)
        
        self.num_classes   = hparams.model.get("num_classes", 4)
    
        # --- Loss function ---
        self.loss_fn = nn.CrossEntropyLoss()

        # --- Metrics ---
        self.train_acc = Accuracy(task="multiclass", num_classes=self.num_classes )
        # self.val_acc   = Accuracy(task="multiclass", num_classes=self.num_classes )
        self.test_acc  = Accuracy(task="multiclass", num_classes=self.num_classes )
    
    def forward(self, X):
        return self.model(X)
    
    
    def _extract_xy(self, batch):
        # CombinedLoader dict: {"BasicMotions_train": ...}
        if isinstance(batch, dict):
            batch = next(iter(batch.values()))

        # allow (X, y) or (X, y, meta...)
        if isinstance(batch, (tuple, list)) and len(batch) >= 2:
            return batch[0], batch[1]

        raise TypeError(f"Unexpected batch type/shape: {type(batch)}")
    
    # ------------------------------------------------------------
    # Training step
    # ------------------------------------------------------------
    def training_step(self, *args, **kwargs):
        # Possible patterns:
        # 1) (batch, batch_idx)
        # 2) (batch, batch_idx, dataloader_idx)
        # 3) (batch_idx, dataloader_idx=..., batch=...) weird ordering when called via *kwargs.values()

        dataloader_idx = kwargs.get("dataloader_idx", None)

        # Pull positional args
        if len(args) == 2:
            batch, batch_idx = args
        elif len(args) == 3:
            batch, batch_idx, dataloader_idx = args
        else:
            # last resort: try to find batch-like object in args
            batch = None
            batch_idx = None
            for a in args:
                if isinstance(a, (tuple, list, dict)) or hasattr(a, "shape"):
                    batch = a
                elif isinstance(a, int):
                    batch_idx = a
                elif isinstance(a, str):
                    dataloader_idx = a

            if batch is None:
                raise TypeError(f"Could not find batch in args={args}, kwargs={kwargs}")

        # If batch is a dict (CombinedLoader), take first value
        if isinstance(batch, dict):
            batch = next(iter(batch.values()))

        # If still not a tuple/list, print helpful debug once
        if not (isinstance(batch, (tuple, list)) and len(batch) >= 2):
            raise TypeError(f"Batch not (X,y). batch={batch} type={type(batch)} "
                            f"args={args} kwargs={kwargs} dl_idx={dataloader_idx}")

        X, y = batch[0], batch[1]
        logits = self(X)
        loss = self.loss_fn(logits, y)
        acc = self.train_acc(logits, y)
        self.log("train_loss", loss, prog_bar=True, on_epoch=True)
        self.log("train_acc", acc, prog_bar=True, on_epoch=True)
        return loss
    
    # def training_step(self, batch, batch_idx=None, dataloader_idx=None):
    #     # If Lightning passed the dataloader key into `batch`, swap.
    #     if isinstance(batch, str) and dataloader_idx is None:
    #         # likely call signature was (dataloader_idx, batch, batch_idx)
    #         dataloader_idx = batch
    #         batch = batch_idx
    #         batch_idx = None  # we don't need it for sanitycheck

    #     print("BATCH:", type(batch), "DL_IDX:", dataloader_idx)

    #     # CombinedLoader sometimes wraps batch in dict: {"data_module": (X, y)}
    #     if isinstance(batch, dict):
    #         batch = next(iter(batch.values()))

    #     X, y = batch
    #     logits = self(X)
    #     loss = self.loss_fn(logits, y)
    #     acc = self.train_acc(logits, y)
    #     self.log("train_loss", loss, prog_bar=True, on_epoch=True)
    #     self.log("train_acc", acc, prog_bar=True, on_epoch=True)
    #     return loss
    
    # def training_step(self, batch, batch_idx):
    #     print("BATCH:", batch, "TYPE:", type(batch))
    #     X, y = batch
    #     # X, y = self._extract_xy(batch)
    #     preds = self(X)
  
    #     loss = self.loss_fn(preds, y)
    #     acc = self.train_acc(preds, y)
    #     self.log("train_loss", loss, prog_bar=True, on_epoch=True)
    #     self.log("train_acc", acc, prog_bar=True, on_epoch=True)
    #     return loss

        
    # ------------------------------------------------------------
    # Test step
    # ------------------------------------------------------------
    def test_step(self, batch, batch_idx=None, dataloader_idx=None):
        if isinstance(batch, str) and dataloader_idx is None:
            dataloader_idx = batch
            batch = batch_idx
            batch_idx = None
        if isinstance(batch, dict):
            batch = next(iter(batch.values()))
        X, y = batch
        preds = self(X)
        
        loss = self.loss_fn(preds, y)
        acc = self.test_acc(preds, y)
        self.log("test_loss", loss)
        self.log("test_acc", acc)
    
    # def test_step(self, batch, batch_idx):
    #     X, y = batch
    #     # X, y = self._extract_xy(batch)
    #     preds = self(X)
        
    #     loss = self.loss_fn(preds, y)
    #     acc = self.test_acc(preds, y)
    #     self.log("test_loss", loss)
    #     self.log("test_acc", acc)


    # ------------------------------------------------------------
    # Optimizer and scheduler configuration
    # ------------------------------------------------------------
    def configure_optimizers(self):
        if self.hparams.optimizer.optim == 'AdamW':
            optimizer = torch.optim.AdamW(self.model.parameters(), lr=self.hparams.optimizer.lr)

        scheduler = hydra.utils.instantiate(self.hparams.scheduler, optimizer)
        lr_scheduler_config = {
            "scheduler": scheduler,
            "interval": "step",
            "frequency": 1,
        }

        return {"optimizer": optimizer, "lr_scheduler": lr_scheduler_config}
    
    
    
    
    # ------------------------------------------------------------
    # Validation step
    # ------------------------------------------------------------
    # def validation_step(self, batch, batch_idx):
    #     X, y = batch
    #     preds = self(X) 
        
    #     loss = self.loss_fn(preds, y)
    #     acc = self.val_acc(preds, y)
    #     self.log("val_loss", loss, prog_bar=True, on_epoch=True, logger=True, on_step=False)
    #     self.log("val_acc", acc, prog_bar=True, on_epoch=True, logger=True, on_step=False)
