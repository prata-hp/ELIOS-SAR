---
license: agpl-3.0
language:
- en
base_model:
- Ultralytics/YOLO26
pipeline_tag: image-segmentation
tags:
- rock-segmentation
- excavator
- rock-picking
datasets:
- akahukas/rock-segmentation-dataset
---

# YOLO26n-seg for Rock Segmentation

<div align="center">
  <table width="100%">
    <tr>
      <td align="center"><b>Original RGB</b></td>
      <td align="center"><b>Segmentation Mask</b></td>
      <td align="center"><b>Contour Overlay</b></td>
    </tr>
    <tr>
      <td width="33.3%"><img src="assets/yolo26_rgb.jpg" width="100%"></td>
      <td width="33.3%"><img src="assets/yolo26_mask.jpg" width="100%"></td>
      <td width="33.3%"><img src="assets/yolo26_contour.jpg" width="100%"></td>
    </tr>
  </table>
</div>

This model is a fine-tuned **YOLO26n-seg** developed as part of a Master's Thesis titled:<br>
**Evaluating Rock Position Estimation Pipeline Using 3D Sensors for Excavation Task**

The model has been used to segment rocks by using images captured during the rock-picking task of a real excavator as an input. You can find further information and see the model in action at the [Thesis Project Page](https://tau-alma.github.io/rock-3D-positioning-webpage/)

## Training Process

### Data

The model has been finetuned with the following dataset: 
[rock-segmentation-dataset](https://huggingface.co/datasets/akahukas/rock-segmentation-dataset)

### Hardware & Software

The model has been trained on a RTX 3080 10GB GPU, utilizing the [Ultralytics](https://github.com/ultralytics/ultralytics) framework.

## Acknowledgements

- The thesis work has been completed in the [Autonomous Mobile Machines Group](https://research.tuni.fi/amm/), at Tampere University.
- The thesis work has been funded by the Horizon Europe Project [XSCAVE](https://xscave.eu/) under Grant 101189836.
- Thanks to [Novatron Oy](https://novatron.com/) for providing access to the excavator and the data interface.

## Citation

If you use this model, please cite the original thesis as the primary research source and this repository for the model artifact.

```bibtex
@mastersthesis{hakamaki2026thesis,
  author    = {Saku Hakamäki},
  title     = {Evaluating Rock Position Estimation Pipeline Using 3D Sensors for Excavation Task},
  school    = {Tampere University},
  year      = {2026},
  url       = {https://urn.fi/URN:NBN:fi:tuni-202604274316},
}

@software{hakamaki2026model,
  author       = {Saku Hakamäki},
  title        = {YOLO26n-seg for Rock Segmentation},
  year         = {2026},
  publisher    = {Hugging Face},
  version      = {1.0.0},
  url          = {https://huggingface.co/akahukas/yolo26n-seg-rock-positioning}
}
```