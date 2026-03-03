#*----------------------------------------------------------------------------*
#* Copyright (C) 2025 ETH Zurich, Switzerland                                 *
#* SPDX-License-Identifier: Apache-2.0                                        *
#*                                                                            *
#* Licensed under the Apache License, Version 2.0 (the "License");            *
#* you may not use this file except in compliance with the License.           *
#* You may obtain a copy of the License at                                    *
#*                                                                            *
#* http://www.apache.org/licenses/LICENSE-2.0                                 *
#*                                                                            *
#* Unless required by applicable law or agreed to in writing, software        *
#* distributed under the License is distributed on an "AS IS" BASIS,          *
#* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.   *
#* See the License for the specific language governing permissions and        *
#* limitations under the License.                                             *
#*                                                                            *
#* Author:  Anna Tegon                                                        *
#* Author:  Thorir Mar Ingolfsson                                             *
#*----------------------------------------------------------------------------*

import torch
import torch.nn as nn
import pytorch_lightning as pl
import hydra
from safetensors.torch import load_file
import torch_optimizer as torch_optim
import torch.nn.functional as F
from torchmetrics import MetricCollection
from torchmetrics.classification import (
    Accuracy, Precision, Recall, AUROC,
    AveragePrecision, CohenKappa, F1Score
)
from util.train_utils import RobustQuartileNormalize

class ClassificationTask(pl.LightningModule):

    def __init__(self, hparams):
        super().__init__()
        self.save_hyperparameters(hparams)
        self.model = hydra.utils.instantiate(self.hparams.model)
        self.num_classes = self.hparams.model.num_classes
        self.classification_type = self.hparams.classification_type

        # Input normalization
        if self.hparams.input_normalization is not None and self.hparams.input_normalization.normalize:
            self.normalize = True
            self.normalize_fct = RobustQuartileNormalize(
                self.hparams.input_normalization.quartile_normalization_lower_val,
                self.hparams.input_normalization.quartile_normalization_upper_val
            )

        # Loss function
        self.criterion = nn.CrossEntropyLoss()
        
        # Metrics
        self.classification_task = "multiclass"
        label_metrics = MetricCollection([
            Accuracy(task=self.classification_task, num_classes=self.num_classes, average="macro"),
            Recall(task='multiclass', num_classes=self.num_classes, average="macro"),
            Precision(task=self.classification_task, num_classes=self.num_classes, average="macro"),
            F1Score(task=self.classification_task, num_classes=self.num_classes, average="macro"),
            CohenKappa(task=self.classification_task, num_classes=self.num_classes)
        ])
        logit_metrics = MetricCollection([
            AUROC(task=self.classification_task, num_classes=self.num_classes, average="macro"),
            AveragePrecision(task=self.classification_task, num_classes=self.num_classes, average="macro"),
        ])
        self.train_label_metrics = label_metrics.clone(prefix='train_')
        self.val_label_metrics   = label_metrics.clone(prefix='val_')
        self.test_label_metrics  = label_metrics.clone(prefix='test_')
        self.train_logit_metrics = logit_metrics.clone(prefix='train_')
        self.val_logit_metrics   = logit_metrics.clone(prefix='val_')
        self.test_logit_metrics  = logit_metrics.clone(prefix='test_')

    def load_pretrained_checkpoint(self, model_ckpt):
        """
        Load a pretrained model checkpoint and unfreeze specific layers for fine-tuning.
        """
        assert self.model.classifier is not None
        print("Loading pretrained checkpoint")
        ckpt = torch.load(model_ckpt)
        self.load_state_dict(ckpt['state_dict'], strict=False)

        for name, param in self.model.named_parameters():
            if self.hparams.finetuning.freeze_layers:
                param.requires_grad = True
            if 'classifier' in name:
                param.requires_grad = True

        print("Pretrained model ready.")
    
    def load_safetensors_checkpoint(self, model_ckpt):
        """
        Load a pretrained model checkpoint in safetensors format and unfreeze specific layers for fine-tuning.
        """
        assert self.model.classifier is not None
        print("Loading pretrained safetensors checkpoint")
        state_dict = load_file(model_ckpt)
        self.load_state_dict(state_dict, strict=False)

        for name, param in self.model.named_parameters():
            if self.hparams.finetuning.freeze_layers:
                param.requires_grad = True
            if 'classifier' in name:
                param.requires_grad = True

        print("Pretrained model ready.")

    

    def _step(self, X):
        y_pred_logits = self.model(X)

        y_pred_probs = torch.softmax(y_pred_logits, dim=1)
        y_pred_label = torch.argmax(y_pred_probs, dim=1)

        return {
            'label': y_pred_label,
            'probs': y_pred_probs,
            'logits': y_pred_logits,
        }

    def training_step(self, batch, batch_idx):
        X, y = batch
        if self.normalize:
            X = self.normalize_fct(X)

        y_pred = self._step(X)
        loss = self.criterion(y_pred['logits'], y)

        self.train_label_metrics(y_pred['label'], y)
        self.train_logit_metrics(y_pred['logits'], y)
        self.log_dict(self.train_label_metrics, on_step=True, on_epoch=False)
        self.log_dict(self.train_logit_metrics, on_step=True, on_epoch=False)
        self.log('train_loss', loss, on_step=True, on_epoch=True, prog_bar=True, logger=True, sync_dist=True)
        return loss

    def validation_step(self, batch, batch_idx):
        X, y = batch
        if self.normalize:
            X = self.normalize_fct(X)

        y_pred = self._step(X)
        loss = self.criterion(y_pred['logits'], y)

        self.val_label_metrics(y_pred['label'], y)
        self.val_logit_metrics(y_pred['logits'], y)
        self.log_dict(self.val_label_metrics, on_step=False, on_epoch=True)
        self.log_dict(self.val_logit_metrics, on_step=False, on_epoch=True)
        self.log('val_loss', loss, prog_bar=True, logger=True, sync_dist=True)
        return loss

    def test_step(self, batch, batch_idx):
        X, y = batch
        if self.normalize:
            X = self.normalize_fct(X)

        y_pred = self._step(X)
        loss = self.criterion(y_pred['logits'], y)

        self.test_label_metrics(y_pred['label'], y)
        self.test_logit_metrics(y_pred['logits'], y)
        self.log_dict(self.test_label_metrics, on_step=False, on_epoch=True)
        self.log_dict(self.test_logit_metrics, on_step=False, on_epoch=True)
        self.log('test_loss', loss, prog_bar=True, logger=True, sync_dist=True)
        return loss

    def configure_optimizers(self):
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=self.hparams.optimizer.lr)

        scheduler = hydra.utils.instantiate(self.hparams.scheduler, optimizer)
        lr_scheduler_config = {
            "scheduler": scheduler,
            "interval": "step",
            "frequency": 1,
        }

        return {"optimizer": optimizer, "lr_scheduler": lr_scheduler_config}
    
    
