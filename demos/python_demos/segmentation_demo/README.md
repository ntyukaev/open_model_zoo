# Image Segmentation Python\* Demo {#omz_demos_python_demos_segmentation_demo_README}

This topic demonstrates how to run the Image Segmentation demo application, which does inference using image
segmentation networks like FCN8.

## How It Works

Upon the start-up the demo application reads command line parameters and loads a network and an image to the
Inference Engine plugin. When inference is done, the application creates an output image.

> **NOTE**: By default, Open Model Zoo demos expect input with BGR channels order. If you trained your model to work with RGB order, you need to manually rearrange the default channels order in the demo application or reconvert your model using the Model Optimizer tool with `--reverse_input_channels` argument specified. For more information about the argument, refer to **When to Reverse Input Channels** section of [Converting a Model Using General Conversion Parameters](https://docs.openvinotoolkit.org/latest/_docs_MO_DG_prepare_model_convert_model_Converting_Model_General.html).

## Running

Running the application with the `-h` option yields the following usage message:

```
python3 segmentation_demo.py -h
```

The command yields the following usage message:

```
usage: segmentation_demo.py [-h] -m MODEL -i INPUT [INPUT ...] [-lab LABELS]
                            [-c COLORS] [-lw LEGEND_WIDTH] [-o OUTPUT_DIR]
                            [-l CPU_EXTENSION] [-d DEVICE]

Options:
  -h, --help            Show this help message and exit.
  -m MODEL, --model MODEL
                        Required. Path to an .xml file with a trained model.
  -i INPUT [INPUT ...], --input INPUT [INPUT ...]
                        Required. Path to a folder with images or path to an
                        image files.
  -lab LABELS, --labels LABELS
                        Optional. Path to a text file containing class labels.
  -c COLORS, --colors COLORS
                        Optional. Path to a text file containing colors for
                        classes.
  -lw LEGEND_WIDTH, --legend_width LEGEND_WIDTH
                        Optional. Width of legend.
  -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        Optional. Path to a folder where output files will be
                        saved.
  -l CPU_EXTENSION, --cpu_extension CPU_EXTENSION
                        Optional. Required for CPU custom layers. Absolute
                        MKLDNN (CPU)-targeted custom layers. Absolute path to
                        a shared library with the kernels implementations.
  -d DEVICE, --device DEVICE
                        Optional. Specify the target device to infer on; CPU,
                        GPU, FPGA, HDDL or MYRIAD is acceptable. Sample will
                        look for a suitable plugin for device specified.
                        Default value is CPU.

```

Running the application with the empty list of options yields the usage message given above and an error message.

To run the demo, you can use public or pre-trained models. You can download the pre-trained models with the OpenVINO [Model Downloader](../../../tools/downloader/README.md). The list of models supported by the demo is in the `models.lst` file in the demo's directory.

> **NOTE**: Before running the demo with a trained model, make sure the model is converted to the Inference Engine format (\*.xml + \*.bin) using the [Model Optimizer tool](https://docs.openvinotoolkit.org/latest/_docs_MO_DG_Deep_Learning_Model_Optimizer_DevGuide.html).

You can use the following command do inference on Intel&reg CPU; Processors on an image using a trained FCN8 network:

```
    python3 segmentation_demo.py -i <path_to_image>/inputImage.bmp -m <path_to_model>/fcn8.xml
```

## Demo Output

The application outputs are a segmented image (`out.bmp`).

## See Also

* [Using Open Model Zoo demos](../../README.md)
* [Model Optimizer](https://docs.openvinotoolkit.org/latest/_docs_MO_DG_Deep_Learning_Model_Optimizer_DevGuide.html)
* [Model Downloader](../../../tools/downloader/README.md)
