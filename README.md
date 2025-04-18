# Wildcards
A fork of version of a script from https://github.com/AUTOMATIC1111/stable-diffusion-webui-wildcards.git
Allows you to use `__name__` syntax in your prompt to get a random line from a file named `name.txt` in the wildcards directory.
Changes are mostly meant for batch processing and ease of use.

# Added features

* Added a user interface for the image generation tabs.
* Moved global settings to the main interface.
* Added options for repeating image seeds and chosen lines any number of times. The number of images generated will still be controlled by the batch size and batch count.
* Prevent doubles by shuffling lines randomly instead of picking a random line.
* Allows sequential choice instead of random choice by putting a # character between the starting __ and the wildcard.
* Allows setting a starting index and length for more control over which lines to choose. In case of overflow of the line count of any wildards file it will repeat counting from the start of the lines.
* Supports recursive wildcards files.
* Note that the extension will have to be enabled from the user interface for it to do anything.

## Install
To install from webui, go to `Extensions -> Install from URL`, paste `https://github.com/peter-vos/sd-webui-batch-wildcards.git`
into URL field, and press Install. Then restart the webui.

## Install manually
Alternatively, to install by hand:

From your base `stable-diffusion-webui` directory, run the following command to install:
```
git clone https://github.com/peter-vos/sd-webui-batch-wildcards.git
```

Then restart the webui.